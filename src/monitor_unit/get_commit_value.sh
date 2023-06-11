DIR=pgweb

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

git clone git://git.postgresql.org/git/pgweb.git
git rev-parse HEAD >"commit_id.txt"
#
# if [[ -d "$DIR" ]]; then
#     echo "$DIR exists"
#     check_push_event
# else
#     echo "Does not exist"
#     # Cloning the repository if it does not exist
# fi
