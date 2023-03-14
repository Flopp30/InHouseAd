import re
import time
from typing import Optional

import bs4
import requests
from bs4 import BeautifulSoup

from settings import logger, SEARCH_ID

RE_SENTENCES_PATTERN = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s'


def get_sentence_for_link(a_tag: bs4.Tag) -> str:
    sentences = re.split(RE_SENTENCES_PATTERN, a_tag.parent.text)
    a_text = ''
    for sentence in sentences:
        if a_tag.text and a_tag.text in sentence:
            a_text = sentence
    if not a_text:
        a_text = a_tag.text
    return a_text


def get_links_text(url: str) -> dict:
    res = dict()
    if url.startswith('/wiki/'):
        url = 'https://ru.wikipedia.org' + url
    response = requests.get(url)
    logger.info(f'Посещен url адрес {url}')
    time.sleep(0.1)
    content = BeautifulSoup(response.text, 'html.parser').find(id=SEARCH_ID)
    p_tags = content.find_all('p')
    for tag in p_tags:
        for a in tag.find_all('a', href=True):
            a_text = get_sentence_for_link(a)
            res.update({a['href']: a_text})
    return res


def find_path(start_url: str, end_url: str) -> Optional[list]:
    queue = [(start_url, [])]
    visited = set()
    visited.add(start_url)

    while queue:
        url, path = queue.pop(0)
        if 'https://ru.wikipedia.org' + url == end_url:
            return path
        if len(path) >= 3:
            continue
        links_text = get_links_text(url)
        for next_url, next_text in links_text.items():
            if not next_url.startswith('/wiki'):
                continue
            visited.add(next_url)
            next_path = path + [(next_text, 'https://ru.wikipedia.org' + next_url)]

            queue.append((next_url, next_path))

    return None


if __name__ == '__main__':
    start_url = 'https://ru.wikipedia.org/wiki/Xbox_360_S'
    end_url = 'https://ru.wikipedia.org/wiki/Nintendo_3DS'

    if not start_url.startswith('https://ru.wikipedia.org/wiki/') \
            or not end_url.startswith('https://ru.wikipedia.org/wiki/'):
        logger.error("Ошибка! URL должен быть страницей Wikipedia.")
        exit()

    logger.info("Finding path...")
    path = find_path(start_url, end_url)

    if path is None:
        logger.info("No path found")
    else:
        print('Найден путь до страницы:')
        for i, (text, url) in enumerate(path):
            print(f"{i + 1}--------------------------\n"
                  f"{text}\n{url}")
