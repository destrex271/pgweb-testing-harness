from os.path import basename
import smtplib, ssl
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import json

port = 465
smtp_server = "smtp.gmail.com"

us_dict = {}

with open('./src/workflow_utils/recp.json', 'r') as f:
    us_dict = json.load(f)

print(us_dict)

USERNAME = os.environ.get('USERNAME')
PASSWORD = os.environ.get('PASSWORD')
files = ['./src/failed_tests.log', './src/final_report.log']
# files = ['commit_id.txt']
message = '''
Please visit the actions page for more info on the latest run.
'''

msg = MIMEMultipart()
msg['From'] = USERNAME
msg['To'] = us_dict['to']
msg['Date'] = formatdate(localtime=True)
msg['Subject'] = 'Testing Harness Reports for latest commit'
msg.attach(MIMEText(message))

for file in files:
    with open(file, "rb") as f:
        part = MIMEApplication(f.read(), _subtype="log")
        part.add_header('content-disposition', f'attachment; filename={file}')
        msg.attach(part)

context = ssl.create_default_context()
with smtplib.SMTP_SSL(smtp_server, port) as server:
    server.login(USERNAME, PASSWORD)
    server.sendmail(USERNAME, 'akshatdev2711@gmail.com', msg)
