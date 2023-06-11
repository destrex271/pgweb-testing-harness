REPO_NAME="pgweb-testing-harness"
REPO_OWNER="destrex271"
GITHUB_TOKEN="$SECRET_KEY"

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
git remote set-url origin https://x-access-token:$SECRET_KEY@github.com/$REPO_OWNER/$REPO_NAME
git push -u origin main
