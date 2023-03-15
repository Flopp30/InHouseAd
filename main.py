import asyncio
import re
from typing import Optional

import aiohttp
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


def get_links_text(text: str) -> dict:
    '''
    Ищет все ссылки из блоков <p> внутри контейнера с ID = SEARCH_ID (см. settings.py)
    Возвращает в словаре вида:
    {'a1.href': 'a1_text', 'a2.href': 'a2_text', 'a3.href': 'a3_text', ... }
    :param text: str (url)
    :return: dict
    '''
    res = dict()

    p_tags = BeautifulSoup(text, 'html.parser').find(id=SEARCH_ID).find_all('p')

    for tag in p_tags:
        for a_tag in tag.find_all('a', href=True):
            a_text = get_sentence_for_link(a_tag)
            res.update({a_tag['href']: a_text})

    return res


async def get_page(session: aiohttp.ClientSession, url: str, path: Optional[list]) -> tuple:
    '''
    Отправляет запрос по указанному адресу, возвращает html код страницы
    :param session: aiohttp.ClientSession
    :param url: url address
    :param path: использую для общей логики, чтобы данные по пути запроса были привязаны к странице
    :return: (response.text, path)
    '''
    async with session.get(url) as r:
        logger.info(f'Посещена страница {url}')
        r_text = await r.text()
        return r_text, path


# TODO вопросы по работе этой функции
async def find_path(session, start_url, end_url) -> Optional[list]:
    '''
    Принимает стартовый адрес и искомый, ищет путь между ними
    :param session: aiohttp.ClientSession
    :param start_url: start url
    :param end_url: finish url
    :return: возвращает либо путь, либо ничего
    '''
    tasks = list()
    urls = [(start_url, [])]
    visited = set()
    while urls:

        while urls:  # <-- Цикл для заполнения задач
            url, path = urls.pop(0)
            if url.startswith('/wiki/'):
                url = URL_DOMAIN + url
            task = asyncio.create_task(get_page(session, url, path))
            tasks.append(task)

        pages = await asyncio.gather(*tasks)

        if pages:
            for page in pages:
                page, path = page
                links_text = get_links_text(page)
                for next_url, next_text in links_text.items():
                    if not next_url.startswith('/wiki'):
                        continue
                    if next_url not in visited:
                        visited.add(next_url)
                        next_path = path + [(next_text, URL_DOMAIN + next_url)]
                        if len(next_path) >= 3:
                            continue
                        urls.append((next_url, next_path))
                        if URL_DOMAIN + next_url == end_url:
                            return next_path
    return None  # <-- Никогда не возвращает None здесь при валидных данных:(


async def main():
    start_url, end_url = 'https://ru.wikipedia.org/wiki/Xbox_360_S', 'https://ru.wikipedia.org/wiki/'

    if not start_url.startswith(URL_DOMAIN) \
            or not end_url.startswith(URL_DOMAIN):
        logger.error("Ошибка! URL должен быть страницей Wikipedia.")
        exit()

    logger.info("Ищу путь...")
    async with aiohttp.ClientSession() as session:
        path = await find_path(session, start_url, end_url)

    if path is None:
        logger.info("Путь не найден :(")
    else:
        print(f'Найден путь c {start_url} до {end_url}:')
        for i, (text, url) in enumerate(path):
            print(f"{i + 1}--------------------------\n"
                  f"{text}\n{url}")


if __name__ == '__main__':
    asyncio.run(main())
