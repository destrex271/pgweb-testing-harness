from django.contrib.staticfiles.testing import LiveServerTestCase
from django.test.testcases import call_command, connections
import requests
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


def prepare_site_map(base):
    if base.endswith('/'):
        base = base[0:-1]
    urls = [base]
    site_map.append(base)
    while len(urls) > 0:
        url = urls[0]
        res = None
        try:
            res = requests.get(url)
        except requests.exceptions.ConnectionError:
            continue
        if res:
            soup = BeautifulSoup(res.content, "html.parser")
            for lnk in soup.find_all('a'):
                lk = lnk.get('href')
                if lk:
                    if not lk.startswith('http') and (lk.startswith('/') or lk.startswith("#")):
                        lk = base + lk
                    # print(lk, site_map)
                    if lk not in site_map and lk.__contains__('localhost'):
                        # print("Adding")
                        site_map.append(lk)
                        urls.append(lk)
        del urls[0]


class AccessibilityTests(LiveServerTestCase):

    fixtures = ['pgweb/fixtures/users.json', 'pgweb/fixtures/org_types.json',
                'pgweb/fixtures/organisations.json', 'pgweb/core/fixtures/data.json', 'pgweb/fixtures/lang_fixtures.json', 'pgweb/fixtures/approved_events.json']

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
        prepare_site_map(self.live_server_url)
        os.system(f'''lighthouse {self.live_server_url} --only-categories accessibility --chrome-flags="--no-sandbox --headless --disable-gpu" --output json --output-path ./report.json''')
        # os.system('''pa11y-ci --sitemap https://pa11y.org/sitemap.xml -c ./pgweb/conf''')
        # os.system(f'''lightcrawler --url {self.live_server_url} --config ./pgweb/conf.json --chrome-flags="--no-sandbox --headless --disable-gpu --output=html --output-path ./a.html"''')
        # os.system("ls")
        print("----------------------------------")
        # os.system("ls pgweb")
        # os.system("cat ./a.json")
