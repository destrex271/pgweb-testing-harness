from django.contrib.staticfiles.testing import LiveServerTestCase
from django.test.testcases import call_command, connections
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver

from django.contrib.auth.models import User
from string import punctuation

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
        serv = Service(executable_path=GeckoDriverManager().install())
        cls.selenium = webdriver.Firefox(
            service=serv, options=options)
        cls.username = "testuser"
        cls.firstname = "test"
        cls.lastname = "user"
        cls.email = "testuser@gmail.com"
        cls.passwd = "test123@#"
        cls.prefix = "id_"
        cls.create_addr = "/account/signup/"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.selenium.quit()
        super().tearDownClass()

    def test_create_account_with_valid_parmas(self):
        self.selenium.get(self.live_server_url + self.create_addr)
        username_field = self.selenium.find_element(
            By.ID, self.prefix+"username")
        firstname_field = self.selenium.find_element(
            By.ID, self.prefix+"first_name")
        lastname_field = self.selenium.find_element(
            By.ID, self.prefix+"last_name")
        email_field = self.selenium.find_element(By.ID, self.prefix+"email")
        email2_field = self.selenium.find_element(By.ID, self.prefix+"email2")
        sub_btn = self.selenium.find_element(
            By.XPATH, '/html/body/div[2]/div/div[2]/div/form/button')

        # Automation Sequence
        username_field.send_keys(self.username)
        firstname_field.send_keys(self.firstname)
        lastname_field.send_keys(self.lastname)
        email_field.send_keys(self.email)
        email2_field.send_keys(self.email)

        sub_btn.click()

        # Check for successfull completion and redirection
        self.assertNotEqual(self.selenium.current_url,
                            self.live_server_url + self.create_addr)

        # Query the Database to check if the user was actually registered
        usr = User.objects.filter(
            username=self.username,
            first_name=self.firstname,
            last_name=self.lastname,
            email=self.email,
        )
        self.assertEqual(len(usr), 1)

    def test_account_creation_invalid_username(self):
        # Generating a set of all special chars to generate an invalid username
        sequences = set(punctuation)
        sequences.remove('-')
        sequences.remove('.')
        for x in sequences:
            self.selenium.get(self.live_server_url + self.create_addr)
            username_field = self.selenium.find_element(
                By.ID, self.prefix+"username")
            firstname_field = self.selenium.find_element(
                By.ID, self.prefix+"first_name")
            lastname_field = self.selenium.find_element(
                By.ID, self.prefix+"last_name")
            email_field = self.selenium.find_element(
                By.ID, self.prefix+"email")
            email2_field = self.selenium.find_element(
                By.ID, self.prefix+"email2")
            sub_btn = self.selenium.find_element(
                By.XPATH, '/html/body/div[2]/div/div[2]/div/form/button')

            # Automation Sequence
            username_field.send_keys(self.username + x)
            firstname_field.send_keys(self.firstname)
            lastname_field.send_keys(self.lastname)
            email_field.send_keys(self.email)
            email2_field.send_keys(self.email)

            sub_btn.click()

            # Check user registration status
            self.assertEqual(self.selenium.current_url,
                             self.live_server_url+self.create_addr)

            # Checking Alert messages
            alert = self.selenium.find_elements(By.CLASS_NAME, "alert")
            self.assertEqual(
                alert[0].text, "Please correct the errors below, and re-submit the form.")
            self.assertEqual(
                alert[1].text, "Invalid character in user name. Only a-z, 0-9, . and - allowed for compatibility with third party software.")

            # Check for any entries in Database
            usrs = User.objects.filter(username=self.username + x)
            self.assertEqual(len(usrs), 0)

    def test_create_account_diff_emails(self):
        self.selenium.get(self.live_server_url + self.create_addr)
        username_field = self.selenium.find_element(
            By.ID, self.prefix+"username")
        firstname_field = self.selenium.find_element(
            By.ID, self.prefix+"first_name")
        lastname_field = self.selenium.find_element(
            By.ID, self.prefix+"last_name")
        email_field = self.selenium.find_element(By.ID, self.prefix+"email")
        email2_field = self.selenium.find_element(By.ID, self.prefix+"email2")
        sub_btn = self.selenium.find_element(
            By.XPATH, '/html/body/div[2]/div/div[2]/div/form/button')

        # Automation Sequence
        username_field.send_keys(self.username)
        firstname_field.send_keys(self.firstname)
        lastname_field.send_keys(self.lastname)
        email_field.send_keys(self.email)
        email2_field.send_keys("$%dif" + self.email)

        sub_btn.click()

        # Check for successfull completion and redirection
        self.assertEqual(self.selenium.current_url,
                         self.live_server_url + self.create_addr)

        # Check for alerts
        alerts = self.selenium.find_elements(By.CLASS_NAME, "alert")
        self.assertEqual(
            alerts[0].text, "Please correct the errors below, and re-submit the form.")
        self.assertEqual(alerts[1].text, "Email addresses don't match")

        # Check for any wrong entries in the database
        users = User.objects.filter(username=self.username)
        self.assertEqual(len(users), 0)

    def test_create_account_invalid_email(self):
        self.selenium.get(self.live_server_url + self.create_addr)
        username_field = self.selenium.find_element(
            By.ID, self.prefix+"username")
        firstname_field = self.selenium.find_element(
            By.ID, self.prefix+"first_name")
        lastname_field = self.selenium.find_element(
            By.ID, self.prefix+"last_name")
        email_field = self.selenium.find_element(By.ID, self.prefix+"email")
        email2_field = self.selenium.find_element(By.ID, self.prefix+"email2")
        sub_btn = self.selenium.find_element(
            By.XPATH, '/html/body/div[2]/div/div[2]/div/form/button')

        # Automation Sequence
        username_field.send_keys(self.username)
        firstname_field.send_keys(self.firstname)
        lastname_field.send_keys(self.lastname)
        email_field.send_keys(self.email.replace("@", ""))
        email2_field.send_keys("$%dif" + self.email)

        sub_btn.click()

        # Check for successfull completion and redirection
        self.assertEqual(self.selenium.current_url,
                         self.live_server_url + self.create_addr)

        # Check for any wrong entries in the database
        users = User.objects.filter(username=self.username)
        self.assertEqual(len(users), 0)


