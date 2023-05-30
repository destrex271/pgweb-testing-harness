from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
# from webdriver_manager.chrome import ChromeType
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver

class MySeleniumTests(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.FirefoxOptions()
        options.headless = True
        cls.selenium = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=options)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_home_page_links(self):
        self.selenium.get(f"{self.live_server_url}/")
        links = self.selenium.find_element(By.TAG_NAME, "a")
        print(links)

