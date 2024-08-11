import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - " "%(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

log_file = "logs/EONA.log"
handler = RotatingFileHandler(log_file, maxBytes=1e6, backupCount=5)
formatter = logging.Formatter(
    "%(asctime)s:%(levelname)s:%(name)s: %(message)s")
handler.setFormatter(formatter)


logger = logging.getLogger("EONA")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
