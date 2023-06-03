from django.contrib.staticfiles.testing import LiveServerTestCase
from django.test.testcases import call_command, connections
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver
import requests

# Custom utilities
from pgweb.utils.report_generation import write_to_report

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

# Generate a list of all the urls of the website


def segregate_links(seln, addr):
    init_count = 0
    seln.get(f"{addr}/")
    links = seln.find_elements(By.TAG_NAME, 'a')
    fl = open('urls.txt', 'w+')
    for link in links:
        lnk = link.get_attribute('href')
        init_count += 1
        fl.write(lnk)
        if lnk.__contains__('localhost'):
            internal_links.append(lnk)
        else:
            external_links.append(lnk)

    counter = 0
    for link in internal_links:
        if counter == init_count:
            break
        seln.get(f"{addr}")
        lnks = seln.find_elements(By.TAG_NAME, 'a')
        for lk in lnks:
            v = lk.get_attribute('href')
            if v.__contains__('localhost') and not v in internal_links:
                fl.write(v)
                internal_links.append(v)
            elif not v in external_links and not v.__contains__('localhost'):
                fl.write(v)
                external_links.append(v)
        counter += 1
    fl.close()


class RecusrsiveLinkCrawlTests(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.FirefoxOptions()
        options.headless = True
        cls.selenium = webdriver.Firefox(
            executable_path=GeckoDriverManager().install(), options=options)
        segregate_links(cls.selenium, cls.live_server_url)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_external_links(self):
        for lnk in external_links:
            res = requests.get(lnk)
            if not res is None:
                stat = res.status_code
                if not stat == 200:
                    broken_external_links[lnk] = stat
            else:
                broken_external_links[lnk] = "Not reachable"
        if len(broken_external_links) > 0:
            write_to_report(broken_external_links, "Broken External Urls")
        self.assertTrue(len(broken_external_links) ==
                        0, msg=broken_external_links)

    def test_internal_links(self):
        for lnk in internal_links:
            res = requests.get(lnk)
            if not res is None:
                stat = res.status_code
                if not stat == 200:
                    broken_internal_links[lnk] = stat
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

        # Final List of Broken Urls
        if len(broken_internal_links) > 0:
            write_to_report(broken_internal_links, "Broken Internal Urls")

        self.assertTrue(len(broken_internal_links) ==
                        0, msg=broken_internal_links)
