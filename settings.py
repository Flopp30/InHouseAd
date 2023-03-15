import sys

from loguru import logger

# Request params
HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
}

# Parser params
SEARCH_ID = 'bodyContent'  # Блок, в котором ищем ссылки
MAX_SEARCH_DEPTH = 3  # Глубина поиска (количество кликов для перехода)
URL_DOMAIN = 'https://ru.wikipedia.org'

# Logger
logger.add(sys.stdout, format="{time} {level} {message}", filter="my_module",
           level="INFO", backtrace=True, diagnose=True
           )
logger.add("file.log", enqueue=True)
