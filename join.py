#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb as mdb
import datetime
import cgi
# DEBUG No need to import cgitb when done debugging
#import cgitb
import json as j
import sys

import sqlGlobals as g
import sqlPassword as p
import JSONDateTimeEncoder as jsondte

#f = open("./debugLog","a")
f = None

def debuglog(message):
#    f.write("%s %s\n" % (datetime.datetime.now().isoformat(), message) )
    f

con = None

# DEBUG Turn this off when done debugging
#cgitb.enable(display=0, logdir=".")

# The 400 error code
STATUS_400_STR = "Status: 400 Bad Request"

# Get the passed CGI parameters
params = cgi.FieldStorage()

# Check that we have all the required inputs we need
DEV_ID_STR = "DeviceId"
BEAC_ID_STR = "BeaconId"
if (BEAC_ID_STR not in params or
    DEV_ID_STR not in params):
    # Complain
    print STATUS_400_STR
    print
    print ("Must include " + BEAC_ID_STR + ", " + DEV_ID_STR )
    debuglog("Bad input params")
    sys.exit(1)

# Ok, get the parameters

# Do the following for BeaconId and DeviceId
def longCheck(key, base=10):
    try:
        return long(params.getvalue(key),base)
    except ValueError, e:
        print STATUS_400_STR
        print
        print key + " should be an integer"
        debuglog("%s not an integer" % (key))
        sys.exit(1)

# Get the Lat, Lon, and DeviceId
BeaconId = longCheck(BEAC_ID_STR)
DeviceId = longCheck( DEV_ID_STR, base=16)

if (DeviceId < 0):
    print STATUS_400_STR
    print
    print "Invalid DeviceId"
    debuglog("Bad deviceId")
    sys.exit(1)

# Created

# Ok, try connecting to the server

try:
    con = mdb.connect(g.server, g.username, p.password, g.dbname);
    cur = con.cursor(cursorclass=mdb.cursors.DictCursor)

    # Check that this BeaconId exists
    COUNT_STR = 'Count'
    cur.execute("SELECT count(1) AS " + COUNT_STR + " FROM beacons WHERE BeaconId=%s LIMIT 1", (BeaconId,))
    row = cur.fetchone()
    # Shouldn't be anything else but just in case ...
    cur.nextset()

    debuglog("Found %d entries in beacons with BeaconId %s" % (row[COUNT_STR],str(DeviceId)))

    if row[COUNT_STR]==0:
        print STATUS_400_STR
        print
        print "No such BeaconId!"
        debuglog("No such BeaconId!")
        sys.exit(1)

    # Ok, can proceed.
    # Can this fail??
    nInsert1 = cur.execute("""
INSERT INTO devices (DeviceId, BeaconId, Joined)
VALUES (%s,%s,now())
ON DUPLICATE KEY
UPDATE BeaconId=%s, Joined=now()
""", (DeviceId, BeaconId, BeaconId))

    debuglog("nInsert1 is %d" % (nInsert1))
    
    # Fast forward past the empty result set
    cur.nextset()

    debuglog("fast forwarded")

    nInsert2 = cur.execute("""
SELECT b.BeaconId AS BeaconId,LatE6,LonE6,Course,Details,Telephone,Email,Created,Expires,count(DeviceId) AS Count
FROM devices d INNER JOIN beacons b
ON b.BeaconId=d.BeaconId
WHERE b.BeaconId=%s
GROUP BY b.BeaconId LIMIT 1;
""", (BeaconId))

    debuglog("nInsert2 is %d" % (nInsert2))

    updatedBeacon = cur.fetchone()

    debuglog("got updatedBeacon")

    # Success??
    print "Content-Type: application/json"
    print

    # JSON it out (see the JSONDateTimeEncoder.py)
    print j.dumps(updatedBeacon,cls=jsondte.JSONDateTimeEncoder)
    
except mdb.Error, e:

    print "Status: 502 Bad Gateway"
    print
    print "Error %d: %s" % (e.args[0],e.args[1])
    
    debuglog("Error %d: %s" % (e.args[0],e.args[1]))


finally:

    if f:
        f.close()
    if con:
        con.close()
