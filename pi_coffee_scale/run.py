import pyacaia
import logging
import time
from pygatt import GATTToolBackend 

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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

    from pygatt import GATTToolBackend
    adapter = GATTToolBackend('hci0'); adapter.reset(); adapter.start(); d = adapter.connect("68:5E:1C:15:BC:F7")
    d.subscribe('0000ffe1-0000-1000-8000-00805f9b34fb', handle)