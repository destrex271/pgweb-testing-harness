import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver

from django.test.testcases import call_command, connections
from django.contrib.staticfiles.testing import LiveServerTestCase
import random

from .extra_utils.util_functions import create_permitted_user, generate_session_cookie, varnish_cache


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


class BugReportsForm(LiveServerTestCase):

    fixtures = ['pgweb/fixtures/users.json', 'pgweb/fixtures/org_types.json',
                'pgweb/fixtures/organisations.json']

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

        # dummy data
        cls.name = "Dummy Bug"

        varnish_cache()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.selenium.quit()
        super().tearDownClass()

    def tests_bug_report_submit(self):
        # Login user by setting session cookie
        self.selenium.get(self.live_server_url + "/")
        ck = generate_session_cookie(create_permitted_user())
        self.selenium.add_cookie(ck)

        # Routing to main page to execute tests
        self.selenium.get(self.live_server_url + "/account/submitbug/")

        self.selenium.find_element(
            By.ID, self.prefix + "name").send_keys(self.name)
        self.selenium.find_element(
            By.ID, self.prefix + "pgversion").find_elements(By.TAG_NAME, "option")[1]
        self.selenium.find_element(
            By.ID, self.prefix + "os").send_keys("Linux x86_64")
        self.selenium.find_element(By.ID, self.prefix + "shortdesc").send_keys(
            "This is a short description for this dummy bug")
        self.selenium.find_element(By.ID, self.prefix + "details").send_keys(
            "These are the details of the Dummy Bug:\n\t1. Bug 1\n\t2. Bug 2")

        # submit bug
        self.selenium.find_element(
            By.XPATH, "/html/body/div[2]/div/div[2]/div/form/button").click()

        self.selenium.find_element(
            By.ID, self.prefix + "pgversion").find_elements(By.TAG_NAME, "option")[1]
