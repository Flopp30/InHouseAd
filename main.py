import re
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup, Tag

from settings import logger, SEARCH_ID, URL_DOMAIN, HEADERS

RE_SENTENCES_PATTERN = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s'


def get_sentence_for_link(a_tag: Tag) -> str:
    '''
    Возвращает предложение в теге-родители, где упоминается данная ссылка
    :param a_tag: <a> tag
    :return: text
    '''
    sentences = re.split(RE_SENTENCES_PATTERN, a_tag.parent.text)
    a_text = ''
    for sentence in sentences:
        if a_tag.text and a_tag.text in sentence:
            a_text = sentence
    if not a_text:
        a_text = a_tag.text
    return a_text


def get_links_text(url: str) -> dict:
    '''
    Ищет все ссылки из блоков <p> внутри контейнера с ID = SEARCH_ID (см. settings.py)
    Возвращает в словаре вида:
    {'a1.href': 'a1_text', 'a2.href': 'a2_text', 'a3.href': 'a3_text', ... }
    :param url: str (url)
    :return: dict
    '''
    res = dict()

    try:
        response = requests.get(url, headers=HEADERS)
    except Exception as e:
        logger.error(f'Во время выполнения запроса к {URL_DOMAIN + url} возникла ошибка {e}')
        exit()

    logger.info(f'Посещен url адрес {url}')
    time.sleep(0.1)

    p_tags = BeautifulSoup(response.text, 'html.parser').find(id=SEARCH_ID).find_all('p')

    for tag in p_tags:
        for a_tag in tag.find_all('a', href=True):
            a_text = get_sentence_for_link(a_tag)
            res.update({a_tag['href']: a_text})

    return res


def find_path(start_url: str, end_url: str) -> Optional[list]:
    '''
    Принимает точку старта и искомый url, ищет оптимальный путь поиском в ширину.
    Возвращает структуру [(text info, URL address), (text info, URL address) ..]
    :param start_url: URL стартовой страницы
    :param end_url: Искомый URL
    :return: list(tuple(text, url), tuple(text, url)...)
    '''
    queue = [(start_url, [])]
    visited = set()
    visited.add(start_url)

    while queue:
        url, path = queue.pop(0)

        if url.startswith('/wiki/'):
            url = URL_DOMAIN + url
        if url == end_url:
            return path
        if len(path) >= 3:
            continue

        links_text = get_links_text(url)

        for next_url, next_text in links_text.items():
            if not next_url.startswith('/wiki'):
                continue
            visited.add(next_url)
            next_path = path + [(next_text, URL_DOMAIN + next_url)]

            queue.append((next_url, next_path))

    return None


def main():
    start_url, end_url = input('Введите стартовый URL: '), input('Введите URL, путь до которого требуется найти: ')

    if not start_url.startswith(URL_DOMAIN) \
            or not end_url.startswith(URL_DOMAIN):
        logger.error("Ошибка! URL должен быть страницей Wikipedia.")
        exit()

    logger.info("Ищу путь...")
    path = find_path(start_url, end_url)

    if path is None:
        logger.info("Путь не найден :(")
    else:
        print('Найден путь до страницы:')
        for i, (text, url) in enumerate(path):
            print(f"{i + 1}--------------------------\n"
                  f"{text}\n{url}")


if __name__ == '__main__':
    main()
