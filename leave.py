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
#    f.write("leave: %s %s\n" % (datetime.datetime.now().isoformat(), message) )
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


BeaconId = longCheck(BEAC_ID_STR)
DeviceId = longCheck( DEV_ID_STR, base=16)

if (DeviceId < 0):
    print STATUS_400_STR
    print
    print "Invalid DeviceId"
    debuglog("Bad deviceId")
    sys.exit(1)

# Ok, try connecting to the server

try:
    con = mdb.connect(g.server, g.username, p.password, g.dbname);
    cur = con.cursor(cursorclass=mdb.cursors.DictCursor)

    # just try to do it blindly
    nRows = cur.execute("""
DELETE FROM devices
WHERE BeaconId=%s AND DeviceId=%s
""", (BeaconId,DeviceId))

    debuglog("nRows is %d" % (nRows))

    if (1 == nRows):
        print "Content-Type: text/plain"
        print
        print "Ok."
    else:
        print STATUS_400_STR
        print
        print "Failure."

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
