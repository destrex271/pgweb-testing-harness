from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver

from django.test.testcases import call_command, connections
from django.contrib.staticfiles.testing import LiveServerTestCase
import random

from .extra_utils.util_functions import create_permitted_user_with_org_email, generate_session_cookie, varnish_cache
from .downloads.models import Product


markup_content = '''<h1>Introducing Product X: Revolutionizing the Way You Work</h1>
  <p>Product X is a game-changing solution designed to transform the way you work, boosting productivity, efficiency, and collaboration like never before.</p>
  <h2>Unleash Your Potential</h2>
  <p>With Product X, you can unleash your full potential by streamlining your workflow and eliminating unnecessary manual tasks. Its intuitive interface and powerful automation features allow you to focus on what truly matters, while it handles the rest.</p>
  <h2>Seamless Integration</h2>
  <p>Product X seamlessly integrates with your existing tools and systems, ensuring a smooth transition and minimizing disruption. Whether you use popular productivity suites or specialized software, Product X effortlessly integrates to provide a unified and efficient work environment.</p>
  <p>Experience the benefits of automation, seamless integration with existing tools, and a user-friendly interface that simplifies complex tasks. Say goodbye to manual processes and embrace a new era of efficiency with Product X.</p>'''

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
                'pgweb/fixtures/org_types.json', 'pgweb/fixtures/organisations.json', 'pgweb/downloads/fixtures/data.json']

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
        cls.name = "Product XYZ"

        # Call SQL for simulating local varnish cache
        varnish_cache()

    @ classmethod
    def tearDownClass(cls) -> None:
        cls.selenium.quit()
        return super().tearDownClass()

    def test_product_submit_and_approval(self):
        self.selenium.get(self.live_server_url + "/")
        usr = create_permitted_user_with_org_email()
        ck = generate_session_cookie(usr)
        self.selenium.add_cookie(ck)

        self.selenium.get(self.live_server_url + "/account/products/new/")
        print(self.selenium.current_url)

        # Add data to fields
        self.selenium.find_element(
            By.ID, self.prefix + "name").send_keys(self.name)
        self.selenium.find_element(
            By.ID, self.prefix + "url").send_keys('https://kyllex.live')
        org_drop_down_elems = self.selenium.find_element(By.ID,
                                                         self.prefix + "org").find_elements(By.TAG_NAME, 'option')
        ind = random.randint(
            1, len(org_drop_down_elems) - 1)
        org_drop_down_elems[ind].click()

        catg_drop_down_elems = self.selenium.find_element(By.ID,
                                                          self.prefix + "category").find_elements(By.TAG_NAME, 'option')
        ind = random.randint(
            1, len(catg_drop_down_elems) - 1)
        self.ctg = catg_drop_down_elems[ind].text
        catg_drop_down_elems[ind].click()

        lict_drop_down_elems = self.selenium.find_element(By.ID,
                                                          self.prefix + "licencetype").find_elements(By.TAG_NAME, 'option')
        ind = random.randint(
            1, len(lict_drop_down_elems) - 1)
        lict_drop_down_elems[ind].click()

        self.selenium.find_element(
            By.ID, self.prefix + "description").send_keys(markup_content)

        # Save product
        self.selenium.find_element(
            By.XPATH, "/html/body/div[2]/div/div[2]/div/form/button").click()

        alerts = self.selenium.find_elements(By.CLASS_NAME, 'alert')
        print("ALERTS: ")
        for alert in alerts:
            print(alert.text)

        # Check for redirection
        heading = self.selenium.find_element(By.TAG_NAME, 'h1').text
        self.assertEqual(heading.lower(), "products")
        self.assertEqual(self.selenium.current_url,
                         self.live_server_url + "/account/edit/products/")

        # Check Database
        prds = Product.objects.filter(name=self.name)
        self.assertEqual(len(prds), 1)
        prds.first().approved = True
        prds.first().save()
        print(prds.first())

        # Check Downloads page
        self.selenium.get(self.live_server_url +
                          "/download/product-categories/")

        link = self.selenium.find_element(By.LINK_TEXT, self.ctg)
        link.click()

        print(self.selenium.current_url)
        table_elems = self.selenium.find_elements(
            By.TAG_NAME, 'table')
        print("Links")
        for tb in table_elems:
            lks = tb.find_elements(By.TAG_NAME, 'a')
            for lk in lks:
                print(lk.text)
                if lk.text.__contains__(self.name):
                    self.assertEqual(lk.text.lower(), self.name.lower())

    def test_unapproved_product_submit(self):
        self.selenium.get(self.live_server_url + "/")
        usr = create_permitted_user_with_org_email()
        ck = generate_session_cookie(usr)
        self.selenium.add_cookie(ck)

        self.selenium.get(self.live_server_url + "/account/products/new/")
        print(self.selenium.current_url)

        # Add data to fields
        self.selenium.find_element(
            By.ID, self.prefix + "name").send_keys(self.name)
        self.selenium.find_element(
            By.ID, self.prefix + "url").send_keys('https://kyllex.live')
        org_drop_down_elems = self.selenium.find_element(By.ID,
                                                         self.prefix + "org").find_elements(By.TAG_NAME, 'option')
        ind = random.randint(
            1, len(org_drop_down_elems) - 1)
        org_drop_down_elems[ind].click()

        catg_drop_down_elems = self.selenium.find_element(By.ID,
                                                          self.prefix + "category").find_elements(By.TAG_NAME, 'option')
        ind = random.randint(
            1, len(catg_drop_down_elems) - 1)
        self.ctg = catg_drop_down_elems[ind].text
        catg_drop_down_elems[ind].click()

        lict_drop_down_elems = self.selenium.find_element(By.ID,
                                                          self.prefix + "licencetype").find_elements(By.TAG_NAME, 'option')
        ind = random.randint(
            1, len(lict_drop_down_elems) - 1)
        lict_drop_down_elems[ind].click()

        self.selenium.find_element(
            By.ID, self.prefix + "description").send_keys(markup_content)

        # Save product
        self.selenium.find_element(
            By.XPATH, "/html/body/div[2]/div/div[2]/div/form/button").click()

        alerts = self.selenium.find_elements(By.CLASS_NAME, 'alert')
        print("ALERTS: ")
        for alert in alerts:
            print(alert.text)

        # Check for redirection
        heading = self.selenium.find_element(By.TAG_NAME, 'h1').text
        self.assertEqual(heading.lower(), "products")
        self.assertEqual(self.selenium.current_url,
                         self.live_server_url + "/account/edit/products/")

        # Check Database
        prds = Product.objects.filter(name=self.name)
        self.assertEqual(len(prds), 1)

        # Check Downloads page
        self.selenium.get(self.live_server_url +
                          "/download/product-categories/")

        link = self.selenium.find_element(By.LINK_TEXT, self.ctg)
        link.click()

        print(self.selenium.current_url)
        table_elems = self.selenium.find_elements(
            By.TAG_NAME, 'table')
        flag = True
        for tb in table_elems:
            lks = tb.find_elements(By.TAG_NAME, 'a')
            for lk in lks:
                print(lk.text)
                if lk.text.__contains__(self.name):
                    flag = False

        self.assertTrue(flag)
