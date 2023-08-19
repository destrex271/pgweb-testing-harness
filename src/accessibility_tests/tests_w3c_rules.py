from django.contrib.staticfiles.testing import LiveServerTestCase
from django.forms.fields import math, re
from django.test.testcases import call_command, connections
import requests
import json
import concurrent.futures
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver

from .extra_utils.util_functions import varnish_cache
from bs4 import BeautifulSoup

import os


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

site_map = []


def translate_sitemap(base):
    global site_map
    # if base.endswith('/'):
    #     base = base[0:-1]
    # base += "/sitemap.xml"
    # print(base)
    base_adr = base
    base = "https://www.postgresql.org/sitemap.xml"
    res = requests.get(base)
    print(res)
    if res.status_code == 200:
        root = ET.fromstring(res.content)
        urls = []
        for loc in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
            urls.append(str(loc.text).replace("www.postgresql.org", base_adr))
        site_map = urls


# def prepare_site_map(base):
#     if base.endswith('/'):
#         base = base[0:-1]
#     urls = [base]
#     pattern = r'docs/\d+'
#     site_map.append(base)
#     while len(urls) > 0:
#         url = urls[0]
#         if re.search(pattern, url):
#             continue
#         res = None
#         try:
#             res = requests.get(url)
#         except requests.exceptions.ConnectionError:
#             continue
#         if res:
#             soup = BeautifulSoup(res.content, "html.parser")
#             for lnk in soup.find_all('a'):
#                 lk = lnk.get('href')
#                 if lk:
#                     if re.search(pattern, lk):
#                         continue
#                     if not lk.startswith('http') and (lk.startswith('/') or lk.startswith("#")):
#                         lk = base + lk
#                     # print(lk, site_map)
#                     if lk not in site_map and lk.__contains__('localhost'):
#                         # print("Adding")
#                         site_map.append(lk)
#                         urls.append(lk)
#         del urls[0]
#

def run_lighthouse(url_lst):
    print("Testing: ", {url_lst})
    main_data = {}
    for url in url_lst:
            os.system(f'lighthouse --chrome-flags="--no-sandbox --headless --disable-gpu" --only-categories accessibility --disable-storage-reset="true" {url}')
            with open('./report.json', 'r') as f:
                js_data = json.loads(f.read())
                print(js_data)
                for x in js_data.keys():
                    print(x)
                # print(js_data['categories'])
                main_data[url] = js_data['categories']
    return main_data


class AccessibilityTests(LiveServerTestCase):

    # fixtures = ['pgweb/fixtures/users.json', 'pgweb/fixtures/org_types.json',
    #             'pgweb/fixtures/organisations.json', 'pgweb/core/fixtures/data.json', 'pgweb/fixtures/lang_fixtures.json', 'pgweb/fixtures/approved_events.json']

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

    @classmethod
    def tearDownClass(cls) -> None:
        cls.selenium.quit()
        super().tearDownClass()

    def tests_accessibility_issues(self):
        os.system(f"unlighthouse-ci --site {self.live_server_url} --debug --build-static --output-path .")
        # # prepare_site_map(self.live_server_url)
        # translate_sitemap(self.live_server_url)
        # # self.assertLess(len(site_map), 0)
        # threads = ThreadPoolExecutor(len(site_map)//10)
        # print(len(site_map))
        # self.assertTrue(len(site_map) > 0, msg="Unable to Translate Sitemap; Please check the website sitemap")
        # i = 1
        # lst = []
        # tasks = []
        # # main_data = run_lighthouse(site_map)
        # for url in site_map:
        #     print(i)
        #     if i % 10 != 0:
        #         lst.append(url)
        #     else:
        #         tasks.append(threads.submit(run_lighthouse, lst))
        #         lst = []
        #         print(lst)
        #         lst.append(url)
        #     i += 1
        # ftasks = concurrent.futures.as_completed(tasks)
        # for ftask in ftasks:
        #     print(ftask)
        #     try:
        #         data = ftask.result()
        #         # print(data)
        #         # main_data.update(data)
        #     except Exception as ex:
        #         print(ex)
        #         self.assertTrue(False, msg='Error in rendering documentation')
        #     else:
        #         print(data)
        # print(os.system('ls ../'))
        # print(os.system('ls'))
        # print(main_data)
        # if main_data:
        #     with open('output.json', 'w') as f:
        #         json.dump(main_data, f)