class UserLoginTests(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.FirefoxOptions()
        options.headless = True
        serv = Service(executable_path=GeckoDriverManager().install())
        cls.selenium = webdriver.Firefox(
            service=serv, options=options)
        cls.username = "root"
        cls.email = "root@gmail.com"
        cls.passwd = "root"
        cls.login_path = "/account/login/"
        cls.prefix = "id_"
        call_command('loaddata', 'pgweb/fixtures/users.json')
        print("Loaded fixtures")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.selenium.quit()
        super().tearDownClass()

    def test_registered_account_login(self):
        self.selenium.get(self.live_server_url + self.login_path)
        # Capturing DOM elements
        username_field = self.selenium.find_element(
            By.ID, self.prefix + "username")
        passwd_field = self.selenium.find_element(
            By.ID, self.prefix + "password")
        sub_btn = self.selenium.find_element(
            By.XPATH, "/html/body/div[2]/div/div[2]/div/form/div[3]/input")

        # Automation sequence
        username_field.send_keys(self.username)
        passwd_field.send_keys(self.passwd)
        sub_btn.click()

        self.assertEqual(self.selenium.current_url,
                         self.live_server_url + "/account/")

        heading = self.selenium.find_element(By.TAG_NAME, 'h1')
        self.assertEqual(heading.text, "Your account")

    # def test_registered_account_login_with_email(self):
    #     self.selenium.get(self.live_server_url + self.login_path)
    #     # Capturing DOM elements
    #     username_field = self.selenium.find_element(
    #         By.ID, self.prefix + "username")
    #     passwd_field = self.selenium.find_element(
    #         By.ID, self.prefix + "password")
    #     sub_btn = self.selenium.find_element(
    #         By.XPATH, "/html/body/div[2]/div/div[2]/div/form/div[3]/input")
    #
    #     # Automation sequence
    #     username_field.send_keys(self.email)
    #     passwd_field.send_keys(self.passwd)
    #     sub_btn.click()
    #
    #     self.assertEqual(self.selenium.current_url,
    #                      self.live_server_url + "/account/")
    #
    #     heading = self.selenium.find_element(By.TAG_NAME, 'h1')
    #     self.assertEqual(heading.text, "Your account")

    def test_unregistered_account_login(self):
        self.selenium.get(self.live_server_url + self.login_path)
        # Capturing fields on webpage
        username_field = self.selenium.find_element(
            By.ID, self.prefix+"username"
        )
        passwd_field = self.selenium.find_element(
            By.ID, self.prefix + "password"
        )
        sub_btn = self.selenium.find_element(
            By.XPATH, "/html/body/div[2]/div/div[2]/div/form/div[3]/input")

        # Automation Sequence
        username_field.send_keys("abcdefg")
        passwd_field.send_keys("password123#")
        sub_btn.click()

        self.assertEqual(self.selenium.current_url,
                         self.live_server_url + self.login_path)

        heading = self.selenium.find_element(By.TAG_NAME, 'h1')
        self.assertEqual(heading.text, "Sign in")

        alert = self.selenium.find_element(By.CLASS_NAME, 'alert')
        self.assertEqual(
            alert.text, "Please enter a correct username and password. Note that both fields may be case-sensitive.")

    def test_registered_account_wrong_password_login(self):
        self.selenium.get(self.live_server_url + self.login_path)
        # Capturing fields on webpage
        username_field = self.selenium.find_element(
            By.ID, self.prefix+"username"
        )
        passwd_field = self.selenium.find_element(
            By.ID, self.prefix + "password"
        )
        sub_btn = self.selenium.find_element(
            By.XPATH, "/html/body/div[2]/div/div[2]/div/form/div[3]/input")

        # Automation Sequence
        username_field.send_keys(self.username)
        passwd_field.send_keys("passwrd123#")
        sub_btn.click()

        self.assertEqual(self.selenium.current_url,
                         self.live_server_url + self.login_path)

        heading = self.selenium.find_element(By.TAG_NAME, 'h1')
        self.assertEqual(heading.text, "Sign in")

        alert = self.selenium.find_element(By.CLASS_NAME, 'alert')
        self.assertEqual(
            alert.text, "Please enter a correct username and password. Note that both fields may be case-sensitive.")
