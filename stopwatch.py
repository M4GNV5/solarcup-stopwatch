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

teams = []
highscores = []
current = 0

def putTextTopLeft(img, pos, text, scale=2, thick=3, font=cv2.FONT_HERSHEY_SIMPLEX):
	(w, h), baseLine = cv2.getTextSize(text, font, scale, thick)
	x, y = pos
	cv2.putText(img, text, (x, y + h), font, scale, color, thick)
	return w, h

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

def stopAllTeams():
	max = len(teams)
	for i in range(0, laneCount):
		if current + i < max:
			stopTeam(teams[current + i])
			teams[current + 1]["stop"] = teams[current + 1]["start"]

	resortHighscore()

with open("teams.list") as fd:
	dummy = datetime(2018, 1, 1)
	for line in fd:
		line = line.strip()
		if line == "":
			break

		teams.append({"name": line, "running": False, "start": dummy, "stop": dummy, "best": None})

def serialWorker():
	ser = serial.Serial(sys.argv[1], 9600)
	while True:
		char = ser.read(1)
		if line == "1": #"A_start"
			startTeam(teams[current])
		elif line == "2": #"A_stop"
			stopTeam(teams[current])
		elif line == "3": #"B_start"
			startTeam(teams[current + 1])
		elif line == "4": #"B_stop"
			stopTeam(teams[current + 1])

logos = logos[::-1]
for i, path in enumerate(logos):
	img = cv2.imread(path)
	logos[i] = img

if len(sys.argv) > 1:
	worker = threading.Thread(target=serialWorker, name="serialWorker")
	worker.daemon = True
	worker.start()

cap = cv2.VideoCapture(0)
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
	for i in range(current, current + laneCount):
		team = teams[i]
		if "start" not in team:
			team["start"] = now
			team["stop"] = now

		if team["running"]:
			team["stop"] = now

		w, h = putTextTopLeft(img, (x, y), team["name"])
		y = y + h + 10

		w, h = putTextTopLeft(img, (x, y), formatTime(team))
		y = y + h + 20

	y = y + 100
	ret, frame = cap.read()
	if ret:
		hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
		thresh = cv2.inRange(hsv, (110, 30, 30), (130, 255, 255))
		contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
		for contour in contours:
			cx, cy, w, h = cv2.boundingRect(contour)
			if w * h >= min_rect_size:
				cv2.rectangle(frame, (cx, cy), (cx + w, cy + h), rect_color, 3)

		h, w, c = frame.shape
		img[y : y + h, x : x + w] = frame

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
	elif rawKey == 0xff53: #right arrow
		stopAllTeams()
		current = current + laneCount
		if current + laneCount > len(teams):
			current = current - len(teams)
	elif rawKey == 0xff51: #left arrow
		stopAllTeams()
		current = current - laneCount
		if current <= -laneCount:
			current = current + len(teams)
	elif key > ord('0') and key <= ord('0') + laneCount:
		i = key - ord('0') - 1
		team = teams[current + i]
		if team["running"]:
			stopTeam(team)
			resortHighscore()
		else:
			startTeam(team)

cap.release()
