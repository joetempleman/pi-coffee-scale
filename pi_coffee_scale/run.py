import pyacaia
import logging
import time
from pygatt import GATTToolBackend
from pygatt.exceptions import NotConnectedError

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.debug("Starting")
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
    addr = "68:5E:1C:15:BC:F7"
    logger.info("Getting Adapter")
    adapter = GATTToolBackend('hci0'); 
    logger.info("Getting Adapter")
    adapter.reset(); 
    logger.info("Starting Adapter")
    adapter.start(); 
    logger.info("Connecting to %s", addr)
    tries = 0
    d = None
    while d == None:
        try:
            d = adapter.connect(addr)
        except NotConnectedError:
            if tries < 5:    
                logger.error("Failed to connect, retrying")
                tries += 1
            else:
                raise
    d.subscribe('0000ffe1-0000-1000-8000-00805f9b34fb', handle)