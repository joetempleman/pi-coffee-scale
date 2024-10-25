import pyacaia
import logging
import time
import pygatt
import threading

from pygatt import GATTToolBackend
from pygatt.device import BLEDevice
from pygatt.exceptions import NotConnectedError, BLEError
from gpiozero import OutputDevice, Button
from pygatt.backends.gatttool import device
from queue import Queue

WEIGHT_BUFFER = 1

BASE_UUID = "0000%s-0000-1000-8000-00805f9b34fb"
DATA_SERVICE = BASE_UUID % "ffe0"
DATA_CHARACTERISTIC = BASE_UUID % "ffe1"

FELICITA_GRAM_UNIT = "g"
FELICITA_OUNCE_UNIT = "oz"

MIN_BATTERY_LEVEL = 129
MAX_BATTERY_LEVEL = 158

CMD_START_TIMER = 0x52
CMD_STOP_TIMER = 0x53
CMD_RESET_TIMER = 0x43

CMD_TOGGLE_TIMER = 0x42
CMD_TOGGLE_PRECISION = 0x44
CMD_TARE = 0x54
CMD_TOGGLE_UNIT = 0x55

TRIES_BEFORE_RESET = 5

RELAY_PIN = 17
BUTTON_PIN = 4

logging.basicConfig()
device.log.setLevel("DEBUG")

logger = logging.getLogger(__name__)
logger.debug("Starting")


relay = OutputDevice(RELAY_PIN, active_high=True, initial_value=False)
button = Button(BUTTON_PIN)


class CancelledDose(Exception):
    pass


class FailedConnection(Exception):
    pass


def reset(adapter) -> None:
    # logger.info("Resetting Adapter")
    # adapter.reset();
    logger.info("Starting Adapter")
    adapter.start()


def get_adapter() -> GATTToolBackend:
    logger.info("Getting Adapter")
    adapter = GATTToolBackend("hci0")

    reset(adapter)
    return adapter


def connect(adapter: GATTToolBackend, addr: str, max_tries: int = 100) -> BLEDevice:
    logger.info("Connecting to %s", addr)
    tries = 0
    device: BLEDevice = None
    while device == None:
        try:
            device = adapter.connect(addr, timeout=0.5, auto_reconnect=True)
            logger.info("Connected")
        except NotConnectedError:
            tries += 1
            if tries == max_tries:
                raise FailedConnection(
                    "Hit max retries on adapter connect to addr %s", addr
                )

    return device


class CoffeeDoser:

    def __init__(
        self,
        adapter: GATTToolBackend,
        scale_addr: str,
        button: Button,
        relay: OutputDevice,
        target_weight: float = 16,
    ):
        self._lock = threading.Lock()
        self._target_weight = target_weight
        self._adapter = adapter
        self._scale_addr = scale_addr
        # Try to connect on startup to speed things up, but it will connect on button press
        # if the scale isn't currently on, so don't try too many times and continue
        try:
            self._device = connect(self._adapter, self._scale_addr, max_tries=10)
        except FailedConnection:
            self._device = None
            logger.info("Failed to connect, continuing")
        self._button = button

        self._relay = relay

        self._subscribed = False
        self._cancel_dose = False

        self._thread_queue = Queue()
        
    def run(self):
        self._button.when_pressed = self.button_pressed

        while True:
            time.sleep(100)


    def dose_coffee(self):
        with self._lock:
            self._cancel_dose = False
            try:
                self._subscribe()
            except BLEError:
                logger.error("Failed to connect to scale. Canceling Dose")
                return

            logger.info("Weight reading working. Enabling relay")
            self._relay.on()
            while (
                self.weight_reading + WEIGHT_BUFFER < self._target_weight
                and not self._cancel_dose
            ):
                logger.info("Weight is %s, waiting", self.weight_reading)
                time.sleep(0.1)

            self._relay_off_and_unsubscribe()

    def monitor_weight(self, handle, data):
        self._subscribed = True
        try:
            self.weight_reading = int("".join(([str(v - 48) for v in data[3:8]]))) / 10
        except:
            logger.exception("Failed to parse weight, data payload %s", data)
            self._subscribed = False
            self.weight_reading = -1
        # logger.info("Entered monitor_weight, weight = %s", weight_reading)

    def button_pressed(self):
        logger.info("Button pressed, relay status %s", self._relay.value)
        if self._relay.value == 1 or self._lock.locked():
            logger.info("Button pressed again, turning off relay")
            self._cancel_dose = True
            # Setting _cancel_dose should be enough, but in case the other thread has died,
            # turn off the relay and unsubscribe too
            self._relay_off_and_unsubscribe()
        else:
            threading.Thread(target=self.dose_coffee).start()

    def _relay_off_and_unsubscribe(self):
        logger.info("Relay off")
        self._relay.off()
        try:
            logger.info("Unsubscribing")
            self._device.unsubscribe(DATA_CHARACTERISTIC, wait_for_response=False)
            logger.info("Unsubscribed")
        except BLEError:
            logger.warning("Failed to unsubscribe, continuing")

    def _subscribe(self):
        self._subscribed = False
        if not self._device:
            self._device = connect(self._adapter, self._scale_addr)

        logger.info("Subscribing to weight")
        try:
            self._device.subscribe(
                DATA_CHARACTERISTIC,
                callback=self.monitor_weight,
                wait_for_response=False,
            )
        except BLEError:
            raise FailedConnection("Failed to subscribe")
        time.sleep(0.1)
        logger.info("Subscribed=%s", self._subscribed)
        tries = 0
        while not self._subscribed:
            if self._cancel_dose:
                raise CancelledDose("Wait cancelled by button press")

            if tries >= 20:
                raise FailedConnection("Tried %s times and failed to subscribe", tries)

            logger.info("Waiting for weight reading")
            tries += 1
            time.sleep(0.5)


if __name__ == "__main__":
    adapter = get_adapter()

    doser = CoffeeDoser(adapter, "68:5E:1C:15:BC:F7", button, relay)
    doser.run()