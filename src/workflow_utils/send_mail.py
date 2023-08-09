import smtplib, ssl
import os

port = 465
smtp_server = "smtp.gmail.com"
USERNAME = os.environ.get('USERNAME')
PASSWORD = os.environ.get('PASSWORD')


message = '''
Subject : Pgweb test report
Please visit the actions page for more info on the latest run.
'''


context = ssl.create_default_context()
with smtplib.SMTP_SSL(smtp_server, port, context) as server:
    server.login(USERNAME, PASSWORD)
    server.sendmail(USERNAME, 'akshatdev2711@gmail.com', message)

