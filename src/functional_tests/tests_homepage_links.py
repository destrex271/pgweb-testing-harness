from collections import deque
import re
from django.contrib.staticfiles.testing import LiveServerTestCase
from django.test.testcases import call_command, connection, connections
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver
import requests
from selenium.webdriver.firefox.service import Service
from django.db import connection
from .extra_utils.util_functions import varnish_cache, fixture_teardown
from bs4 import BeautifulSoup as BSoup
from .extra_utils.crawler import CustomCrawler
from .utils.download_docs import setup_documentation
from .utils.clean_tables import remove_versions
# Custom utilities
from pgweb.utils.report_generation import write_to_report
from requests.packages.urllib3.util.retry import Retry
from .extra_utils.crawler import CustomCrawler
# Fix for CASCADE TRUNCATE FK error

LiveServerTestCase._fixture_teardown = fixture_teardown
# ---------------------------

class CustomLinkTester(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.FirefoxOptions()
        options.headless = True
        serv = Service(executable_path=GeckoDriverManager().install())
        cls.selenium = webdriver.Firefox(service=serv, options=options)

        # Loading initial dummy database
        varnish_cache()
        call_command('loaddata', 'pgweb/docs/fixtures/data.json')
        call_command('loaddata', 'pgweb/lists/fixtures/data.json')
        call_command('loaddata', 'pgweb/sponsors/fixtures/data.json')
        call_command('loaddata', 'pgweb/contributors/fixtures/data.json')
        call_command('loaddata', 'pgweb/featurematrix/fixtures/data.json')

        # Crawl links
        cls.crawler = CustomCrawler(cls.live_server_url)
        cls.crawler.crawl()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_internal_links(self):
        broken_internal_links = {}
        for link in self.crawler.internal_links:
            pattern = re.compile('docs/(current|[0-9])')
            pat2 = re.compile('docs/books/pg.*')
            if pattern.search(link) or pat2.search(link):
                continue
            res = requests.get(link)
            if res is not None:
                stat = res.status_code
                if not stat == 200:
                    broken_internal_links[link] = [
                        stat, self.crawler.parent_url_dict[link][0], self.crawler.parent_url_dict[link][1]]
            else:
                broken_internal_links[link] = "Not reachable"

        # Checking if the internal URL is working on the deployed version
        broken_links=list(broken_internal_links.keys()).copy()
        for lk in broken_links:
            lvk = str(lk).replace(
                f'{self.live_server_url}', "https://www.postgresql.org")

            if requests.get(lvk).status_code == 200:
                broken_internal_links.pop(lk)

        self.assertFalse(broken_internal_links, msg="Please check the broken_urls log for a detailed description.")

    def test_external_links(self):
        broken_external_links = {}
        session = requests.Session()
        session.headers.update({"User-Agent": "Defined"})
        for link in self.crawler.external_links:
            res = None
            try:
                res = session.get(link)
            except requests.exceptions.ConnectionError:
                continue
            pattern = re.compile('docs/(current|[0-9])')
            pat2 = re.compile('docs/books/pg.*')
            if pattern.search(link) or pat2.search(link):
                continue
            if res is not None:
                stat = res.status_code
                if not stat == 200:
                    if stat == 400 and link.__contains__('twitter'): # Twitter API 400  false alarm handling
                        pass
                    else:
                        broken_external_links[link] = [stat, self.crawler.parent_url_dict[link][0].replace(
                            self.live_server_url, 'https://www.postgresql.org'), self.crawler.parent_url_dict[link][1]]
            else:
                broken_external_links[link] = "Not reachable"

        if broken_external_links:
            write_to_report(broken_external_links, "Broken External Links", par=True)
        self.assertFalse(broken_external_links, msg="Please check the broken_urls.log file.")