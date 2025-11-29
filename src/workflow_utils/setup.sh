
function handle_build_fail(){
    echo "Build Failed!"
    exec > ../../failed_tests.log 2>&1
    echo "Errors reported"
    exit 1
}

#
# Settings for settings_local.py
conf='DEBUG=True\nSITE_ROOT="http://localhost:8000"\nSESSION_COOKIE_SECURE=False\nSESSION_COOKIE_DOMAIN=None\nCSRF_COOKIE_SECURE=False\nCSRF_COOKIE_DOMAIN=None\nALLOWED_HOSTS=["*"]\nSTATIC_ROOT = "/var/www/example.com/static/"'
database="DATABASES = {\n\t'default': {\n\t\t'ENGINE': 'django.db.backends.postgresql',\n\t\t'NAME': 'db',\n\t\t'PORT': 5432,\n\t\t'PASSWORD': 'postgres',\n\t\t'HOST' : 'localhost',\n\t\t'USER': 'postgres'\n\t}\n}"
# database = "DATABASES={\n\t'default' : {\n\t\t'ENGINE': 'django.db.backends.sqlite3','NAME':'db'}}"

# ------------------------------

# Build System dependencies
sudo apt update && sudo apt install git -y 
# sudo apt-get install -y postgresql-client python3-dev python3-pip firefox libnss3 libtidy-dev
sudo apt-get install -y libyaml-dev build-essential
sudo apt-get install -y \
    postgresql-client \
    firefox \
    libnss3 \
    libtidy-dev
# sudo apt-get install python-yaml

# Clone PGWeb repository
git clone https://git.postgresql.org/git/pgweb.git
cd pgweb
echo "Cloned Repo"

# Install chrome
# wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
# sudo apt install -y ./google-chrome-stable_current_amd64.deb
# sudo apt install -y chromium-browser

pg_isready --host=localhost
which psql

# Install lighthouse
# npm i -g lighthouse
# npm i -g yarn
# yarn global add @unlighthouse/cli puppeteer

# Python dependencies
echo "Installing pgweb dependencies...."
sed -i '/psycopg2/d' requirements.txt
# sed -i '/PyYAML/d' requirements.txt
sed -i '/pycryptodomex/d' requirements.txt
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -r requirements.txt
harness_pip_stat=$?
echo $harness_pip_stat
if [ $harness_pip_stat != 0 ]; then
    echo "Harness failed in installing dependencies"
    handle_build_fail
fi
echo "Dependencies Installed for  pgweb!"


# Remove psycopg2 to avoid conflicts
python3 -m pip install -r ../../../requirements.txt
pgweb_pip_stat=$?
if [ $pgweb_pip_stat != 0 ]; then
    echo "Harness unable to install pgweb dependencies"
    handle_build_fail
fi

echo "installed"

# Create Database & add procedures
PGPASSWORD=postgres psql -h localhost -U postgres -c "CREATE DATABASE db;"
PGPASSWORD=postgres psql -h localhost -U postgres -d db -f sql/varnish_local.sql

# Add Local Settings
touch pgweb/settings_local.py
echo -e $conf >>pgweb/settings_local.py
echo -e $database >>pgweb/settings_local.py
cat pgweb/settings_local.py


for entry in ../../functional_tests/*; do
    echo "$entry"
    cp -r "$entry" pgweb/
done

cp -r ../../utils pgweb/

# Run all the tests
export DJANGO_SETTINGS_MODULE=pgweb.settings
ls
# Migrations
python3 manage.py makemigrations
make_migrate_stat=$?

if [ $make_migrate_stat != 0 ]; then
    echo "\n\nError in Making migrations"
    handle_build_fail
fi

python3 manage.py migrate
migrate_stat=$?
if [ $make_migrate_stat != 0 ]; then
    echo "\n\nError in Making migrations"
    handle_build_fail
fi

# Load version fixtures
PGPASSWORD=postgres psql -h localhost -U postgres -a -f sql/varnish_local.sql
# Scripts to load initial data
# sudo chmod +x pgweb/load_initial_data.sh
# yes | ./pgweb/load_initial_data.sh
# echo "Loaded data"

# yes | ./pgweb/load_initial_data.sh
# ./manage.py test --pattern="tests_*.py" --keepdb --verbosity=2 2>&1 | tee -a ../../final_report.log
# ./manage.py test --pattern="tests_re*.py" --keepdb --verbosity=2 2>&1 | tee -a ../../final_report.log
python3 manage.py test --pattern="tests_*.py" --keepdb --verbosity=2 2>&1 | tee -a ../../final_report.log

python3 ../../utils/process_logs.py
cat ../../final_report.log
cat ../../failed_tests.log

PGPASSWORD=postgres psql -h localhost -U postgres -c "DROP DATABASE db;"
