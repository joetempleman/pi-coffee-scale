import pyacaia
import logging
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if __name__ == '__main__':
    addresses = pyacaia.find_acaia_devices(backend='pygatt')

    if addresses:
        logger.debug("Mac addr %s", addresses)        
    else:
        logger.error("Failed to find devices")
        sys.exit(1)

    time.sleep(1)
    scale=pyacaia.AcaiaScale(addresses[0], backend='pygatt')

    scale.connect()

    for i in range(10):
        print(scale.weight)
        time.sleep(0.5)

    scale.disconnect()


