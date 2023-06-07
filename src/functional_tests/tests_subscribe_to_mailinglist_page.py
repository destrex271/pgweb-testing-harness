from django.contrib.staticfiles.testing import LiveServerTestCase
from django.test.testcases import call_command, connections
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver
