REPO_OWNER="destrex271"
REPO_NAME="pgweb-testing-harness"
WORKFLOW_NAME="run_functional_tests.yml"
GITHUB_TOKEN="$SECRET_KEY"

# Trigger the workflow using the GitHub REST API with authentication
curl -X POST \
    -H "Accept: application/vnd.github.v3+json" \
    -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/actions/workflows/$WORKFLOW_NAME/dispatches" \
    -d '{"ref":"main"}'
