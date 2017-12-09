#!/bin/bash

BASEDIR="$(dirname $0)"
HSDATA_URL="https://github.com/HearthSim/hsdata.git"
HSDATA_DIR="$BASEDIR/hsdata"
HEARTHFORGE_URL="https://github.com/HearthSim/hearthforge.git"
HEARTHFORGE_DIR="$BASEDIR/assets"

command -v git &>/dev/null || {
	>&2 echo "ERROR: git is required to bootstrap this project."
	exit 1
}

fetch_git() {
	echo "Fetching data files from $1"
	if [[ ! ( -e "$2" && -e "$2/.git" ) ]]; then
		git clone --depth=1 "$1" "$2"
	else
		git -C "$2" fetch &&
		git -C "$2" reset --hard origin/master
	fi
}

fetch_git $HSDATA_URL $HSDATA_DIR
fetch_git $HEARTHFORGE_URL $HEARTHFORGE_DIR
