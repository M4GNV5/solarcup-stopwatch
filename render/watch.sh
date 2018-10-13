#!/bin/bash

host="<target location here>"

function insertAndUploadTemplate()
{
	name="$1"
	(cat "$name.part" && printf "\n") \
		| tr '\n	' '`' \
		| xargs -I {} sed 's|%%%|{}|' template.html \
		| tr '`' '\n' \
		> tmp.html

	scp tmp.html "$host/$name/index.html"
	rm "$name.part"
	rm tmp.html
}

while inotifywait -e close_write ../output.csv; do
	./render
	insertAndUploadTemplate schueler
	insertAndUploadTemplate offen
	insertAndUploadTemplate firmen
done
