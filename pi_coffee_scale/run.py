import pyacaia
import logging
import time
from pygatt import GATTToolBackend
from pygatt.exceptions import NotConnectedError

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

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.debug("Starting")


def reset(adapter):
    logger.info("Resetting Adapter")
    adapter.reset(); 
    logger.info("Starting Adapter")
    adapter.start(); 

def connect(addr="68:5E:1C:15:BC:F7"):
    logger.info("Getting Adapter")
    adapter = GATTToolBackend('hci0'); 

    reset(adapter)

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

read = 0

def get_weight(handle, value): 
    logger.info("Entered get_weight")
    weight = int(''.join(([str(v - 48) for v in value[3:8]]))) / 10
    local_read = read
    time.sleep(1)
    logger.info("read == %s, local_read == %s", read, local_read)
    read = local_read + 1

if __name__ == '__main__':
    # addresses = pyacaia.find_acaia_devices(backend='pygatt')

    # if addresses:
    #     logger.debug("Mac addr %s", addresses)        
    # else:
    #     logger.error("Failed to find devices")
    #     sys.exit(1)

    # addr = addresses[0]
    d = connect()
    logger.info("Subscribing to handle")
    d.subscribe(DATA_CHARACTERISTIC, callback=get_weight, wait_for_response=False)
    logger.info("Subscribed")        
    while True:
        time.sleep(100)
