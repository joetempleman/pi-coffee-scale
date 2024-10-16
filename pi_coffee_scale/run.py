import pyacaia
import logging
import time
from pygatt import GATTToolBackend
from pygatt.exceptions import NotConnectedError

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

if __name__ == '__main__':
    # addresses = pyacaia.find_acaia_devices(backend='pygatt')

    # if addresses:
    #     logger.debug("Mac addr %s", addresses)        
    # else:
    #     logger.error("Failed to find devices")
    #     sys.exit(1)

    # addr = addresses[0]
    def handle(handle, value): 
        print(int(''.join(([str(v - 48) for v in value[3:8]]))) / 10)
    d = connect()
    logger.info("Subscribing to handle")
    d.subscribe('0000ffe1-0000-1000-8000-00805f9b34fb', callback=handle, wait_for_response=False)
    logger.info("Subscribed")        
    while True:
        time.sleep(100)
