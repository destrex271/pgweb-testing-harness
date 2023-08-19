from os.path import basename
import smtplib, ssl
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json

# Check if files need to be sent
with open('./src/failed_tests.log', 'r') as f:
    if f.read().lower().__contains__('no tests failed'):
        import sys
        print("Tests succeded, no email required!")
        sys.exit(0)

port = 465
smtp_server = "smtp.gmail.com"

us_dict = {}

with open('./src/workflow_utils/recp.json', 'r') as f:
    us_dict = json.load(f)

print(us_dict)

USERNAME = os.environ.get('USERNAME')
PASSWORD = os.environ.get('PASSWORD')
files = ['./src/failed_tests.log', './src/final_report.log']
message = '''
Please visit the actions page for more info on the latest run.
'''
for to_user in us_dict['to']:
    msg = MIMEMultipart()
    msg['From'] = USERNAME
    msg['To'] = to_user
    msg['Subject'] = 'Testing Harness Reports for latest commit'
    msg.attach(MIMEText(message, 'plain'))

    for file in files:
        print(file)
        with open(file, "rb") as f:
            part = MIMEApplication(f.read(), _subtype="log")
            part.add_header('content-disposition', f'attachment; filename={file}')
            msg.attach(part)

    print("sending msg")
    a = msg.as_string()
    with smtplib.SMTP_SSL(smtp_server, port) as server:
        # server.login(USERNAME, PASSWORD)
        server.login(USERNAME, PASSWORD)
        print("Logged in")
        server.sendmail(USERNAME, to_user, msg.as_string())
        print("SENT")
