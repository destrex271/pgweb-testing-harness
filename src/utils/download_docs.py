import os
from datetime import datetime
from os.path import isfile
from bs4 import BeautifulSoup
from django.utils.timezone import now
import requests
import wget
import json
import subprocess
import psycopg2

# ------------------------------


def prepare_json_template(id_, version, latest, cur: bool):

    return {
        "model": "core.version",
        "pk": id_,
        "fields": {
            "tree": str(version),
            "latestminor": latest,
            "reldate": "2023-07-04",
            "current": cur,
            "supported": True,
            "testing": 0,
            "docsloaded": "2023-07-04T07:36:48",
            "docsgit": "",
            "firstreldate": "2023-07-04",
            "eoldate": "2023-07-04"
        }
    }

# ------------------------------


connection = psycopg2.connect(
    dbname="pgmsdb", user="postgres", password="postgres", host="localhost")

curs = connection.cursor()

# Delete rows from the "docs" table
curs.execute(
    "DELETE FROM docs WHERE version IN (SELECT id FROM core_version)")

# Delete rows from the "core_version" table
curs.execute("DELETE FROM core_version")


url = "https://www.postgresql.org/ftp/source/"
download_url = "https://ftp.postgresql.org/pub/source/"

req = requests.get(url)
soup = BeautifulSoup(req.content, 'html.parser')

links = soup.find_all('a')


# prepare link map
download_map = {}
verk = []
i = 0
for link in links:
    print(i, link.text)
    if '.' in link.text:
        vc = link.text.split('.')[0]
        # print(link.text.split('.'))
        if link.text[0] == 'v' and vc not in verk and int(vc[1:]) > 12:
            download_map[link.text[1:]] = download_url + \
                link.text + "/postgresql-" + link.text[1:] + ".tar.gz"
            vers = link.text.split('.')[0]
            # print(vers)
            verk.append(vers)

    elif 'beta' in link.text:
        vc = link.text.split('beta')[0]
        # print(vc)
        if link.text[0] == 'v' and vc not in verk and int(vc[1:]) > 12:
            download_map[link.text[1:]] = download_url + \
                link.text + "/postgresql-" + link.text[1:] + ".tar.gz"
            vers = link.text.split('beta')[0]
            verk.append(vers)

print(download_map)


# Populate database with versions
i = 1
v = True
fixture = []
completed = []

for version, download_link in download_map.items():
    obj = {}
    if '.' in version:
        if str(version).count('.') == 1:
            vers = version.split('.')
            print("vers", vers)
            obj = prepare_json_template(
                i, vers[0], vers[1], v)
        else:
            x = version.split('.')
            print(x[0])
            print()
            latm = str(x[1]) + "." + str(x[2])
            obj = prepare_json_template(
                i, version.split('.')[0], latm, v)
        v = False

    elif 'beta' in version:
        vers = version.split('beta')[0]
        obj = prepare_json_template(i, version.split(
            'beta')[0], version.split('beta')[1], v)
    if not len(obj) == 0:
        fixture.append(obj)
        i += 1

print(fixture)


# Save JSON to a file
with open('versions.json', 'w+') as file:
    json.dump(fixture, file)
    file.close()


# download all documentation files
for key in download_map:
    print('Downloading v' + key + " ....... " + download_map[key])
    wget.download(download_map[key])
    print("Downloaded")


subprocess.Popen(['python', 'manage.py', 'loaddata', 'versions.json'])
# subprocess.run('./manage.py loaddata ../versions.json')

subprocess.Popen(['ls'])

for version, _ in download_map.items():
    versk = version.replace('beta', '.')
    vers = versk.split('.')

    print("Loading.. "+"postgresql-" + str(version) + ".tar.gz")
    subprocess.Popen(['python', 'docload.py', vers[0],
                     "postgresql-" + str(version) + ".tar.gz"])
