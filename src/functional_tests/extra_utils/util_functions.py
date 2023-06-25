from django.db import connections
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import (
    SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY,
    get_user_model
)
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth.models import Permission, User

# pgweb codebase models; ignore the errors
from pgweb.core.models import Organisation, OrganisationType
from pgweb.events.models import Event


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
