#!/bin/bash
# Builds the FreeCAD release zips from files/freecad/<version>/, so the zips and the folders in
# this repository never differ. Each zip is named after the version and the booklet version in
# that folder's manifest.json:
#   tools/release/freecad-zips.sh            # writes dist/freecad-<version>-recipes-v<booklet>.zip
# Attach each zip to the release with the same tag name (without .zip).
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p dist
for dir in files/freecad/*/; do
	version=$(basename "$dir")
	booklet=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["booklet"])' "$dir/manifest.json")
	name="freecad-$version-recipes-v$booklet"
	stage=$(mktemp -d)
	cp -r "$dir" "$stage/$name"
	rm -f "dist/$name.zip"
	(cd "$stage" && zip -qrX "$OLDPWD/dist/$name.zip" "$name")
	rm -r "$stage"
	echo "dist/$name.zip"
done
