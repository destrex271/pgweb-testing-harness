function trigger() {
	REPO_OWNER="destrex271"
	REPO_NAME="pgweb-testing-harness"
	WORKFLOW_NAME="run_tests.yml"
	GITHUB_TOKEN="$SECRET_KEY"

	# Trigger the workflow using the GitHub REST API with authentication
	curl -X POST \
		-H "Accept: application/vnd.github.v3+json" \
		-H "Authorization: token $GITHUB_TOKEN" \
		"https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/actions/workflows/$WORKFLOW_NAME/dispatches" \
		-d '{"ref":"main"}'
}

apt update -y && apt upgrade -y
apt install -y git curl
git clone git://git.postgresql.org/git/pgweb.git

ls
strp=$(cat commit_id.txt)
cd pgweb
echo "$strp"
echo "$(git rev-parse HEAD)"
if [ "$strp" != "$(git rev-parse HEAD)" ]; then
	echo "Triggering Action"
	trigger
fi

cd ..
rm -rf pgweb
