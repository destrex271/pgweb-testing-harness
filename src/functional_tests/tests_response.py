from django.test.testcases import TestCase
from django.test import Client
from pgweb import urls

# These tests check whether or not all the primary views of the website are up or not


def check_response(res, url):
    x = res.status_code == 200
    # TODO Add url
    return x


class ResponseTest(TestCase):

    def setUp(self) -> None:
        self.client = Client()

    def test_home_response(self):
        url = "/"
        res = self.client.get(url)
        self.assertTrue(check_response(res, url))

    def test_about_response(self):
        url = "/about/"
        res = self.client.get(url)
        self.assertTrue(check_response(res, url))

    def test_download_response(self):
        url = "/download/"
        res = self.client.get(url)
        self.assertTrue(check_response(res, url))

    def test_docs_response(self):
        url = '/docs/'
        res = self.client.get(url)
        self.assertTrue(check_response(res, url))

    def test_community_response(self):
        url = "/community/"
        res = self.client.get(url)
        self.assertTrue(check_response(res, url))

    def test_developers_response(self):
        url = "/developer/"
        res = self.client.get(url)
        self.assertTrue(check_response(res, url))

    def test_support_response(self):
        url = "/support/"
        res = self.client.get(url)
        self.assertTrue(check_response(res, url))

    def test_donate_response(self):
        url = "/about/donate/"
        res = self.client.get(url)
        self.assertTrue(check_response(res, url))
