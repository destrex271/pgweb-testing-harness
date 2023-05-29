# Settings for settings_local.py
conf='DEBUG=True\nSITE_ROOT="http://localhost:8000"\nSESSION_COOKIE_SECURE=False\nSESSION_COOKIE_DOMAIN=None\nCSRF_COOKIE_SECURE=False\nCSRF_COOKIE_DOMAIN=None\nALLOWED_HOSTS=["*"]'
database="DATABASES = {\n\t'default': {\n\t\t'ENGINE': 'django.db.backends.postgresql_psycopg2',\n\t\t'NAME': 'pgweb',\n\t\t'PORT': 5432,\n\t\t'PASSWORD': 'postgres',\n\t\t'HOST' : 'localhost',\n\t\t'USER': 'postgres'\n\t}\n}"

# ------------------------------

# Clone PGWeb repository
git clone https://github.com/destrex271/pgweb-testing-harness
git clone git://git.postgresql.org/git/pgweb.git
cd pgweb

# Build System dependencies
sudo apt purge google-chrome-stable
sudo apt purge chromium-browser
sudo apt update && sudo apt-get install -y postgresql-client python3-pip chromium-browser firefox libnss3

# Google Chrome Stable Installation
# wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
# sudo dpkg -i google-chrome-stable_current_amd64.deb
# rm ~/.config/google-chrome/Default/.org.chromium.Chromium.*

# Python dependencies
pip install -r requirements.txt
pip install -r ../pgweb-testing-harness/requirements.txt

# Create Database
psql -h localhost -U postgres -c "CREATE DATABASE pgweb;"

# Add Local Settings
touch pgweb/settings_local.py
echo -e $conf >>pgweb/settings_local.py
echo -e $database >>pgweb/settings_local.py
cat pgweb/settings_local.py

# ps auxw | grep postgres
# lsof -p 4836 | grep unix

# Migrations
./manage.py migrate

# Test scripts
# psql -d pgweb -f sql/varnish_local.sql

# Load dummy data
# pgweb/load_initial_data.sh

# functional_tests = ../pgweb-testing-harness/src/functional_tests

for entry in ../pgweb-testing-harness/src/functional_tests/*; do
	echo "$entry"
	cp "$entry" pgweb/
	ls pgweb
done

# Run all the tests
python manage.py test --pattern="tests_*.py"
# Version
firefox --version
