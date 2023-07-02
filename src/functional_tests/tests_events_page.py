import random
from django.contrib.auth.models import Permission, User
from django.contrib.staticfiles.testing import LiveServerTestCase
from django.test.testcases import call_command, connections
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver

# pgweb codebase models; ignore the errors
from .core.models import Organisation, OrganisationType
from .events.models import Event

# Util functions
from .extra_utils.util_functions import create_unauth_user, create_permitted_user, generate_session_cookie, varnish_cache


markup_content = '''
Awesome Series @ Write Kit

[Markdown (Syntax & Extensions, Documentation & Cheat Sheets, Libraries, ...)](https://github.com/writekit/awesome-markdown) •
[Markdown Editors & (Pre)viewers](https://github.com/writekit/awesome-markdown-editors)  •
[Books (Services, Hand-Written, Auto-Built w/ Open Data, ...)](https://github.com/writekit/awesome-books)


# Awesome Markdown Editors & (Pre)viewers

A collection of awesome markdown editors and (pre)viewers
for Linux, Apple OS X, Microsoft Windows, the World Wide Web and more.

---

[ANNOUNCEMENT] Looking for the latest news, tools, tips & tricks, and more
about markdown and friends?
Follow along the Manuscripts News ([@manuscriptsnews](https://twitter.com/manuscriptsnews)) channel on twitter for updates.

---

#### _Contributions welcome. Anything missing? Send in a pull request. Thanks._



_Zen Writing - leaving you alone with your thoughts and your words_


## Markdown Online Editors

**Mark**
(web: [`mark.barelyhuman.dev`](https://mark.barelyhuman.dev),
github: [`barelyhuman/mark`](https://github.com/barelyhuman/mark)) - Simple Web Markdown Editor

**Minimalist Online Markdown Editor**
(web: [`markdown.pioul.fr`](http://markdown.pioul.fr),
 github: [`pioul/Minimalist-Online-Markdown-Editor`](https://github.com/pioul/Minimalist-Online-Markdown-Editor))

**StackEdit**
(web: [`stackedit.io`](https://stackedit.io),
 github: [`benweet/stackedit`](https://github.com/benweet/stackedit))

**Markdown Note**
(web: [`writekit.github.io/markdown.note/note.html`](http://writekit.github.io/markdown.note/note.html),
 github: [`writekit/markdown.note`](https://github.com/writekit/markdown.note)) -
another simple single HTML page, server-less Markdown editor in JavaScript

**Dillinger.io**
(web: [`dillinger.io`](http://dillinger.io/),
 github: [`joemccann/dillinger`](https://github.com/joemccann/dillinger))

**MarkTwo**
 (web: [`marktwo.app`](https://marktwo.app),
  github:[`anthonygarvan/marktwo`](https://github.com/anthonygarvan/marktwo)),
  MarkTwo is a free and open source progressive web app which can be installed on any platform or used within the browser. It features seamless transition between read and edit mode, snappy performance for large documents, and efficient, continuous, and private syncing via your own Google drive. It also has a host of productivity enhancements that make it ideal for long-form notes and journals.

**HackMD**
(web: [`hackmd.io`](http://hackmd.io/),
 github: [`HackMD`](https://github.com/hackmdio)) - Allows collaboration and more UI options. Link to Github is maintained.

 **LetsMarkdown.com**
(web: [`LetsMarkdown.com`](https://letsmarkdown.com/),
github: [`Cveinnt/LetsMarkdown.com`](https://github.com/Cveinnt/LetsMarkdown.com)) - 👨‍💻👩‍💻 Fast, minimal web editor that makes markdown editing collaborative and accessible to everyone.

'''


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


