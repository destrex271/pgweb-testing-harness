from django.contrib.staticfiles.testing import LiveServerTestCase
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver
import urllib

class MySeleniumTests(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        options = webdriver.FirefoxOptions()
        options.headless = True
        cls.selenium = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=options)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()

    def test_home_page_links(self):
        print(self.live_server_url)
        self.selenium.get(f"{self.live_server_url}/")
        links = self.selenium.find_elements(By.TAG_NAME, "a")
        for link in links:
            txt = link.get_attribute("href")
            x = urllib.request.urlopen(txt)
            print(x.getcode())
        assert len(links) != 0
