from datetime import datetime
import os
from bs4 import BeautifulSoup
from django.utils.timezone import now
import requests
import wget
import json
import subprocess
import psycopg2
from django.core.management import call_command 
# from .core.models import Version

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
            "eoldate": "3000-07-04"
        }
    }


def setup_documentation():

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
        if '.' in link.text:
            vc = link.text.split('.')[0]
            if link.text[0] == 'v' and vc not in verk and int(vc[1:]) > 10:
                download_map[link.text[1:]] = download_url + \
                    link.text + "/postgresql-" + link.text[1:] + ".tar.gz"
                vers = link.text.split('.')[0]
                verk.append(vers)

        elif 'beta' in link.text:
            vc = link.text.split('beta')[0]
            if link.text[0] == 'v' and vc not in verk and int(vc[1:]) > 12:
                download_map[link.text[1:]] = download_url + \
                    link.text + "/postgresql-" + link.text[1:] + ".tar.gz"
                vers = link.text.split('beta')[0]
                verk.append(vers)



    i = 1
    v = True
    fixture = []

    for version, _ in download_map.items():
        obj = {}
        if '.' in version:
            if str(version).count('.') == 1:
                vers = version.split('.')
                obj = prepare_json_template(
                    i, vers[0], vers[1], v)
            else:
                x = version.split('.')
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

    # print(fixture)

    # Save JSON to a file
    with open('versions.json', 'w+') as file:
        json.dump(fixture, file)
        file.close()

    call_command('loaddata', 'versions.json')

    # download all documentation files
    for key in download_map:
        wget.download(download_map[key])
    
    for version, _ in download_map.items():
        versk = version.replace('beta', '.')
        vers = versk.split('.')
    
        # print("Loading.. "+"postgresql-" + str(version) + ".tar.gz")
        subprocess.run(['python', './pgweb/utils/docload.py', vers[0],
                                 "postgresql-" + str(version) + ".tar.gz"])
        # p.wait()

    return download_map

# if __name__ == "__main__":
#     setup_documentation()
