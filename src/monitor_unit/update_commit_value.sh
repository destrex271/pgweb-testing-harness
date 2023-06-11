git clone git://git.postgresql.org/git/pgweb.git
cd pgweb

# Get last commit id
git rev-parse HEAD >"commit_id.txt"
cat commit_id.txt
cd ..
rm -rf pgweb

# Push to repository
git add .
git config --global user.name "destrex271"
git config --global user.email "destrex271@gmail.com"

git add .
git commit -m "GH Action; Updated commit id"
