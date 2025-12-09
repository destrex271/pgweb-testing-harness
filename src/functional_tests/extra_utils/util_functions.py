from datetime import datetime
from django.db import connections
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import (
    SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY,
    get_user_model
)
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth.models import Permission, User
from django.test.testcases import call_command
# Additional Libraries
import hashlib
import os
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

# pgweb codebase models; ignore the errors
from pgweb.core.models import Organisation, OrganisationType, OrganisationEmail
from pgweb.events.models import Event
from pgweb.news.models import NewsTag


def create_firefox_driver():
    """
    Create a Firefox WebDriver instance configured for container environments.
    This function sets up proper Firefox options and preferences to avoid
    issues in containerized environments like Debian 11.
    
    The DISPLAY environment variable is set to ':99' if not already set,
    which is the default display used by xvfb-run in the CI environment.
    """
    # Ensure DISPLAY is set for xvfb (default :99 used by xvfb-run)
    if 'DISPLAY' not in os.environ:
        os.environ['DISPLAY'] = ':99'
    
    options = webdriver.FirefoxOptions()
    options.headless = True
    
    # Firefox-specific preferences for container environments
    # Disable caching to avoid /dev/shm issues in containers
    options.set_preference("browser.cache.disk.enable", False)
    options.set_preference("browser.cache.memory.enable", False)
    options.set_preference("browser.cache.offline.enable", False)
    options.set_preference("network.http.use-cache", False)
    
    # Create service with geckodriver
    # Log to /dev/null unless GECKODRIVER_LOG env var is set for debugging
    log_path = os.environ.get('GECKODRIVER_LOG', os.devnull)
    serv = Service(
        executable_path=GeckoDriverManager().install(),
        log_path=log_path
    )
    
    # Create and return the WebDriver instance
    driver = webdriver.Firefox(service=serv, options=options)
    return driver


def varnish_cache():
    # Mannually running varnish cache sim code
    cursor = connections["default"].cursor()
    cursor.execute('''
        BEGIN;

        --
        -- "cheating" version of the varnish_purge() function
        -- that can be used on a local installation that doesn't
        -- have any frontends.
        --

        CREATE OR REPLACE FUNCTION varnish_purge(url text)
        RETURNS void
        AS $$
        $$ LANGUAGE 'sql';

        CREATE OR REPLACE FUNCTION varnish_purge_expr(expr text)
        RETURNS void
        AS $$
        $$ LANGUAGE 'sql';

        CREATE OR REPLACE FUNCTION varnish_purge_xkey(key text)
        RETURNS void
        AS $$
        $$ LANGUAGE 'sql';

        COMMIT;''')
    cursor.close()


def create_unauth_user():

    usr = User.objects.filter(username="testuser1234").first()
    if usr is None:
        usr = User.objects.create_user(username="testr1234", email="testr1234@gmail.com",
                                       password="testuser1234trypasswd")
    return usr


def create_permitted_user_with_org_email():
    user = get_user_model()
    content_type = ContentType.objects.get_for_model(Event)
    post_permission = Permission.objects.filter(content_type=content_type)

    usr = user.objects.filter(email="testusr1@gmail.com").first()
    if usr is None:
        usr = user.objects.create_user(username="testuser12", email="testusr1@gmail.com",
                                       password="testuser12@trypasswd")

        # adding necessary permissions to user
        for perm in post_permission:
            usr.user_permissions.add(perm)

    # Create Organisation for User with user as the manager
    org = Organisation.objects.filter(name="Dummy Org").first()
    if org is None:
        org = Organisation(
            approved=True,
            name="Dummy Org",
            address="Dummy Org addr",
            url="https://www.shiksha-sopan.org",
            orgtype=OrganisationType.objects.get(id=1),
            mailtemplate="default",
            lastconfirmed="2023-06-13T10:33:32.959",
        )
        org.save()
        org.managers.set([usr])
    else:
        org.managers.set([usr])

    # Add organisation email
    org_email = OrganisationEmail.objects.filter(org=org).first()
    if org_email is None:
        org_email = OrganisationEmail(
            org=org,
            address="test_org@gmail.com",
            confirmed=True,
            token=str(hashlib.sha256(b"test_org@gmail.com"))[:100],
            added=datetime.now()
        )
        org_email.save()

    # Add tag for org
    news_tag = NewsTag.objects.create(
        urlname="urlname",
        name="tag1",
        description="Tag description",
    )
    news_tag.allowed_orgs.set([org])
    news_tag.save()
    # print(org, " Organisations:", news_tag.allowed_orgs[0])
    return usr


def create_permitted_user():
    user = get_user_model()
    content_type = ContentType.objects.get_for_model(Event)
    post_permission = Permission.objects.filter(content_type=content_type)

    usr = user.objects.filter(email="testusr1@gmail.com").first()
    if usr is None:
        usr = user.objects.create_user(username="testuser12", email="testusr1@gmail.com",
                                       password="testuser12@trypasswd")

        # adding necessary permissions to user
        for perm in post_permission:
            usr.user_permissions.add(perm)

    # Create Organisation for User with user as the manager
    org = Organisation.objects.filter(name="Dummy Org").first()
    if org is None:
        org = Organisation(
            approved=True,
            name="Dummy Org",
            address="Dummy Org addr",
            url="https://www.shiksha-sopan.org",
            orgtype=OrganisationType.objects.get(id=1),
            mailtemplate="default",
            lastconfirmed="2023-06-13T10:33:32.959",
        )
        org.save()
        org.managers.set([usr])
    else:
        org.managers.set([usr])

    return usr


def generate_session_cookie(usr):

    # Create Session
    session = SessionStore()
    session[SESSION_KEY] = usr.pk
    session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
    session[HASH_SESSION_KEY] = usr.get_session_auth_hash()
    session.save()

    # Generate Cookie
    cookie = {
        'name': settings.SESSION_COOKIE_NAME,
        'value': session.session_key,
        'secure': False,
        'path': '/',
    }

    return cookie



def fixture_teardown(self):
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