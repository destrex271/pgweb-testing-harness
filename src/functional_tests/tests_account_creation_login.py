from django.contrib.staticfiles.testing import LiveServerTestCase
from django.test.testcases import call_command, connections
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver
import selenium

from django.contrib.auth.models import User
from string import punctuation

from .extra_utils.util_functions import create_permitted_user, generate_session_cookie, fixture_teardown

LiveServerTestCase._fixture_teardown = fixture_teardown

# Account creation test


class CreateUserAccount(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.FirefoxOptions()
        options.headless = True
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
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

    fixtures = ['pgweb/fixtures/users.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.FirefoxOptions()
        options.headless = True
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        serv = Service(executable_path=GeckoDriverManager().install())
        cls.selenium = webdriver.Firefox(
            service=serv, options=options)
        cls.username = "root"
        cls.email = "root@gmail.com"
        cls.passwd = "root"
        cls.login_path = "/account/login/"
        cls.prefix = "id_"

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
        self.assertEqual(heading.text.lower().strip(), "your account")

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
        self.assertEqual(heading.text.lower().strip(), "sign in")

        alert = self.selenium.find_element(By.CLASS_NAME, 'alert')
        self.assertEqual(
            alert.text.lower().strip(), "please enter a correct username and password. note that both fields may be case-sensitive.")

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
        self.assertEqual(heading.text.lower().strip(), "sign in")

        alert = self.selenium.find_element(By.CLASS_NAME, 'alert')
        self.assertEqual(
            alert.text.lower().strip(), "please enter a correct username and password. note that both fields may be case-sensitive.")

class EditProfileFormTests(LiveServerTestCase):

    fixtures = ['pgweb/fixtures/users.json',
                'pgweb/fixtures/org_types.json', 'pgweb/fixtures/organisations.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.FirefoxOptions()
        options.headless = True
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        serv = Service(executable_path=GeckoDriverManager().install())
        cls.selenium = webdriver.Firefox(
            service=serv, options=options)
        cls.username = "root"
        cls.alt_email = "root2@gmail.com"
        cls.alt_first_name = "rootfname"
        cls.alt_last_name = "rootlname"
        cls.passwd = "root"
        cls.login_path = "/account/login/"
        cls.prefix = "id_"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.selenium.quit()
        super().tearDownClass()

    def test_add_secondary_email(self):

        # Login sequence
        self.selenium.get(self.live_server_url + "/")
        perm_user = create_permitted_user()
        ck = generate_session_cookie(perm_user)
        self.selenium.add_cookie(ck)

        self.selenium.get(self.live_server_url + "/account/profile/")


        self.selenium.find_element(By.ID, self.prefix+"first_name").send_keys(self.alt_first_name)
        self.selenium.find_element(By.ID, self.prefix+"last_name").send_keys(self.alt_last_name)
        self.selenium.find_element(By.ID, self.prefix+"email1").send_keys(self.alt_email)
        self.selenium.find_element(By.ID, self.prefix+"email2").send_keys(self.alt_email)

        # submit data
        self.selenium.find_element(By.XPATH, "/html/body/div[2]/div/div[2]/div/form/div[9]/input").click()

        # Check if displayed under profile section
        try:
            elems = self.selenium.find_element(By.ID, "pgContentWrap").find_elements(By.TAG_NAME, "li")
            # print(elems)
            text_li = []
            for elem in elems:
                text_li.append(elem.text[:elem.text.find("(")].replace(' ', ''))
            # print(text_li)
            self.assertIn(self.alt_email, text_li)
        except selenium.common.exceptions.NoSuchElementException:
            self.assertTrue(False, msg="Secondary email not listed on profile page")

    # def test_delete_secondary_email(self):
    #
    #     # Login sequence
    #     self.selenium.get(self.live_server_url + "/")
    #     perm_user = create_permitted_user()
    #     ck = generate_session_cookie(perm_user)
    #     self.selenium.add_cookie(ck)
    #
    #     self.selenium.get(self.live_server_url + "/account/profile/")
    #
    #     # Add name & email
    #     self.selenium.find_element(By.ID, self.prefix+"first_name").send_keys(self.alt_first_name)
    #     self.selenium.find_element(By.ID, self.prefix+"last_name").send_keys(self.alt_last_name)
    #     self.selenium.find_element(By.ID, self.prefix+"email1").send_keys(self.alt_email)
    #     self.selenium.find_element(By.ID, self.prefix+"email2").send_keys(self.alt_email)
    #
    #     # submit data
    #     self.selenium.find_element(By.XPATH, "/html/body/div[2]/div/div[2]/div/form/div[9]/input").click()
    #
    #     # Check if displayed under profile section
    #     try:
    #         elems = self.selenium.find_element(By.ID, "pgContentWrap").find_elements(By.TAG_NAME, "li")
    #         text_li = []
    #         print(elems)
    #         for elem in elems:
    #             text_li.append(elem.text[:elem.text.find("(")].replace(' ', ''))
    #         self.assertIn(self.alt_email, text_li)
    #         el = None
    #         for elem in elems:
    #             if elem.text.__contains__(self.alt_email):
    #                 el = elem
    #                 print("Found!")
    #                 break
    #         self.assertFalse(el == None)
    #         if el:
    #             x = el.find_element(By.TAG_NAME, 'input')
    #             print(x)
    #             x.click()
    #             # submit data
    #             self.selenium.find_element(By.XPATH, "/html/body/div[2]/div/div[2]/div/form/div[9]/input").click()
    #             print("Deleted!")
    #
    #         elems = self.selenium.find_element(By.ID, "pgContentWrap").find_elements(By.TAG_NAME, "li")
    #         print(elems[0].text)
    #         self.assertEqual(len(elems), 0)
    #     except selenium.common.exceptions.NoSuchElementException:
    #         self.assertTrue(False, msg="No secondary emails present")
