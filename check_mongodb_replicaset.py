#!/usr/bin/python
# author: Andre Michi <andremichi@gmail.com>
# description: Simple nagios plugin to monitoring MongoDB ReplicaSet
# date: 07/17/2012
# comments: Fell free to contribute, change and opine. =)

from pymongo import Connection,errors	# Import Connection and errors from pymongo module.
import sys								# Import sys module for nagios system exits.

# slavesThreshold, set this variable value according to the number of MongoDB servers in your replicaSet configuration.
slavesThreshold = 2

# Mongodb_port by default is 27017, so change according to your configuration. 
# Create a new connection to mongodb on localhost, slave_okay needs to be enable for queries on a slave node.
connection = Connection('localhost', 27017 , slave_okay=True)
# Connect to a test database to enable db.commands
db = connection.test
# Saves the result of 'isMaster' "query"
res = db.command('isMaster')
hosts = []
# Try to get all variables needed.
try:
	replicasetName = res['setName']
	masterStatus = res['ismaster']
	primaryHost = res['primary']
	hosts = res['hosts']
# If 2 MongoDB Servers are down, the connection to the primary server is impossible, so the entirely ReplicaSet are unavailable.
except KeyError:
	print "[ CRITICAL ]  - Check if MongoDB is running on at least two servers"
	sys.exit(2)
# After getting the keys from MongoDB ReplicaSet, the script try to see if there are 2 secondaries servers running.
if primaryHost is not None:
	hosts.remove(primaryHost)
	slaveHosts = []
	for host in hosts:
		host,port = host.split(':')
		try:
			conn = Connection(host, slave_okay=True)
			db = conn.test
			res = db.command('isMaster')
			slaveStatus = str(res['secondary'])
			if slaveStatus == "True":
				slaveHosts.append(host)
		except errors.AutoReconnect:
			print "Could not connect to host " +host
	# If there are less than 2 secondaries servers, an Warning is emmited. MongoDB works with at least 1 primary and 1 secondary server.
	if len(slaveHosts) < slavesThreshold:
		print "[ WARNING ] - Only one slave server running " + slaveHosts
		sys.exit(1)
	# If the primary and two secondaries
	else:
		print "[ OK ] - ReplicaSet " + replicasetName + " running with Master server " + primaryHost + " and two other slaves"
		sys.exit(0)
