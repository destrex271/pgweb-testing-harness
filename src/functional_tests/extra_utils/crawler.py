from collections import deque
import requests
from bs4 import BeautifulSoup as BSoup

class CustomCrawler:
    def __init__(self, base_url):
        self.base_url = base_url
        self.external_links = set()
        self.internal_links = set()
        self.parent_url_dict = {}

    def _extract_links(self, url):
        page = requests.get(url).content
        content = BSoup(page, "html.parser")
        links = content.find_all('a')
        for lk in links:
            href = lk.get('href')
            if href and href != '':
                if href.startswith('/'):
                    href = self.base_url + href
                if href.endswith('.html') and href.startswith('ftp') and not (href.startswith('http') or
                                                                              href.startswith('/')) or href.__contains__('.html#'):
                    continue
                if href.startswith('http') and not (href.startswith('mailto') or href.startswith('#')):
                    if href.__contains__("localhost") or href.startswith('/'):
                        self.internal_links.add(href)
                    else:
                        self.external_links.add(href)
                    self.parent_url_dict[href] = [url]
                    self.parent_url_dict[href].append(lk.get_text())

    def crawl(self, max_internal_depth=2, max_external_depth=1):
        url_queue = deque([(self.base_url + "/", 0)])  # (url, depth)
        all_urls = [url_queue[0][0]] # list of all urls visited
        while len(url_queue) > 0:
            cur_url, depth = url_queue.popleft()
            
            if cur_url in self.external_links and depth >= max_external_depth:
                break
            if cur_url in self.internal_links and depth >= max_internal_depth:
                break
            
            self._extract_links(cur_url)

            for link in self.internal_links:
                if link not in all_urls:
                    url_queue.append((link, depth + 1))
                    all_urls.append(link)