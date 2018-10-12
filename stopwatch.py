from threading import Thread
from time import sleep
from datetime import datetime
import cv2
import numpy as np
import serial
import sys
import threading

size = (1080, 1920, 3)
color = (0, 0, 0)
laneCount = 2
logos = [
	"solarcup.jpg",
	"buergernetz.png",
	"esv.jpg"
]
min_rect_size = 10000
rect_color = (0, 0, 255)
fps = 60
dummyTime = datetime(2018, 1, 1)

teams = []
activeTeams = [None] * laneCount
highscores = []
editing = None
editingId = 0
editingResult = None

def laneIdToText(id):
	return chr(ord('A') + id)

def putText(img, pos, text, scale=2, thick=3, font=cv2.FONT_HERSHEY_SIMPLEX):
	cv2.putText(img, text, pos, font, scale, color, thick)

def putTextTopLeft(img, pos, text, scale=2, thick=3, font=cv2.FONT_HERSHEY_SIMPLEX, maxWidth=0):
	(w, h), baseLine = cv2.getTextSize(text, font, scale, thick)
	if maxWidth > 0:
		while w > maxWidth:
			(w, h), baseLine = cv2.getTextSize(text, font, scale, thick)
			text = text[0:-1]

	x, y = pos
	putText(img, (x, y + h), text, scale, thick, font)
	return w, h

def resetEditingResult():
	global editingResult
	found = filter(lambda x: x["id"] == editingId, teams)
	if len(found) == 0:
		editingResult = None
	else:
		editingResult = found[0]

def resortHighscore():
	global highscores
	highscores = sorted(filter(lambda x: x["best"] != None, teams), key=lambda x: x["best"])

def formatTime(team, diff=None):
	if diff == None:
		diff = team["stop"] - team["start"]
	#mins = int(diff.seconds / 60)
	seconds = int(diff.seconds)# % 60)
	millis = int(diff.microseconds / 10000)
	return "%02d.%02d" % (seconds, millis)

def startTeam(team):
	if not team["running"]:
		now = datetime.now()
		team["running"] = True
		team["start"] = now
		team["stop"] = now

def stopTeam(team):
	if team["running"]:
		now = datetime.now()
		team["running"] = False
		team["stop"] = now

		diff = team["stop"] - team["start"]
		if team["best"] == None or diff < team["best"]:
			team["best"] = diff

		with open("output.csv", "a") as fd:
			fd.write("%s,%s,%s,%s\n" % (team["name"], team["start"], team["stop"], formatTime(team)))

		resortHighscore()

def stopAllTeams():
	for team in activeTeams:
		if team != None:
			stopTeam(team)
			team["start"] = dummyTime
			team["stop"] = dummyTime

	activeTeams[:] = None
	resortHighscore()

with open("teams.csv") as fd:
	for line in fd:
		line = line.strip()
		if line == "":
			break

		id, name, best = line.split(",")
		if best == "":
			best = None

		teams.append({
			"id": int(id),
			"name": name,
			"running": False,
			"start": dummyTime,
			"stop": dummyTime,
			"best": best
		})

def serialWorker():
	ser = serial.Serial(sys.argv[1], 9600)
	while True:
		char = ser.read(1)
		if char == "1": #"A_start"
			startTeam(activeTeams[0])
		elif char == "2": #"A_stop"
			stopTeam(activeTeams[0])
		elif char == "3": #"B_start"
			startTeam(activeTeams[1])
		elif char == "4": #"B_stop"
			stopTeam(activeTeams[1])

logos = logos[::-1]
for i, path in enumerate(logos):
	img = cv2.imread(path)
	logos[i] = img

if len(sys.argv) > 1:
	worker = threading.Thread(target=serialWorker, name="serialWorker")
	worker.daemon = True
	worker.start()

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
	for i, team in enumerate(activeTeams):
		if team == None:
			continue

		if team["running"]:
			team["stop"] = now

		w, h = putTextTopLeft(img, (x, y), "Bahn %s: %s" % (laneIdToText(i), team["name"]), maxWidth=size[1] / 2)
		y = y + h + 10

		w, h = putTextTopLeft(img, (x, y), formatTime(team))
		y = y + h + 20

	h, w, c = size
	if editing != None:
		if editingResult == None:
			name = "unknown team"
		else:
			name = editingResult["name"]
		putText(img, (5, h - 5), "Team auf Bahn %s: %d (%s)" % (laneIdToText(editing), editingId, name), scale=1)

	x, y = size[1] / 2 + 20, 20
	for team in highscores:
		w1, h1 = putTextTopLeft(img, (x, y), formatTime(team, team["best"]))
		w2, h2 = putTextTopLeft(img, (x + w1 + 10, y), team["name"])
		y = y + max(h1, h2) + 20

	cv2.imshow("dashboard", img)
	rawKey = cv2.waitKey(1000 / fps) & 0xfffff
	key = rawKey & 0xff
	if key == ord('q'):
		break
	elif rawKey == 0x001b: #esc
		editing = None
		editingId = 0
	elif rawKey == 0x000a: #enter
		if editingResult != None:
			activeTeams[editing] = editingResult
			editing = None
			editingId = 0
	elif rawKey == 0xff08: #backspace
		editingId = editingId / 10
		resetEditingResult()
	elif key >= ord('a') and key < ord('a') + laneCount:
		i = key - ord('a')
		if activeTeams[i] and activeTeams[i]["running"]:
			stopTeam(activeTeams[i])
		else:
			editing = i
			editingId = 0
			resetEditingResult()
	elif editing != None and key >= ord('0') and key <= ord('9'):
		editingId = editingId * 10 + key - ord('0')
		resetEditingResult()
