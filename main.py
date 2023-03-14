import re
import time

import requests
from bs4 import BeautifulSoup

RE_SENTENCES_PATTERN = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s'


def get_links_text(url):
    res = dict()
    if url.startswith('/wiki/'):
        url = 'https://ru.wikipedia.org' + url
    response = requests.get(url)
    time.sleep(0.1)
    print(url)
    content = BeautifulSoup(response.text, 'html.parser').find(id='bodyContent')
    p_tags = content.find_all('p')
    for tag in p_tags:
        sentences = (re.split(RE_SENTENCES_PATTERN, tag.text))
        for a in tag.find_all('a', href=True):
            for idx, sentence in enumerate(sentences):
                if a.has_attr('title') and a['title'] in sentence:
                    a_text = sentence
                else:
                    a_text = a.text
                print({a['href']: a_text})
                res.update({a['href']: a_text})
    return res


def find_path(start_url, end_url):
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
        print("Error: URLs must be Wikipedia pages")
        exit()

    print("Finding path...")
    path = find_path(start_url, end_url)

    if path is None:
        print("No path found")
    else:
        print("Path:")
        for i, (text, url) in enumerate(path):
            print(f"{i + 1}. {text}: {url}")
