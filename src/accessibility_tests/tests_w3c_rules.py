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
        self.selenium.get(self.live_server_url)
        print(self.selenium.find_elements(By.TAG_NAME, 'h1'))
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
