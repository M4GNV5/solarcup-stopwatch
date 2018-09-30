from threading import Thread
from time import sleep
from datetime import datetime
import cv2
import numpy as np

size = (1080, 1920, 3)
color = (0, 0, 0)
laneCount = 2
logos = [
	"solarcup.jpg",
	"buergernetz.png",
	"esv.jpg"
]

teams = []
highscores = []
current = 0

def putTextTopLeft(img, pos, text, scale=2, thick=3, font=cv2.FONT_HERSHEY_SIMPLEX):
	(w, h), baseLine = cv2.getTextSize(text, font, scale, thick)
	x, y = pos
	cv2.putText(img, text, (x, y + h), font, scale, color, thick)
	return w, h

def formatTime(team):
	diff = team["stop"] - team["start"]
	#mins = int(diff.seconds / 60)
	seconds = int(diff.seconds)# % 60)
	millis = int(diff.microseconds / 10000)
	return "%02d.%02d" % (seconds, millis)

def stopTeam(team):
	if team["running"]:
		team["running"] = False

		with open("output.csv", "a") as fd:
			fd.write("%s,%s,%s,%s\n" % (team["name"], team["start"], team["stop"], formatTime(team)))

with open("teams.list") as fd:
	dummy = datetime(2018, 1, 1)
	for line in fd:
		line = line.strip()
		if line == "":
			break

		teams.append({"name": line, "running": False, "start": dummy, "stop": dummy})

logos = logos[::-1]
for i, path in enumerate(logos):
	img = cv2.imread(path)
	logos[i] = img

cv2.namedWindow("dashboard", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("dashboard", cv2.WND_PROP_FULLSCREEN, 1)
img = np.zeros(size, dtype=np.uint8)
while True:
	img[:,:] = (255, 255, 255)

	x = size[1] - 20
	for logo in logos:
		h, w, c = logo.shape
		y = size[0] - h - 20
		img[y : y + h, x - w : x] = logo
		x = x - w - 20

	now = datetime.now()
	x, y = 20, 20
	for team in teams[current : current + laneCount]:
		if "start" not in team:
			team["start"] = now
			team["stop"] = now

		if team["running"]:
			team["stop"] = now

		w, h = putTextTopLeft(img, (x, y), team["name"])
		y = y + h + 10

		w, h = putTextTopLeft(img, (x, y), formatTime(team))
		y = y + h + 20

	x, y = size[1] / 2 + 20, 20
	for team in highscores:
		w1, h1 = putTextTopLeft(img, (x, y), formatTime(team))
		w2, h2 = putTextTopLeft(img, (x + w1 + 10, y), team["name"])
		y = y + max(h1, h2) + 20

	cv2.imshow("dashboard", img)
	key = cv2.waitKey(1) & 0xff
	if key == ord('q'):
		break
	elif key == ord(' '):
		stopTeam(teams[current])
		stopTeam(teams[current + 1])
		current = current + laneCount
		highscores = sorted(teams[0 : current], key=lambda x: x["stop"] - x["start"])
	elif key > ord('0') and key <= ord('0') + laneCount:
		i = key - ord('0') - 1
		team = teams[current + i]
		if team["running"]:
			stopTeam(team)
		else:
			team["start"] = now
			team["stop"] = now
			team["running"] = True
