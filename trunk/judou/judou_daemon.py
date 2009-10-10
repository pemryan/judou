#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, time
from daemon import Daemon
from judou_server import JudouServer
from judou_daemon_conf import *

class JudouDaemon(Daemon):
    def run(self):
        s = JudouServer(HOST, PORT)
        s.run()

if __name__ == "__main__":
	daemon = JudouDaemon('/tmp/judou_daemon.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		else:
			print "Unknown command"
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart" % sys.argv[0]
		sys.exit(2)
