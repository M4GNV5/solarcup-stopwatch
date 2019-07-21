from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, quote
import re, json, threading

ADDR, PORT = ("0.0.0.0", 8080)

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
		elif action == "delete":
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
