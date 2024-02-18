import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver

from django.test.testcases import call_command, connections
from django.contrib.staticfiles.testing import LiveServerTestCase

from .extra_utils.util_functions import create_permitted_user_with_org_email, generate_session_cookie, varnish_cache, fixture_teardown

from .news.models import NewsArticle


LiveServerTestCase._fixture_teardown = fixture_teardown
# ---------------------------

markup_content = '''
<h1>PostgreSQL 16: Enhanced Performance and Advanced Features</h1>
<p class="article-metadata">By Jane Wilson | June 25, 2023</p>
<div class="article-content">
  <p>PostgreSQL, the popular open-source relational database management system, has released version 16, bringing significant improvements and advanced features to its users. With a focus on performance and functionality, PostgreSQL 16 offers enhanced capabilities for efficient data management.</p>
  <p>Version 16 introduces optimizations for improved query execution and planning, resulting in faster performance and better handling of complex queries. Additionally, advanced indexing capabilities and enhanced partitioning functionality contribute to enhanced data organization and query optimization. With these upgrades, PostgreSQL 16 solidifies its position as a reliable and powerful choice for database management.</p>
</div>
<p class="article-source">Source: PostgreSQL Community</p>
'''


class NewsFormTests(LiveServerTestCase):

    fixtures = ['pgweb/fixtures/users.json',
                'pgweb/fixtures/org_types.json', 'pgweb/fixtures/organisations.json', 'pgweb/fixtures/news_article.json']

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
        cls.title = "News XYZ"

        # Call SQL for simulating local varnish cache
        varnish_cache()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.selenium.quit()
        return super().tearDownClass()

    def test_submit_news_article(self):

        self.selenium.get(self.live_server_url + "/")
        usr = create_permitted_user_with_org_email()
        ck = generate_session_cookie(usr)
        self.selenium.add_cookie(ck)

        self.selenium.get(self.live_server_url + "/account/news/new/")

        # Add data to fields
        self.selenium.find_element(
            By.ID, self.prefix + "org").find_elements(By.TAG_NAME, "option")[1].click()
        self.selenium.find_element(
            By.ID, self.prefix + "email").find_elements(By.TAG_NAME, "option")[1].click()
        self.selenium.find_element(
            By.ID, self.prefix + "title").send_keys(self.title)
        self.selenium.find_element(
            By.ID, self.prefix + "content").send_keys(markup_content)
        # select news tags
        self.selenium.find_element(By.ID, self.prefix + "tags_1").click()

        # click save draft
        st = self.selenium.find_element(
            By.XPATH, "/html/body/div[2]/div/div[2]/div/form/button")
        st.click()
        alerts = self.selenium.find_elements(By.CLASS_NAME, "alert")
        self.assertNotEqual(self.selenium.current_url,
                            self.live_server_url + "/account/news/new/")
        # Submit news article for moderation
        self.selenium.find_element(
            By.XPATH, "/html/body/div[2]/div/div[2]/div/ul/li/a[2]").click()

        # Check for redirection
        self.assertTrue(self.selenium.current_url.__contains__('submit'))

        # confirm button and submit
        self.selenium.find_element(By.ID, self.prefix + "confirm").click()

        # submit moderation
        m = self.selenium.find_element(
            By.XPATH, "/html/body/div[2]/div/div[2]/div/form/button")
        m.click()

        # check if submitted successfully
        self.assertEqual(self.selenium.current_url,
                         self.live_server_url + "/account/edit/news/")

        # Check Database
        articles = NewsArticle.objects.all()
        self.assertNotEqual(len(articles), 1)

    def test_article_delete_draft(self):
        self.selenium.get(self.live_server_url + '/')
        usr = create_permitted_user_with_org_email()
        ck = generate_session_cookie(usr)
        self.selenium.add_cookie(ck)

        self.selenium.get(self.live_server_url + "/account/news/new/")

        # Add data to fields
        self.selenium.find_element(
            By.ID, self.prefix + "org").find_elements(By.TAG_NAME, "option")[1].click()
        self.selenium.find_element(
            By.ID, self.prefix + "email").find_elements(By.TAG_NAME, "option")[1].click()
        self.selenium.find_element(
            By.ID, self.prefix + "title").send_keys(self.title)
        self.selenium.find_element(
            By.ID, self.prefix + "content").send_keys(markup_content)
        # select news tags
        self.selenium.find_element(By.ID, self.prefix + "tags_1").click()

        # click save draft
        st = self.selenium.find_element(
            By.XPATH, "/html/body/div[2]/div/div[2]/div/form/button")
        st.click()
        alerts = self.selenium.find_elements(By.CLASS_NAME, "alert")
        self.assertNotEqual(self.selenium.current_url,
                            self.live_server_url + "/account/news/new/")
        # Submit news article for moderation
        self.selenium.find_element(
            By.XPATH, "/html/body/div[2]/div/div[2]/div/ul/li/a[2]").click()

        # Check for redirection
        self.assertTrue(self.selenium.current_url.__contains__('submit'))

        # confirm button and submit
        self.selenium.find_element(By.ID, self.prefix + "confirm").click()

        # submit moderation
        m = self.selenium.find_element(
            By.XPATH, "/html/body/div[2]/div/div[2]/div/form/button")
        m.click()

        # check if submitted successfully
        self.assertEqual(self.selenium.current_url,
                         self.live_server_url + "/account/edit/news/")

        # Check Database For article creation
        articles = NewsArticle.objects.all()
        self.assertNotEqual(len(articles), 1)

    def test_news_article_render(self):
        self.selenium.get(self.live_server_url + "/about/newsarchive/")
        content = self.selenium.find_element(By.ID, "pgContentWrap")
        links = content.find_elements(By.TAG_NAME, "a")

        for link in links:
            if link.text.__contains__("test news"):
                self.assertEqual(link.text, "testnews")
                self.assertEqual(requests.get(
                    self.live_server_url + link.get_attribute('href')).status_code, 200)
                break
