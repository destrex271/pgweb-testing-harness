# Settings for settings_local.py
conf='DEBUG=True\nSITE_ROOT="http://localhost:8000"\nSESSION_COOKIE_SECURE=False\nSESSION_COOKIE_DOMAIN=None\nCSRF_COOKIE_SECURE=False\nCSRF_COOKIE_DOMAIN=None\nALLOWED_HOSTS=["*"]\nSTATIC_ROOT = "/var/www/example.com/static/"'
database="DATABASES = {\n\t'default': {\n\t\t'ENGINE': 'django.db.backends.postgresql',\n\t\t'NAME': 'pmgs',\n\t\t'PORT': 5432,\n\t\t'PASSWORD': 'postgres',\n\t\t'HOST' : 'localhost',\n\t\t'USER': 'postgres'\n\t}\n}"
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

# Create Database
PGPASSWORD=postgres psql -h localhost -U postgres -c "CREATE DATABASE pmgs;"

# Add Local Settings
touch pgweb/settings_local.py
echo -e $conf >>pgweb/settings_local.py
echo -e $database >>pgweb/settings_local.py
cat pgweb/settings_local.py

# Migrations
./manage.py makemigrations
./manage.py migrate

# Test scripts
# psql -d pgweb -f sql/varnish_local.sql

functional_tests = ../../functional_tests

for entry in ../../functional_tests/*; do
	echo "$entry"
	cp -r "$entry" pgweb/
done

cp -r ../../utils pgweb/

ls pgweb

# Run all the tests
export DJANGO_SETTINGS_MODULE=pgweb.settings
python manage.py test --pattern="tests_*.py" --keepdb
cat *.txt
