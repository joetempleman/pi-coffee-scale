import pyacaia
import logging
import time
from pygatt import GATTToolBackend
from pygatt.exceptions import NotConnectedError
from gpiozero import OutputDevice, Button


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

RELAY_PIN = 2
BUTTON_PIN = 3

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.debug("Starting")

relay = OutputDevice(RELAY_PIN, active_high=False, initial_value=False)
button = Button(BUTTON_PIN)

def reset(adapter):
    logger.info("Resetting Adapter")
    adapter.reset(); 
    logger.info("Starting Adapter")
    adapter.start(); 

def get_adapter():
    logger.info("Getting Adapter")
    adapter = GATTToolBackend('hci0'); 

    reset(adapter)
    return adapter

def connect(adapter, addr="68:5E:1C:15:BC:F7"):

    logger.info("Connecting to %s", addr)
    tries = 0
    d = None
    while d == None:
        try:
            d = adapter.connect(addr)
            logger.info("Connected")
        except NotConnectedError:
            tries += 1
            if tries == MAX_TRIES:
                raise            
            
            # Every X tries, reset adapter
            if tries % TRIES_BEFORE_RESET == 0:
                logger.error("Failed to connect, resetting adapter and retrying")
                reset()
    return d

def monitor_weight(target_weight, value):
    global relay
    global weight_reading
    weight_reading = int(''.join(([str(v - 48) for v in value[3:8]]))) / 10
    logger.info("Entered monitor_weight, weight = %s", weight_reading)
    if weight_reading + WEIGHT_BUFFER > target_weight:
        logger.info("At weight, closing relay")
        relay.off()

def button_pressed(adapter, device, target_weight):
    global relay
    global weight_reading
    if relay.value:
        relay.off()

    if relay.value == False:
        logger.info("Subscribing to weight")
        weight_reading = 0
        callback = lambda: monitor_weight(target_weight)
        device.subscribe(DATA_CHARACTERISTIC, callback=callback, wait_for_response=False)
        while not weight_reading:
            logger.info("Waiting for weight reading")
            time.sleep(0.1)
        logger.info("Weight reading working. Enabling relay")
        relay.on()

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
    logger.info("Subscribing to handle")

    button.when_pressed = lambda: button_pressed(adapter, d, 15)
    
    while True:
        time.sleep(1)
        button.close()
        time.sleep(100)
