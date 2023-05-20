git clone https://github.com/destrex271/pgweb-testing-harness
git clone git://git.postgresql.org/git/pgweb.git
cd pgweb
sudo apt update # && sudo apt -y upgrade &&
sudo apt -y install python3 python3-pip
pip install -r requirements.txt # Setting up the postgresql website requirements
python manage.py shell <../pgweb-testing-harness/src/functional_tests/test.py
