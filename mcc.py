#!/usr/bin/python

import httplib, urllib
import argparse
import uuid
import socket
import psutil
from time import sleep

import signal
import sys

def signal_handler(signal, frame):
	ret = controlApps(server, node, apps, "DISABLE-APP")
	print ret[0][0]
	print ret[1][0]
	ret = controlApps(server, node, apps, "STOP-APP")
	print ret[0][0]
	print ret[1][0]
	ret = controlApps(server, node, apps, "REMOVE-APP")
	print ret[0][0]
	print ret[1][0]
	ret = unregisterNode (server, node)
	print ret[0]
	sys.exit(0)


class modClusterServer:
	host = ''
	port = 80
	conn = None
	
class Node:
	jvmRoute = ''
	host = ''
	port = 80
	stickySessionForce = False
	connectionType = 'http' 

class Application:
	context = ''
	alias = 'localhost'
	def __init__(self, context, alias='localhost'):
		self.context = context
		self.alias = alias

def createModClusterServer(host, port):
	server = modClusterServer()
	server.host = host
	server.port = port
	return server

def createNode ():
	node = Node()
	try:
		node.host = socket.gethostbyname(socket.gethostname())
	except e:
		node.host = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1]
	node.jvmRoute = uuid.uuid5(uuid.NAMESPACE_DNS, node.host)
	node.port = 80
	return node

def addApp (context, alias='localhost'):
	app = Application(context, alias)
	apps.append(app)

def sendRequest(server, method, url, params, persistent):
	headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
	if server.conn == None:
		server.conn = httplib.HTTPConnection(server.host, server.port)
	server.conn.request(method, url, params, headers)
	response = server.conn.getresponse()
	data = response.read()
	if not persistent:
		server.conn.close()
		server.conn = None
	return [ response.status, response.reason, data ]


def registerNode (server, node): 
	params = urllib.urlencode({'JVMRoute': node.jvmRoute, 'Host': node.host, 'Port': node.port, 'StickySessionForce': node.stickySessionForce , 'Type': node.connectionType })
	return sendRequest(server, "CONFIG", "/", params, False)

def unregisterNode (server, node):
	params = urllib.urlencode({'JVMRoute': node.jvmRoute })
	return sendRequest(server, "REMOVE-APP", "/*", params, False)

def controlApps (server, node, apps, command):
	ret = []
	for app in apps:
		params = urllib.urlencode({'JVMRoute': node.jvmRoute, 'Alias': app.alias, 'Context': app.context})
		ret.append(sendRequest(server, command, "/", params, True))
	server.conn.close()
	server.conn = None
	return ret

def informStatus (server, node):
	lbf = 100 - psutil.cpu_percent()
	params = urllib.urlencode({'JVMRoute': node.jvmRoute, 'Load': lbf })
	return sendRequest(server, "STATUS", "/", params, False)


parser = argparse.ArgumentParser()
parser.add_argument("-s", "--server", help="Modc_cluster server address/host")
parser.add_argument("-k", "--key", help="Modc_cluster advertise secret key")
args = parser.parse_args()

if args.server is None and args.key is None:
	parser.error('Must inform server address or advertise secret key')

signal.signal(signal.SIGINT, signal_handler)

running = True
apps = []

if args.server is None:
	server = createModClusterServer('localhost', 80)
else:
	server = createModClusterServer(args.server, 80)

node = createNode()
ret = registerNode(server, node)
print ret[0]

addApp('/')
addApp('/teste')
ret = controlApps(server, node, apps, "ENABLE-APP")
print ret[0][0]
print ret[1][0]

while running:
	sleep (10)
	ret = informStatus(server, node)



