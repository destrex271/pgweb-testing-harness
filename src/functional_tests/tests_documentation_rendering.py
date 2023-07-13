from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver

from django.test.testcases import call_command, connections
from django.contrib.staticfiles.testing import LiveServerTestCase

from .extra_utils.util_functions import varnish_cache
from .utils.download_docs import setup_documentation
# from .utils.docload import install_docs

# Core Models
from .core.models import Version


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


class DocumentationRenderTests(LiveServerTestCase):

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
        varnish_cache()
        cls.vers_list = []
        download_map = setup_documentation()
        for version, _ in download_map.items():
            cls.vers_list.append(version)
       
    @classmethod
    def tearDownClass(cls) -> None:
        cls.selenium.quit()
        super().tearDownClass()

    def test_rendered_documentation(self):

        self.selenium.get(self.live_server_url + "/docs/")
        links = self.selenium.find_element(
            By.ID, 'pgContentWrap').find_elements(By.TAG_NAME, 'a')
        link_list = []

        for link in links:
            if link.text.isnumeric():
                link_list.append(link.text)

        lvers_list = []
        for a in self.vers_list:
            ver = a
            ver = ver.replace('beta', '.')
            ver = ver.split('.')
            lvers_list.append(ver[0])

        self.assertEqual(lvers_list, link_list)  # Check if all versions are rendered as links

        self.selenium.get(self.live_server_url + "/docs/")
        links = self.selenium.find_element(
            By.ID, 'pgContentWrap').find_elements(By.TAG_NAME, 'a')
    
        link_hrefs = {}
        for link in links:
            if link.text.isnumeric():
                link_hrefs[link.text] = link.get_attribute("href") 

        for version, url in link_hrefs.items():
            print("Testing > ", version)
            self.selenium.get(url)

            # Fetch docContent
            content = self.selenium.find_element(By.ID, "docContent")

            navbar_buttons = content.find_element(By.CLASS_NAME, "navheader").find_elements(By.TAG_NAME, "a")
            nav_btns = []
            for nv_btn in navbar_buttons:
                if nv_btn.text == "Previous" or nv_btn.text == "Next":
                    nav_btns.append(nv_btn)

            text = content.text
            print("Text", text)
            print("Head>", content.find_element(By.TAG_NAME, "h1").text)

            if nav_btns[-1].text == "Next":
                print("Move")
                nav_btns[-1].click()
    
        print(link_hrefs)

