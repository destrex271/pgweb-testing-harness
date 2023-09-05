import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver

from django.test.testcases import call_command, connections
from django.contrib.staticfiles.testing import LiveServerTestCase

from .extra_utils.util_functions import varnish_cache
from .utils.download_docs import setup_documentation
import concurrent.futures
from copy import deepcopy
import time

from bs4 import BeautifulSoup as Bsoup

# Core Models
from .core.models import Version


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


def check_page(root_url, class_obj, version):
    urls = [root_url]
    # print("Root url -> ", urls[0])
    base = root_url[:root_url.rfind("/")]

    broken_links = []

    while len(urls) > 0:

        url = urls[0]
        # print("Queued: ", url)
        page = requests.get(url)
        soup = Bsoup(page.text, "html.parser")
        content = soup.find_all(id='docContent')
        content = content[0].get_text()
        class_obj.assertGreater(len(content), 100)
        # print("Content Length at " + url + " : " + str(len(content)))
        nav_btns = soup.find_all("a")
        next_url = None
        # for lnk in nav_btns:
        #     lk = lnk.get('href')
        #     if lk:
        #         if not lk.startswith('http'):
        #             lk = base + '/' + lk
        #         stat = requests.get(lk).status_code
        #         if stat != 200:
        #             broken_links.append([lk, url])
        for btn in nav_btns:
            if btn.get_text() == 'Next':
                next_url = base + '/' + btn.get('href')
        if next_url:
            # print(next_url)
            urls.append(next_url)
        del urls[0]

    # if len(broken_links) > 0:
        # class_obj.assertFalse(True, 'Broken Links present in documentation. Kindly go through the broken links log file')

    return 0


class DocumentationRenderTests(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Prefix vars
        cls.prefix = "id_"

        # Webdriver Configuration
        options = webdriver.FirefoxOptions()
        options.headless = True
        serv = Service(executable_path=GeckoDriverManager().install())
        cls.selenium = webdriver.Firefox(
            service=serv, options=options)
        varnish_cache()
        cls.vers_list = []
        download_map = setup_documentation()
        cls.dld = download_map
        # print("LOADED: ", download_map)
        for version, _ in download_map.items():
            cls.vers_list.append(version)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.selenium.quit()
        super().tearDownClass()

    def test_rendered_documentation(self):

        self.assertFalse(self.dld is None, msg='Unable to load documentation')
        self.selenium.get(self.live_server_url + "/docs/")
        links = self.selenium.find_element(
            By.ID, 'pgContentWrap').find_elements(By.TAG_NAME, 'a')
        link_list = []

        for link in links:
            if link.text.isnumeric():
                link_list.append(link.text)

        max_docs = len(link_list)

        lvers_list = []
        for a in self.vers_list:
            ver = a
            ver = ver.replace('beta', '.')
            ver = ver.split('.')
            lvers_list.append(ver[0])

        # Check if all versions are rendered as links
        self.assertEqual(lvers_list, link_list)

        self.selenium.get(self.live_server_url + "/docs/")
        links = self.selenium.find_element(
            By.ID, 'pgContentWrap').find_elements(By.TAG_NAME, 'a')

        link_hrefs = {}
        i = 0
        for link in links:
            if link.text.isnumeric():
                if i >= max_docs:
                    break
                link_hrefs[link.text] = link.get_attribute("href")
                i += 1

        executor = concurrent.futures.ThreadPoolExecutor(max_docs)
        tasks = []
        for version, url in link_hrefs.items():
            tasks.append(executor.submit(check_page, url, self, version))
        # concurrent.futures.wait(tasks)
        # print(len(tasks))
        ftasks = concurrent.futures.as_completed(tasks)
        for ftask in ftasks:
            try:
                data = ftask.result()
            except Exception as ex:
                # print(ex)
                self.assertTrue(False, msg='Error in rendering documentation')
