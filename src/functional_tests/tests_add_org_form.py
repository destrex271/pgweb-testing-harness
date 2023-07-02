import random
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver

from django.test.testcases import call_command, connections
from django.contrib.staticfiles.testing import LiveServerTestCase

# Util functions

from .extra_utils.util_functions import create_permitted_user, generate_session_cookie, varnish_cache

# Models from pgweb codebase
from .core.models import Organisation

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


class OrgFormTests(LiveServerTestCase):

    fixtures = ['pgweb/fixtures/users.json',
                'pgweb/fixtures/org_types.json', 'pgweb/fixtures/organisations.json']

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
        cls.org_name = "Organisation XYZ"
        cls.address = "Org addres, STR Road, Dehradun, India"
        cls.url = "https://kyllex.live"

        # Call SQL for simulating local varnish cache
        varnish_cache()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.selenium.quit()
        return super().tearDownClass()

    def test_add_organisation(self):

        # Login User
        self.selenium.get(self.live_server_url + "/")
        perm_user = create_permitted_user()
        ck = generate_session_cookie(perm_user)
        self.selenium.add_cookie(ck)

        # Add Organisation Page
        self.selenium.get(self.live_server_url + "/account/organisations/new/")

        # check if login succeeded
        heading = self.selenium.find_element(By.TAG_NAME, 'h1')
        self.assertEqual(heading.text.lower().strip(), 'new organisation')

        # Fill all the fields
        self.selenium.find_element(
            By.ID, self.prefix + "name").send_keys(self.org_name)
        self.selenium.find_element(
            By.ID, self.prefix + "address").send_keys(self.address)
        self.selenium.find_element(
            By.ID, self.prefix + "url").send_keys(self.url)
        # Org type dropdown
        types = self.selenium.find_element(
            By.ID, self.prefix + "orgtype").find_elements(By.TAG_NAME, 'option')
        k = random.randint(1, len(types) - 1)
        for t in types:
            print(t.text)
        print("Selected ", types[k].text)
        types[k].click()

        # Submit Data
        self.selenium.find_element(
            By.XPATH, '/html/body/div[2]/div/div[2]/div/form/button').click()

        # Check if the page was redirected to organisations
        print(self.selenium.current_url)

        heading = self.selenium.find_element(By.TAG_NAME, 'h1').text
        self.assertEqual(heading.lower().strip(), 'organisations')

        # Check if org is under moderator approval
        li = self.selenium.find_element(
            By.XPATH, "/html/body/div[2]/div/div[2]/div/ul").find_elements(By.TAG_NAME, 'li')

        txt = []
        for l in li:
            txt.append(l.text)

        self.assertTrue(txt.__contains__(self.org_name))

        # Check Against Database
        x = Organisation.objects.filter(name=self.org_name)
        self.assertNotEqual(len(x), 0)

    def test_org_form_alerts_on_wrong_data(self):

        # Login User
        self.selenium.get(self.live_server_url + "/")
        perm_user = create_permitted_user()
        ck = generate_session_cookie(perm_user)
        self.selenium.add_cookie(ck)

        # Add Organisation Page
        self.selenium.get(self.live_server_url + "/account/organisations/new/")

        # check if login succeeded
        heading = self.selenium.find_element(By.TAG_NAME, 'h1')
        self.assertEqual(heading.text.lower().strip(), 'new organisation')

        # Submit Data
        self.selenium.find_element(
            By.XPATH, '/html/body/div[2]/div/div[2]/div/form/button').click()

        # Check if page redirected or not
        self.assertNotEqual(self.selenium.current_url,
                            self.live_server_url + "/account/organisation/new/")
