#!/bin/bash
if [ -f .showdb.json.bak ]; then
	rm .showdb.json.bak
fi

if [ -f .tracker.json.bak ]; then
	rm .tracker.json.bak
fi

cp .showdb.json{.orig,}
cp .tracker.json{.orig,}
