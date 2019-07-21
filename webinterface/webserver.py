from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, quote
from datetime import datetime
import re, json, threading

ADDR, PORT = ("0.0.0.0", 8080)
dummyTime = datetime(2018, 1, 1)

def saveTeams():
	with open("teams.csv", "w") as fd:
		for team in teams:
			fd.write("%d,%s\n" % (team["id"], team["name"]))

class RequestHandler(BaseHTTPRequestHandler):
	def send(self, msg):
		self.wfile.write(msg.encode("utf-8"))

	def redirectTo(self, url):
		self.send_response(302)
		self.send_header('Content-type', 'text/text; charset=utf-8')
		self.send_header("Location", quote(url, safe="/:."))
		self.end_headers()
		self.send("")

	def do_GET(self):
		self.send_response(200)
		self.end_headers()
		with open("webinterface/interface.html", "r") as fd:
			self.send(fd.read())

	def do_POST(self):
		length = int(self.headers["Content-Length"])
		data = parse_qs(self.rfile.read(length).decode("utf-8"))

		def getArg(name):
			if name in data:
				return data[name][0]
			else:
				raise "Missing argument " + name

		action = getArg("action")
		if action == "load":
			_runs = []
			for id, name, start, stop in runs:
				_runs.append({
					"id": id,
					"name": name,
					"time": formatTime(None, stop - start),
					"start": str(start),
				})

			_teams = []
			for team in teams:
				_teams.append({
					"id": team["id"],
					"name": team["name"],
					"best": formatTime(team),
				})

			self.send_response(200)
			self.end_headers()
			self.send(json.dumps({
				"teams": _teams,
				"runs": _runs,
			}))
		elif action == "setlane":
			team = int(getArg("team"))
			lane = int(getArg("lane"))

			if lane < 0 or lane >= len(activeTeams):
				self.send_response(400)
				self.end_headers()
				self.send("invalid lane")

			team = [x for x in filter(lambda x: x["id"] == team, teams)]
			if len(team) == 0:
				self.send_response(400)
				self.end_headers()
				self.send("invalid team")
			else:
				activeTeams[lane] = team[0]
				self.send_response(200)
				self.end_headers()
				self.send("ok")
		elif action == "delrun":
			delId = int(getArg("team"))
			delStart = getArg("start").strip()

			index = None
			for i, run in enumerate(runs):
				id, name, start, stop = run
				if id == delId and str(start) == delStart:
					index = i
					break

			if index is None:
				self.send_response(404)
				self.end_headers()
				self.send("run not found")
			else:
				with open("runs.csv", "a") as fd:
					fd.write("# delete previous run: %s\n" % str(runs[index]))

				del runs[index]
				resetBestscores()
				resortHighscore()


				self.send_response(200)
				self.end_headers()
				self.send("ok")
		elif action == "addteam":
			id = int(getArg("id"))
			name = getArg("name").strip()

			for team in teams:
				if team["id"] == id or team["name"] == name:
					self.send_response(400)
					self.end_headers()
					self.send("already exists")
					return

			teams.append({
				"id": id,
				"name": name,
				"running": False,
				"start": dummyTime,
				"stop": dummyTime,
				"best": None
			})
			saveTeams()

			self.send_response(200)
			self.end_headers()
			self.send("ok")
		elif action == "delteam":
			id = int(getArg("id"))

			index = None
			for i, team in enumerate(teams):
				if team["id"] == id:
					index = i
					break

			if index is None:
				self.send_response(404)
				self.end_headers()
				self.send("team not found")
			else:
				for i, team in enumerate(activeTeams):
					if team == teams[index]:
						activeTeams[i] = None

				del teams[index]
				saveTeams()

				self.send_response(200)
				self.end_headers()
				self.send("ok")



def webserverWorker(httpd):
	print("Webserver started on Port " + str(PORT))
	httpd.serve_forever()

def startWebserver(_teams, _activeTeams, _runs, _resetBestscores, _resortHighscore, _formatTime):
	global teams, activeTeams, runs, resetBestscores, resortHighscore, formatTime
	teams, activeTeams, runs, resetBestscores, resortHighscore, formatTime = \
		_teams, _activeTeams, _runs, _resetBestscores, _resortHighscore, _formatTime

	httpd = HTTPServer((ADDR, PORT), RequestHandler)

	worker = threading.Thread(target=webserverWorker, args=(httpd,), name="webserverWorker")
	worker.daemon = True
	worker.start()
