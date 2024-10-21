import pyacaia
import logging
import time
import pygatt
import threading

from pygatt import GATTToolBackend
from pygatt.device import BLEDevice
from pygatt.exceptions import NotConnectedError
from gpiozero import OutputDevice, Button
from pygatt.backends.gatttool import device

WEIGHT_BUFFER = 1

BASE_UUID = '0000%s-0000-1000-8000-00805f9b34fb'
DATA_SERVICE = BASE_UUID % 'ffe0'
DATA_CHARACTERISTIC = BASE_UUID % 'ffe1'

FELICITA_GRAM_UNIT = 'g'
FELICITA_OUNCE_UNIT = 'oz'

MIN_BATTERY_LEVEL = 129
MAX_BATTERY_LEVEL = 158

CMD_START_TIMER = 0x52
CMD_STOP_TIMER = 0x53
CMD_RESET_TIMER = 0x43

CMD_TOGGLE_TIMER = 0x42
CMD_TOGGLE_PRECISION = 0x44
CMD_TARE = 0x54
CMD_TOGGLE_UNIT = 0x55

MAX_TRIES = 100
TRIES_BEFORE_RESET = 5

RELAY_PIN = 8
BUTTON_PIN = 7

logging.basicConfig()
device.log.setLevel("DEBUG")

logger = logging.getLogger(__name__)
logger.debug("Starting")
relay = OutputDevice(RELAY_PIN, active_high=False, initial_value=False)
button = Button(BUTTON_PIN)
subscribed = False
cancel_wait = False
 
def reset(adapter) -> None:
    # logger.info("Resetting Adapter")
    # adapter.reset(); 
    logger.info("Starting Adapter")
    adapter.start(); 

def get_adapter() -> GATTToolBackend:
    logger.info("Getting Adapter")
    adapter = GATTToolBackend('hci0'); 

    reset(adapter)
    return adapter

def connect(adapter: GATTToolBackend, addr="68:5E:1C:15:BC:F7") -> BLEDevice:

    logger.info("Connecting to %s", addr)
    tries = 0
    device : BLEDevice = None
    while device == None:
        try:
            device = adapter.connect(addr, timeout=0.5, auto_reconnect=True)
            logger.info("Connected")
        except NotConnectedError:
            tries += 1
            if tries == MAX_TRIES:
                raise            
            
            # # Every X tries, reset adapter
            # if tries % TRIES_BEFORE_RESET == 0:
            #     logger.error("Failed to connect, resetting adapter and retrying")
            #     reset()
    return device

def dose_coffee(target_weight, device):
    global cancel_wait
    global relay
    global weight_reading
    global subscribed
    cancel_wait = False

    subscribed = False
    callback = lambda handle, data: monitor_weight(handle, data, device, target_weight)
    logger.info("Subscribing to weight")
    device.subscribe(DATA_CHARACTERISTIC, callback=callback, wait_for_response=False)
    time.sleep(0.1)
    while not subscribed and not cancel_wait:
        logger.info("Waiting for weight reading")
        time.sleep(0.5)

    if cancel_wait:        
        return
    
    logger.info("Weight reading working. Enabling relay")
    relay.on()
    while weight_reading + WEIGHT_BUFFER < target_weight and not cancel_wait:
        logger.info("Weight is %s, waiting", weight_reading)
        time.sleep(0.1)
    
    logger.info("At weight, closing relay")
    relay.off()
    logger.info("Ubsubscribing")
    device.unsubscribe(DATA_CHARACTERISTIC, wait_for_response=False)
    logger.info("Unsubscribed!")


def monitor_weight(handle, data, device: BLEDevice, target_weight):
    global subscribed
    global weight_reading
    subscribed = True
    weight_reading = int(''.join(([str(v - 48) for v in data[3:8]]))) / 10
    # logger.info("Entered monitor_weight, weight = %s", weight_reading)


def button_pressed(adapter: GATTToolBackend, device: BLEDevice, target_weight: int):
    global relay
    global weight_reading
    global cancel_wait
    global subscribed
    logger.info("Button pressed, relay status %s", relay.value)
    if relay.value == 1:
        logger.info("Turning off relay")
        relay.off()
        cancel_wait = True
        device.unsubscribe(DATA_CHARACTERISTIC, wait_for_response=False)
    else:
        threading.Thread(target=dose_coffee, args=(target_weight, device)).start()

if __name__ == '__main__':
    # addresses = pyacaia.find_acaia_devices(backend='pygatt')

    # if addresses:
    #     logger.debug("Mac addr %s", addresses)        
    # else:
    #     logger.error("Failed to find devices")
    #     sys.exit(1)

    # addr = addresses[0]
    adapter = get_adapter()
    d = connect(adapter)
    button.when_pressed = lambda: button_pressed(adapter, d, 15)
    
    while True:
        time.sleep(100)
        # time.sleep(1)
        # logger.info('Pressing button')
        # button.pin.drive_low()
        # time.sleep(0.1)
        # button.pin.drive_high()
        # time.sleep(2)
