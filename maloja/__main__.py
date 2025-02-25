import os
import signal
import subprocess
import time

from setproctitle import setproctitle
from ipaddress import ip_address

from doreah.control import mainfunction
from doreah.io import col
from doreah.logging import log

from . import __pkginfo__ as pkginfo
from .pkg_global import conf
from .proccontrol import tasks
from .setup import setup
from .dev import generate, apidebug



def print_header_info():
	print()
	#print("#####")
	print(col['yellow']("Maloja"),f"v{pkginfo.VERSION}")
	print(pkginfo.HOMEPAGE)
	#print("#####")
	print()



def get_instance():
	try:
		return int(subprocess.check_output(["pidof","maloja"]))
	except Exception:
		return None

def get_instance_supervisor():
	try:
		return int(subprocess.check_output(["pidof","maloja_supervisor"]))
	except Exception:
		return None

def restart():
	if stop():
		start()
	else:
		print(col["red"]("Could not stop Maloja!"))

def start():
	if get_instance_supervisor() is not None:
		print("Maloja is already running.")
	else:
		print_header_info()
		setup()
		try:
			#p = subprocess.Popen(["python3","-m","maloja.server"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
			sp = subprocess.Popen(["python3","-m","maloja","supervisor"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
			print(col["green"]("Maloja started!"))

			port = conf.malojaconfig["PORT"]

			print("Visit your server address (Port " + str(port) + ") to see your web interface. Visit /admin_setup to get started.")
			print("If you're installing this on your local machine, these links should get you there:")
			print("\t" + col["blue"]("http://localhost:" + str(port)))
			print("\t" + col["blue"]("http://localhost:" + str(port) + "/admin_setup"))
			return True
		except Exception:
			print("Error while starting Maloja.")
			return False


def stop():

	for attempt in [(signal.SIGTERM,2),(signal.SIGTERM,5),(signal.SIGKILL,3),(signal.SIGKILL,5)]:

		pid_sv = get_instance_supervisor()
		pid = get_instance()

		if pid is None and pid_sv is None:
			print("Maloja stopped!")
			return True

		if pid_sv is not None:
			os.kill(pid_sv,attempt[0])
		if pid is not None:
			os.kill(pid,attempt[0])

		time.sleep(attempt[1])

	return False






	print("Maloja stopped!")
	return True

def onlysetup():
	print_header_info()
	setup()
	print("Setup complete!")

def run_server():
	print_header_info()
	setup()
	setproctitle("maloja")
	from . import server
	server.run_server()

def run_supervisor():
	setproctitle("maloja_supervisor")
	while True:
		log("Maloja is not running, starting...",module="supervisor")
		try:
			process = subprocess.Popen(
			    ["python3", "-m", "maloja","run"],
			    stdout=subprocess.DEVNULL,
			    stderr=subprocess.DEVNULL,
			)
		except Exception as e:
			log("Error starting Maloja: " + str(e),module="supervisor")
		else:
			try:
				process.wait()
			except Exception as e:
				log("Maloja crashed: " + str(e),module="supervisor")

def debug():
	os.environ["MALOJA_DEV_MODE"] = 'true'
	conf.malojaconfig.load_environment()
	direct()

def print_info():
	print_header_info()
	print(col['lightblue']("Configuration Directory:"),conf.dir_settings['config'])
	print(col['lightblue']("Data Directory:         "),conf.dir_settings['state'])
	print(col['lightblue']("Log Directory:          "),conf.dir_settings['logs'])
	print(col['lightblue']("Network:                "),f"IPv{ip_address(conf.malojaconfig['host']).version}, Port {conf.malojaconfig['port']}")
	print(col['lightblue']("Timezone:               "),f"UTC{conf.malojaconfig['timezone']:+d}")
	print()
	print()

@mainfunction({"l":"level","v":"version","V":"version"},flags=['version','include_images'],shield=True)
def main(*args,**kwargs):

	actions = {
		# server
		"start":start,
		"restart":restart,
		"stop":stop,
		"run":run_server,
		"supervisor":run_supervisor,
		"debug":debug,
		"setup":onlysetup,
		# admin scripts
		"import":tasks.import_scrobbles,		# maloja import /x/y.csv
		"backup":tasks.backup,					# maloja backup --targetfolder /x/y --include_images
		"generate":generate.generate_scrobbles,	# maloja generate 400
		"export":tasks.export,					# maloja export
		"apidebug":apidebug.run,				# maloja apidebug
		# aux
		"info":print_info
	}

	if "version" in kwargs:
		print(info.VERSION)
		return True
	else:
		try:
			action, *args = args
			action = actions[action]
		except (ValueError, KeyError):
			print("Valid commands: " + " ".join(a for a in actions))
			return False

		return action(*args,**kwargs)