class EventsForm(LiveServerTestCase):

    fixtures = ['pgweb/fixtures/users.json', 'pgweb/fixtures/org_types.json',
                'pgweb/fixtures/organisations.json', 'pgweb/core/fixtures/data.json', 'pgweb/fixtures/lang_fixtures.json', 'pgweb/fixtures/approved_events.json']

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

        cls.start_date = "2023-10-10"
        cls.title = "Demo Event: PGCon 20xx"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.selenium.quit()
        super().tearDownClass()

    def test_add_offline_event(self):
        # Login user by setting session cookie
        self.selenium.get(self.live_server_url + "/")
        ck = generate_session_cookie(create_permitted_user())
        self.selenium.add_cookie(ck)

        # Routing to main page to execute tests
        self.selenium.get(self.live_server_url + "/account/events/new/")
        hd = self.selenium.find_element(By.TAG_NAME, "h1")
        self.assertEqual(hd.text.lower().strip(), "new event")

        # Iterate over Drop Down
        org_dropdown = self.selenium.find_element(By.ID, self.prefix+"org")
        options = org_dropdown.find_elements(By.TAG_NAME, "option")
        options[1].click()
        self.org = options[1].text

        title_feild = self.selenium.find_element(
            By.ID, self.prefix + "title")
        title_feild.send_keys(
            self.title
        )

        city = self.selenium.find_element(By.ID, self.prefix + "city")
        city.send_keys('Dummy City')

        state = self.selenium.find_element(By.ID, self.prefix + "state")
        state.send_keys('Dummy State')

        country = self.selenium.find_element(By.ID, self.prefix + "country")
        ctrs = country.find_elements(By.TAG_NAME, 'option')
        ctrs[random.randint(0, len(ctrs) - 1)].click()

        language = self.selenium.find_element(By.ID, self.prefix + "language")
        lngs = language.find_elements(By.TAG_NAME, 'option')
        lngs[1].click()

        community_event = self.selenium.find_element(
            By.ID, self.prefix + "badged")
        community_event.click()

        start_date = self.selenium.find_element(
            By.ID, self.prefix + "startdate")
        start_date.send_keys(self.start_date)

        end_date = self.selenium.find_element(By.ID, self.prefix + "enddate")
        end_date.send_keys('2023-10-12')

        summary = self.selenium.find_element(By.ID, self.prefix + "summary")
        summary.send_keys('''The PostgreSQL community recently conducted a highly successful event that brought together enthusiasts, developers, and experts from around the world. The event aimed to showcase the latest developments, share knowledge, and foster collaboration within the PostgreSQL ecosystem. The event featured a diverse range of sessions, including technical presentations, panel discussions, workshops, and networking opportunities. Renowned speakers delivered insightful talks on various topics related to PostgreSQL, covering areas such as performance optimization, high availability, data modeling, security, and emerging trends. Attendees had the opportunity to engage in interactive discussions and learn from the experiences of industry leaders and seasoned professionals. The event provided a platform for both beginners and experienced users to exchange ideas, ask questions, and explore innovative use cases.''')

        details = self.selenium.find_element(By.ID, self.prefix + "details")
        details.send_keys(markup_content)

        btn = self.selenium.find_element(By.CLASS_NAME, 'btn-primary')
        btn.click()

        # Check Heading
        msg_hd = self.selenium.find_element(By.TAG_NAME, 'h3')
        self.assertEqual(msg_hd.text.lower().strip(),
                         "waiting for moderator approval")

        # Check if event was appended to unapproved events and shown
        li = self.selenium.find_element(
            By.XPATH, "/html/body/div[2]/div/div[2]/div/ul")
        events = li.find_elements(By.TAG_NAME, "a")
        self.assertEqual(events[0].text.lower().strip(), (str(
            self.start_date) + ": " + str(self.title)).lower().strip())

        # Check Against Database
        events = Event.objects.filter(
            title=self.title, org_id=Organisation.objects.get(name=self.org).id)

        self.assertNotEqual(len(events), 0)

    def test_add_online_event(self):
        # Login user by setting session cookie
        self.selenium.get(self.live_server_url + "/")
        ck = generate_session_cookie(create_permitted_user())
        self.selenium.add_cookie(ck)

        # Routing to main page to execute tests
        self.selenium.get(self.live_server_url + "/account/events/new/")
        hd = self.selenium.find_element(By.TAG_NAME, "h1")
        self.assertEqual(hd.text.lower().strip(), "new event")

        # Iterate over Drop Down
        org_dropdown = self.selenium.find_element(By.ID, self.prefix+"org")
        options = org_dropdown.find_elements(By.TAG_NAME, "option")
        # for op in options:
        options[1].click()
        self.org = options[1].text

        title_feild = self.selenium.find_element(
            By.ID, self.prefix + "title")
        title_feild.send_keys(
            self.title
        )

        online = self.selenium.find_element(By.ID, self.prefix + "isonline")
        online.click()

        language = self.selenium.find_element(By.ID, self.prefix + "language")
        lngs = language.find_elements(By.TAG_NAME, 'option')
        lngs[1].click()

        community_event = self.selenium.find_element(
            By.ID, self.prefix + "badged")
        community_event.click()

        start_date = self.selenium.find_element(
            By.ID, self.prefix + "startdate")
        start_date.send_keys(self.start_date)

        end_date = self.selenium.find_element(By.ID, self.prefix + "enddate")
        end_date.send_keys('2023-10-12')

        summary = self.selenium.find_element(By.ID, self.prefix + "summary")
        summary.send_keys('''The PostgreSQL community recently conducted a highly successful event that brought together enthusiasts, developers, and experts from around the world. The event aimed to showcase the latest developments, share knowledge, and foster collaboration within the PostgreSQL ecosystem. The event featured a diverse range of sessions, including technical presentations, panel discussions, workshops, and networking opportunities. Renowned speakers delivered insightful talks on various topics related to PostgreSQL, covering areas such as performance optimization, high availability, data modeling, security, and emerging trends. Attendees had the opportunity to engage in interactive discussions and learn from the experiences of industry leaders and seasoned professionals. The event provided a platform for both beginners and experienced users to exchange ideas, ask questions, and explore innovative use cases.''')

        details = self.selenium.find_element(By.ID, self.prefix + "details")
        details.send_keys(markup_content)

        btn = self.selenium.find_element(By.CLASS_NAME, 'btn-primary')
        btn.click()

        # Check Heading
        msg_hd = self.selenium.find_element(By.TAG_NAME, 'h3')
        self.assertEqual(msg_hd.text.lower().strip(),
                         "waiting for moderator approval")

        # Check if event was appended to unapproved events and shown
        li = self.selenium.find_element(
            By.XPATH, "/html/body/div[2]/div/div[2]/div/ul")

        events = li.find_elements(By.TAG_NAME, "a")
        self.assertEqual(events[0].text.lower().strip(), (str(
            self.start_date) + ": " + str(self.title)).lower().strip())

        # Check Against Database
        events = Event.objects.filter(
            title=self.title, org_id=Organisation.objects.get(name=self.org).id)

        self.assertNotEqual(len(events), 0)

    def test_render_approved_event(self):
        title = "testnews"
        title2 = "testnews2"
        # Check the events page to see if event has been rendered
        self.selenium.get(self.live_server_url + "/about/events/")
        content = self.selenium.find_element(By.ID, 'pgContentWrap')
        links = content.find_elements(By.TAG_NAME, 'a')
        for link in links:
            # Check if unapproved event is being displayed
            self.assertFalse(link.text.__contains__(title2))
            if link.text.__contains__(title):
                link.click()
                break
        self.assertNotEqual(
            self.selenium.current_url, self.live_server_url + "/about/events/")

        content = self.selenium.find_element(By.ID, 'pgContentWrap')
        self.assertEqual(content.find_element(
            By.TAG_NAME, 'h1').text.lower(), title.lower())

    def test_add_event_by_unauth_user(self):
        # Login user by setting session cookie
        self.selenium.get(self.live_server_url + "/")
        self.selenium.add_cookie(generate_session_cookie(create_unauth_user()))

        # Routing to main page to execute tests
        self.selenium.get(self.live_server_url + "/account/events/new/")
        hd = self.selenium.find_element(By.TAG_NAME, "h1")
        self.assertEqual(hd.text.lower().strip(), "new event")

        # Iterate over Drop Down
        org_dropdown = self.selenium.find_element(By.ID, self.prefix+"org")
        options = org_dropdown.find_elements(By.TAG_NAME, "option")
        self.assertEqual(len(options), 1)
