from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver

from django.test.testcases import call_command, connections
from django.contrib.staticfiles.testing import LiveServerTestCase
import random

from .extra_utils.util_functions import create_permitted_user_with_org_email, generate_session_cookie, varnish_cache
from .profserv.models import ProfessionalService
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


class ProductFormTests(LiveServerTestCase):

    fixtures = ['pgweb/fixtures/users.json',
                'pgweb/fixtures/org_types.json', 'pgweb/fixtures/organisations.json', 'pgweb/downloads/fixtures/data.json', 'pgweb/fixtures/prof_serv.json']

    @ classmethod
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
        cls.region = "europe"

        # Call SQL for simulating local varnish cache
        varnish_cache()

    @ classmethod
    def tearDownClass(cls) -> None:
        cls.selenium.quit()
        return super().tearDownClass()

    def tests_prof_service_approved_submission(self):
        self.selenium.get(self.live_server_url + "/")
        usr = create_permitted_user_with_org_email()
        ck = generate_session_cookie(usr)
        self.selenium.add_cookie(ck)

        self.selenium.get(self.live_server_url + "/account/services/new/")

        # Add Data to fields
        org_elem = self.selenium.find_element(
            By.ID, self.prefix + "org").find_elements(By.TAG_NAME, "option")[1]
        self.org = org_elem.text
        org_elem.click()
        self.selenium.find_element(
            By.ID, self.prefix + "description").send_keys("Service Description is as follows")
        self.selenium.find_element(
            By.ID, self.prefix + "employees").send_keys(" > 200")
        self.selenium.find_element(
            By.ID, self.prefix + "region_europe").click()
        self.selenium.find_element(
            By.ID, self.prefix + "region_northamerica").click()
        self.selenium.find_element(
            By.ID, self.prefix + "locations").send_keys('Location XYZ')
        self.selenium.find_element(
            By.ID, self.prefix + "hours").send_keys(random.randint(12, 100))
        self.selenium.find_element(
            By.ID, self.prefix + "languages").send_keys('Language 1, Language 2')
        self.selenium.find_element(By.ID, self.prefix + "customerexample").send_keys(
            'Customer Example is as follows:\n1.Xyz\nZyx\nMno')
        self.selenium.find_element(By.ID, self.prefix + "experience").send_keys(
            'Customer Experiece is as follows:\n1. Review 1\n2. Review 2\n3. Review 3')
        self.selenium.find_element(By.ID, self.prefix + "contact").send_keys(
            "Contact details:\n1. Phone number: +919191919191\n2. Email Id : support@service.com")
        self.selenium.find_element(
            By.ID, self.prefix + "provides_support").click()
        self.selenium.find_element(
            By.ID, self.prefix + "provides_hosting").click()
        self.selenium.find_element(By.ID, self.prefix + "interfaces").send_keys(
            'Interfaces are:\n1. Interface 1\n2. Interface 2\n3. Interface 3')

        # submit data
        self.selenium.find_element(
            By.XPATH, '/html/body/div[2]/div/div[2]/div/form/button').click()

        # Check for redirection
        heading = self.selenium.find_element(By.TAG_NAME, "h1")
        self.assertEqual(heading.text.lower(), "professional services")
        self.assertEqual(self.selenium.current_url,
                         self.live_server_url + "/account/edit/services/")

        # Check Database and update approval status
        pfs = ProfessionalService.objects.filter(org__name=self.org)
        self.assertTrue(len(pfs) > 0)
        self.assertIsNotNone(pfs.first())
        pfs.first().approved = True
        pfs.first().save()

        # # Check Professional Service page
        # self.selenium.get(self.live_server_url +
        #                   "/support/professional_support/")
        # lks = self.selenium.find_element(
        #     By.ID, 'pgContentWrap').find_elements(By.TAG_NAME, 'a')
        # for lk in lks:
        #     if lk.text.lower().__contains__(self.region):
        #         lk.click()
        #         break
        # # Check If Professional Service page is rendered
        # self.assertEqual(self.selenium.current_url, self.live_server_url +
        #                  "/support/professional_support/" + self.region + "/")
        #
        # headings = self.selenium.find_elements(By.TAG_NAME, 'h2')
        # for heading in headings:
        #     hds = heading.find_elements(By.TAG_NAME, 'a')
        #     for hd in hds:
        #         if hd.text.lower().__contains__(self.org.lower()):
        #             self.assertEqual(hd.text.lower(), self.org.lower())
        # # Check rendered data
        # tables = self.selenium.find_elements(By.TAG_NAME, 'table')
        #
        # req_columns = ["website", "description", "provides", "employees",
        #                "hours", "languages", "customer example", "experience", "office locations", "contact information"]
        # print("Length: ", len(tables))
        #
        # for table in tables:
        #     table_rows = table.find_elements(By.TAG_NAME, 'tr')
        #     for tr in table_rows:
        #         self.assertIn(tr.find_element(
        #             By.TAG_NAME, 'th').text.lower(), req_columns)
        #         # Check data
        #         print(tr.find_element(By.TAG_NAME, 'td').text)

    def test_prof_service_approved_submission_content_rendering(self):

        # Check Professional Service page
        self.selenium.get(self.live_server_url +
                          "/support/professional_support/")
        lks = self.selenium.find_element(
            By.ID, 'pgContentWrap').find_elements(By.TAG_NAME, 'a')
        for lk in lks:
            if lk.text.lower().__contains__(self.region):
                lk.click()
                break

        # Check If Professional Service page is rendered
        self.assertEqual(self.selenium.current_url, self.live_server_url +
                         "/support/professional_support/" + self.region + "/")

        org = "Test12"
        headings = self.selenium.find_elements(By.TAG_NAME, 'h2')
        for heading in headings:
            hds = heading.find_elements(By.TAG_NAME, 'a')
            for hd in hds:
                if hd.text.lower().__contains__(org.lower()):
                    self.assertEqual(hd.text.lower(), org.lower())
                    self.assertNotEqual(hd.text.lower(), 'shiksha sopan')
        # Check rendered data
        tables = self.selenium.find_elements(By.TAG_NAME, 'table')

        req_columns = ["website", "description", "provides", "employees",
                       "hours", "languages", "customer example", "experience", "office locations", "contact information"]
        print("Length: ", len(tables))

        for table in tables:
            table_rows = table.find_elements(By.TAG_NAME, 'tr')
            for tr in table_rows:
                self.assertIn(tr.find_element(
                    By.TAG_NAME, 'th').text.lower(), req_columns)
                # Check data
                print(tr.find_element(By.TAG_NAME, 'td').text)
