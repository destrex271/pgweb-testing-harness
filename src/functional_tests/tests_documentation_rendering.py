from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver

from django.test.testcases import call_command, connections
from django.contrib.staticfiles.testing import LiveServerTestCase

from .extra_utils.util_functions import varnish_cache
from .utils.download_docs import setup_documentation
from .utils.docload import install_docs

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
        download_map = setup_documentation()
        cls.vers_list = []
        for version, _ in download_map.items():
            cls.vers_list.append(version)
        i = 0
        print(Version.objects.all())
        for obj in Version.objects.all():
            k = cls.vers_list[i]
            install_docs(int(obj.tree), "postgresql-" + k + ".tar.gz", Version)
            i += 1

    @classmethod
    def tearDownClass(cls) -> None:
        cls.selenium.quit()
        super().tearDownClass()

    def test_render_all_versions_as_links(self):
        self.selenium.get(self.live_server_url + "/docs/")
        links = self.selenium.find_element(
            By.ID, 'pgContentWrap').find_elements(By.TAG_NAME, 'a')
        link_list = []
        for link in links:
            link_list.append(link.text[1:])

        print(link_list)
