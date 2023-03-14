import sys

from loguru import logger

# Request params
HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
}

# Parser params
SEARCH_ID = 'bodyContent'  # Блок, в котором ищем <p> и <a>

# Logger
logger.add(sys.stderr, format="{time} {level} {message}", filter="my_module", level="INFO")
logger.add("file_1.log", rotation="500 MB")
