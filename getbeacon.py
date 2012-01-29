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

#f = open("./debuglog","a")
f = None

def debuglog(message):
#    f.write("%s whereami %s\n" % (datetime.datetime.now().isoformat(), message) )
    f

con = None

# DEBUG Turn this off when done debugging
#cgitb.enable(display=0, logdir=".")

# The 400 error code
STATUS_400_STR = "Status: 400 Bad Request"

# Get the passed CGI parameters
params = cgi.FieldStorage()

# Check that we have all the required inputs we need
BEAC_ID_STR = "BeaconId"
if (BEAC_ID_STR not in params):
    # Complain
    print STATUS_400_STR
    print
    print ("Must include " + BEAC_ID_STR )
    debuglog("Bad input params")
    sys.exit(1)

# Ok, get the parameters

# Do the following for DeviceId
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
BeaconId = longCheck( BEAC_ID_STR)

# Ok, try connecting to the server

try:
    con = mdb.connect(g.server, g.username, p.password, g.dbname);
    cur = con.cursor(cursorclass=mdb.cursors.DictCursor)

    nSelect = cur.execute("""
SELECT b.BeaconId AS BeaconId,LatE6,LonE6,Course,Details,WorkingOn,Telephone,Email,Created,Expires,count(DeviceId) AS Count
FROM devices d INNER JOIN beacons b
ON b.BeaconId=d.BeaconId
WHERE b.BeaconId=%s
GROUP BY b.BeaconId LIMIT 1;
""", (BeaconId,))

    debuglog("nSelect is %d" % (nSelect))

    currentBeacon = cur.fetchone()

    debuglog("got currentBeacon")

    # Success??
    print "Content-Type: application/json"
    print

    # JSON it out (see the JSONDateTimeEncoder.py)
    print j.dumps(currentBeacon,cls=jsondte.JSONDateTimeEncoder)
    
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
