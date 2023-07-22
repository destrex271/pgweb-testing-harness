from django.contrib.staticfiles.testing import LiveServerTestCase
from django.test.testcases import call_command, connection, connections
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver
import requests
from selenium.webdriver.firefox.service import Service
from django.db import connection
from .extra_utils.util_functions import varnish_cache
from bs4 import BeautifulSoup as BSoup

from .utils.download_docs import setup_documentation
from .utils.clean_tables import remove_versions
# Custom utilities
from pgweb.utils.report_generation import write_to_report
from requests.packages.urllib3.util.retry import Retry

# Fix for CASCADE TRUNCATE FK error


def _fixture_teardown(self):
    # Allow TRUNCATE ... CASCADE and don't emit the post_migrate signal
    # when flushing only a subset of the apps
    for db_name in self._databases_names(include_mirrors=False):
        # Flush the database
        inhibit_post_migrate = (
            self.available_apps is not None
            or (  # Inhibit the post_migrate signal when using serialized
                # rollback to avoid trying to recreate the serialized data.
                self.serialized_rollback
                and hasattr(connections[db_name], "_test_serialized_contents")
            )
        )
        call_command(
            "flush",
            verbosity=0,
            interactive=False,
            database=db_name,
            reset_sequences=False,
            # In the real TransactionTestCase this is conditionally set to False.
            allow_cascade=True,
            inhibit_post_migrate=inhibit_post_migrate,
        )


LiveServerTestCase._fixture_teardown = _fixture_teardown
# ---------------------------

external_links = []
internal_links = []
broken_internal_links = {}
broken_external_links = {}

parent_url_dict = {}

# Generate a list of all the urls of the website


def segregate_links(addr):

    urls = [addr + "/"]
    all_urls = [addr + "/"]

    while len(urls) > 0:
        print("Checking -> ", urls[0])
        page = requests.get(urls[0]).content
        content = BSoup(page, "html.parser")
        links = content.find_all('a')
        # print(links)
        for lk in links:
            url = lk.get('href')
            if url and url != '':
                if url.startswith('/'):
                    url = addr + url
                if url.endswith('.html') and url.startswith('ftp') and not (url.startswith('http') or
                                                                            url.startswith('/')) or url.__contains__('.html#'):
                    continue
                if url not in all_urls and url.startswith('http') and not (url.startswith('mailto') or url.startswith('#')):
                    if url.__contains__("localhost") or url.startswith('/'):
                        internal_links.append(url)
                        urls.append(url)
                    else:
                        external_links.append(url)

                    parent_url_dict[url] = urls[0]
                    all_urls.append(url)
        # print()
        del urls[0]

    # print("Internal urls ", len(internal_links))
    # print("External urls ", len(external_links))


class RecusrsiveLinkCrawlTests(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.FirefoxOptions()
        options.headless = True
        serv = Service(executable_path=GeckoDriverManager().install())
        cls.selenium = webdriver.Firefox(
            service=serv, options=options)

        # Loading initial dummy database
        # call_command('loaddata', 'pgweb/core/fixtures/data.json')
        call_command('loaddata', 'pgweb/docs/fixtures/data.json')
        call_command('loaddata', 'pgweb/lists/fixtures/data.json')
        call_command('loaddata', 'pgweb/sponsors/fixtures/data.json')
        call_command('loaddata', 'pgweb/contributors/fixtures/data.json')
        call_command('loaddata', 'pgweb/featurematrix/fixtures/data.json')

        # Segregation of internal and external links
        # print("Segregating")
        segregate_links(cls.live_server_url)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_external_links(self):
        # print(external_links)
        session = requests.Session()
        session.headers.update({"User-Agent": "Defined"})
        for lnk in external_links:
            res = None
            try:
                res = session.get(lnk)
            except requests.exceptions.ConnectionError:
                continue
            if res is not None:
                stat = res.status_code
                if not stat == 200:
                    broken_external_links[lnk] = [stat, parent_url_dict[lnk]]
            else:
                broken_external_links[lnk] = "Not reachable"

        if len(broken_external_links) != 0:
            print("Writing to file!!")
            write_to_report(broken_external_links,
                            "Broken External Links", par=True)
        self.assertTrue(len(broken_external_links) ==
                        0, msg="Please check the broken_urls.log file")

    def test_internal_links(self):
        for lnk in internal_links:
            res = requests.get(lnk)
            if res is not None:
                stat = res.status_code
                if not stat == 200:
                    broken_internal_links[lnk] = [stat, parent_url_dict[lnk]]
            else:
                broken_internal_links[lnk] = "Not reachable"

        # Checking if the internal URL is working on the deployed version
        to_rem = []
        for lk in broken_internal_links.keys():
            lvk = str(lk).replace(
                f'{self.live_server_url}', "https://www.postgresql.org")
            if requests.get(lvk).status_code == 200:
                to_rem.append(lk)

        # Removing false errors
        for working_link in to_rem:
            broken_internal_links.pop(working_link)

        if len(broken_internal_links) != 0:
            write_to_report(broken_internal_links,
                            "Broken Internal Links", par=False)
        self.assertTrue(len(broken_internal_links) ==
                        0, msg="Please check the broken_urls.log file")
