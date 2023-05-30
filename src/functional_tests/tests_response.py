from django.test import Client

c = Client()

response = c.get("/")
print(response, type(response))
