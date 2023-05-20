DIR=pgweb

function trigger_tools() {
	echo "Triggering Testing Tools"
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
