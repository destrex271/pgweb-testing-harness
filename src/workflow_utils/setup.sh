# Settings for settings_local.py
conf='DEBUG=True\nSITE_ROOT="http://localhost:8000"\nSESSION_COOKIE_SECURE=False\nSESSION_COOKIE_DOMAIN=None\nCSRF_COOKIE_SECURE=False\nCSRF_COOKIE_DOMAIN=None\nALLOWED_HOSTS=["*"]\nSTATIC_ROOT = "/var/www/example.com/static/"'
database="DATABASES = {\n\t'default': {\n\t\t'ENGINE': 'django.db.backends.postgresql',\n\t\t'NAME': 'pgmsdb',\n\t\t'PORT': 5432,\n\t\t'PASSWORD': 'postgres',\n\t\t'HOST' : 'localhost',\n\t\t'USER': 'postgres'\n\t}\n}"
# database = "DATABASES={\n\t'default' : {\n\t\t'ENGINE': 'django.db.backends.sqlite3','NAME':'db'}}"

# ------------------------------

# Clone PGWeb repository
git clone git://git.postgresql.org/git/pgweb.git
cd pgweb

# Build System dependencies
sudo apt update && sudo apt-get install -y postgresql-client python3-pip firefox libnss3

pg_isready --host=localhost

# Python dependencies
pip install -r requirements.txt
pip install -r ../../../requirements.txt

# Create Database & add procedures
PGPASSWORD=postgres psql -h localhost -U postgres -c "CREATE DATABASE pgmsdb;"
PGPASSWORD=postgres psql -h localhost -U postgres -d pgmsdb -f sql/varnish_local.sql

# Add Local Settings
touch pgweb/settings_local.py
echo -e $conf >>pgweb/settings_local.py
echo -e $database >>pgweb/settings_local.py
cat pgweb/settings_local.py

# Scripts to load initial data
sudo chmod +x pgweb/load_initial_data.sh
yes | pgweb/load_initial_data.sh

for entry in ../../functional_tests/*; do
    echo "$entry"
    cp -r "$entry" pgweb/
done

cp -r ../../utils pgweb/

ls pgweb

# Run all the tests
export DJANGO_SETTINGS_MODULE=pgweb.settings
# coverage run --source='.' manage.py test --pattern="tests_*.py" --keepdb

# Migrations
./manage.py makemigrations
./manage.py migrate

# coverage run --source='.' manage.py test --pattern="tests_ev*.py" --keepdb
# cat "\t\t\t\tFINAL REPORT" >final_report.txt
# ./manage.py test --pattern="tests_*.py" --keepdb --verbosity=2 2>&1 | tee -a final_report.log
./manage.py test --pattern="tests_products_*.py" --keepdb --verbosity=2 2>&1 | tee -a final_report.log

# echo -e "Final Report"
# cat final_report.txt

PGPASSWORD=postgres psql -h localhost -U postgres -c "DROP DATABASE pgmsdb;"
