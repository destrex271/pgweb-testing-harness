from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.chrome import ChromeType
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver

class MySeleniumTests(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = webdriver.Firefox(executable_path=GeckoDriverManager().install())
        # chrome_service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        # chrome_options = Options()
        # options = [
        #     "--no-sandbox",
        #     "--headless",
        #     "--disable-gpu",
        #     "--window-size=1920,1200",
        #     "--ignore-certificate-errors",
        #     "--disable-extensions",
        #     # "--disable-dev-shm-usage"
        # ]
        # for option in options:
        #     chrome_options.add_argument(option)
        #
        # cls.selenium = webdriver.Chrome(service=chrome_service, options=chrome_options)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_home_page_links(self):
        self.selenium.get(f"{self.live_server_url}/")
        links = self.selenium.find_element(By.TAG_NAME, "a")
        print(links)

