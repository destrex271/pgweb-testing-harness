DIR=pgweb

function trigger_tools() {

    REPO_OWNER="destrex271"
    REPO_NAME="pgweb-testing-harness"
    WORKFLOW_NAME="run_functional_tests.yml"
    GITHUB_TOKEN="${{ secrets.SECRET_KEY }}"

    # Trigger the workflow using the GitHub REST API with authentication
    curl -X POST \
        -H "Accept: application/vnd.github.v3+json" \
        -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/actions/workflows/$WORKFLOW_NAME/dispatches" \
        -d '{"ref":"main"}'
}

function check_push_event() {
    cd $DIR
    echo "Check for push event"
    git fetch
    if [ $(git rev-list HEAD..origin/master --count) -gt 0 ]; then
        echo "New push event detected"
        git pull
        trigger_tools
    else
        echo "No new push events"
    fi
}

if [[ -d "$DIR" ]]; then
    echo "$DIR exists"
    check_push_event
else
    echo "Does not exist"
    # Cloning the repository if it does not exist
    git clone git://git.postgresql.org/git/pgweb.git
    trigger_tools
fi
