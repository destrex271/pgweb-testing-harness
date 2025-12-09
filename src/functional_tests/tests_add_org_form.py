import random
from selenium.webdriver.common.by import By

from django.test.testcases import call_command, connections
from django.contrib.staticfiles.testing import LiveServerTestCase

# Util functions

from .extra_utils.util_functions import create_permitted_user, generate_session_cookie, varnish_cache, fixture_teardown, create_firefox_driver

# Models from pgweb codebase
from .core.models import Organisation

LiveServerTestCase._fixture_teardown = fixture_teardown


class OrgFormTests(LiveServerTestCase):

    fixtures = ['pgweb/fixtures/users.json',
                'pgweb/fixtures/org_types.json', 'pgweb/fixtures/organisations.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Prefix vars
        cls.prefix = "id_"

        # Webdriver Configuration
        cls.selenium = create_firefox_driver()

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
        types[k].click()

        # Submit Data
        self.selenium.find_element(
            By.XPATH, '/html/body/div[2]/div/div[2]/div/form/button').click()

        # Check if the page was redirected to organisations
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
