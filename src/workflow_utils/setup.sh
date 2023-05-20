git clone https://github.com/destrex271/pgweb-testing-harness
git clone git://git.postgresql.org/git/pgweb.git
cd pgweb
pip install -r requirements.txt # Setting up the postgresql website requirements
python manage.py shell <../pgweb_testing_harness/src/functional_tests/tests.py
