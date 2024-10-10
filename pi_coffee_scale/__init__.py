
import pyacaia
import logging
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    addresses = pyacaia.find_acaia_devices(backend='pygatt')
    if addresses:
        logger.error("Failed to find devices")
    else:
        logger.debug("Mac addr %s", addresses[0])

    time.sleep(1)
    scale=pyacaia.AcaiaScale()

    scale.connect(addresses[0])

    for i in range(10):
        print(scale.weight)
        time.sleep(0.5)

    scale.disconnect()


