from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver

from django.test.testcases import call_command, connections
from django.contrib.staticfiles.testing import LiveServerTestCase
import random

from .extra_utils.util_functions import create_permitted_user_with_org_email, generate_session_cookie, varnish_cache


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
