from django.contrib.staticfiles.testing import LiveServerTestCase
from django.test.testcases import call_command, connections
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver
import requests

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

external_links = []
internal_links = []
broken_internal_links = []
broken_external_links = []


def segregate_links(seln, addr):
    seln.get(f"{addr}/")
    links = seln.find_elements(By.TAG_NAME, 'a')
    for link in links:
        lnk = link.get_attribute('href')
        if lnk.__contains__('localhost'):
            internal_links.append(lnk)
        else:
            external_links.append(lnk)


class RecusrsiveLinkCrawlTests(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.FirefoxOptions()
        options.headless = True
        cls.selenium = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=options)
        segregate_links(cls.selenium, cls.live_server_url)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_external_links(self):
        for lnk in external_links:
            print(lnk)
            if not requests.get(lnk).status_code == 200:
                broken_external_links.append(lnk)
        self.assertLessEqual(len(broken_external_links), 1, msg=broken_external_links)

    def test_internal_links(self):
        for lnk in internal_links:
            print(lnk)
            if not requests.get(lnk).status_code == 200:
                broken_internal_links.append(lnk)
        self.assertLessEqual(len(broken_internal_links), 1, msg=broken_internal_links)


# class RecusrsiveLinkCrawlTests_InternalLinks(LiveServerTestCase):
#     
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         options = webdriver.FirefoxOptions()
#         options.headless = True
#         cls.selenium = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=options)
#
#     @classmethod
#     def tearDownClass(cls):
#         cls.selenium.quit()
#         super().tearDownClass()
