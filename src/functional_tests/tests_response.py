from django.test.testcases import TestCase 
from django.test import Client
# These tests check whether or not all the primary views of the website are up or not
from pgweb import urls

def check_response(res):
    return res.status_code == 200

class ResponseTest(TestCase):

    def setUp(self) -> None:
        self.client = Client()
        # print(urls.urlpatterns)

    def test_home_response(self):
        res = self.client.get("/")
        self.assertTrue(check_response(res))

    def test_about_response(self):
        res = self.client.get("/about/")
        
        self.assertTrue(check_response(res))

    def test_download_response(self):
        res = self.client.get("/download/")
        self.assertTrue(check_response(res))

    def test_docs_response(self):
        res = self.client.get("/docs/")
        self.assertTrue(check_response(res))

    def test_community_response(self):
        res = self.client.get("/community/")
        self.assertTrue(check_response(res))

    def test_developers_response(self):
        res = self.client.get("/developer/")
        self.assertTrue(check_response(res))

    def test_support_response(self):
        res = self.client.get("/support/")
        self.assertTrue(check_response(res))

    def test_donate_response(self):
        res = self.client.get("/about/donate/")
        self.assertTrue(check_response(res))
