#!/bin/bash

function insertIntoTemplate()
{
	(cat "$1" && printf "\n") \
		| tr '\n	' '`' \
		| xargs -I {} sed 's|%%%|{}|' template.html \
		| tr '`' '\n'
}

while inotifywait -e close_write ../output.csv; do
	./render

	insertIntoTemplate schueler.part > schueler.html
	insertIntoTemplate offen.part > offen.html
	insertIntoTemplate firmen.part > firmen.html
done
