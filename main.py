import asyncio
import re
from typing import Optional
from collections import deque
import aiohttp
from bs4 import BeautifulSoup, Tag

from settings import logger, SEARCH_ID, URL_DOMAIN, HEADERS, MAX_SEARCH_DEPTH

RE_SENTENCES_PATTERN = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s'
TOTAL_PAGE_COUNTER = 0
TOTAL_VISITED_PAGE_COUNTER = 0


async def get_sentence_for_link(a_tag: Tag) -> str:
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


async def get_links_text(text: str) -> dict:
    '''
    Ищет все ссылки и текст вокруг них из блоков <p> внутри контейнера с ID = SEARCH_ID (см. settings.py).
    Выбирает только валидные (url начинает с "/wiki" )
    Возвращает в словаре вида:
    {'a1.href': 'a1_text', 'a2.href': 'a2_text', 'a3.href': 'a3_text', ... }
    :param text: str (url)
    :return: dict
    '''
    res = dict()

    p_tags = BeautifulSoup(text, 'html.parser').find(id=SEARCH_ID).find_all('p')
    for tag in p_tags:
        for a_tag in tag.find_all('a', href=True):
            if not a_tag['href'].startswith('/wiki'):
                continue
            a_text = await get_sentence_for_link(a_tag)
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
    global TOTAL_VISITED_PAGE_COUNTER
    async with session.get(url, headers=HEADERS) as r:
        assert r.status == 200
        TOTAL_VISITED_PAGE_COUNTER += 1
        logger.info(f'Посещена страница {url}')
        r_text = await r.text()
        return r_text, path


async def create_tasks(session: aiohttp.ClientSession, urls: deque):
    '''
    Создает список задач и возвращает его.
    :param session: aiohttp.ClientSession
    :param urls: список url адресов
    :return:
    '''
    tasks = list()
    while urls:
        url, path = urls.popleft()
        if url.startswith('/wiki/'):
            url = URL_DOMAIN + url
        logger.debug(f'Создана задача для страницы {url}')
        task = asyncio.create_task(get_page(session, url, path))
        tasks.append(task)
    return tasks


async def find_path(session, start_url, end_url) -> Optional[list]:
    '''
    Принимает стартовый адрес и искомый, ищет путь между ними
    :param session: aiohttp.ClientSession
    :param start_url: start url
    :param end_url: finish url
    :return: возвращает либо путь, либо ничего
    '''
    global TOTAL_PAGE_COUNTER
    urls = deque()
    urls.append((start_url, []))
    visited = set()
    while urls:

        tasks = await create_tasks(session, urls)
        pages = await asyncio.gather(*tasks, return_exceptions=True)

        for page in pages:
            page, path = page
            links_text = await get_links_text(page)
            for next_url, next_text in links_text.items():
                TOTAL_PAGE_COUNTER += 1
                if next_url not in visited:

                    visited.add(next_url)
                    next_path = path + [(next_text, URL_DOMAIN + next_url)]

                    if URL_DOMAIN + next_url == end_url:
                        return next_path

                    if len(next_path) < MAX_SEARCH_DEPTH:
                        logger.debug(f'{next_url} добавлен  в очередь')
                        urls.append((next_url, next_path))

                    else:
                        logger.debug(f'Пропущен {next_url}. '
                                     f'Глубина поиска превышает заданную в настройках: {MAX_SEARCH_DEPTH}')
                        continue

    return None


async def main():
    start_url, end_url = input('Введите URL старта: '), input('Введите URL, который нужно найти: ')

    if not start_url.startswith(URL_DOMAIN) \
            or not end_url.startswith(URL_DOMAIN):
        print("Ошибка! URL должен быть страницей Wikipedia.")
        exit()

    logger.info("Ищу путь...")
    async with aiohttp.ClientSession() as session:
        path = await find_path(session, start_url, end_url)

    if path is None:
        print("Путь не найден :(")
    else:
        print(f'Найден путь c {start_url} до {end_url}:\n')
        for i, (text, url) in enumerate(path):
            print(f"{i + 1}--------------------------\n"
                  f"{text}\n{url}")
    print(f'\n\nСтраниц обработано: {TOTAL_PAGE_COUNTER}')
    print(f'Страниц посещено: {TOTAL_VISITED_PAGE_COUNTER}')


if __name__ == '__main__':
    asyncio.run(main())
