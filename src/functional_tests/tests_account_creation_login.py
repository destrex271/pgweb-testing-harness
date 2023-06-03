from django.contrib.staticfiles.testing import LiveServerTestCase
from django.test.testcases import call_command, connections
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver

from django.contrib.auth.models import User

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

# Account creation test


class CreateUserAccount(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.FirefoxOptions()
        options.headless = True
        cls.selenium = webdriver.Firefox(
            executable_path=GeckoDriverManager().install(), options=options)
        cls.username = "testuser"
        cls.firstname = "test"
        cls.lastname = "user"
        cls.email = "testuser@gmail.com"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.selenium.quit()
        super().tearDownClass()

    def test_create_account(self):
        create_addr = "/account/signup/"
        prefix = "id_"
        print(self.live_server_url + create_addr)
        self.selenium.get(self.live_server_url + create_addr)
        username_field = self.selenium.find_element(By.ID, prefix+"username")
        firstname_field = self.selenium.find_element(
            By.ID, prefix+"first_name")
        lastname_field = self.selenium.find_element(By.ID, prefix+"last_name")
        email_field = self.selenium.find_element(By.ID, prefix+"email")
        email2_field = self.selenium.find_element(By.ID, prefix+"email2")
        sub_btn = self.selenium.find_element(
            By.XPATH, '/html/body/div[2]/div/div[2]/div/form/button')

        username_field.send_keys(self.username)
        firstname_field.send_keys(self.firstname)
        lastname_field.send_keys(self.lastname)
        email_field.send_keys(self.email)
        email2_field.send_keys(self.email)

        sub_btn.click()

        # Check for successfull completion and redirection
        print(self.selenium.current_url)
        self.assertTrue(self.selenium.current_url !=
                        self.live_server_url + create_addr)

        # Query the Database to check if the user was actually registered
        usr = User.objects.filter(
            username=self.username,
            first_name=self.firstname,
            last_name=self.lastname,
            email=self.email,
        )

        print(usr)
        self.assertTrue(len(usr) == 1)
