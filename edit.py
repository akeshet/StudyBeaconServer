#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb as mdb
import datetime
import cgi
# DEBUG No need to import cgitb when done debugging
import cgitb
import json as j
import sys

import sqlGlobals as g
import sqlPassword as p
import JSONDateTimeEncoder as jsondte

f = None
#f = open("./debuglog","a")


def debuglog(message):
#    f.write("%s edit - %s\n" % (datetime.datetime.now().isoformat(), message) )
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

# Do the following for Lat, Lon, BeaconId, and DeviceId
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
DeviceId = longCheck(DEV_ID_STR, base=16)
BeaconId = longCheck(BEAC_ID_STR)

# The rest of the params are optional
# Put together a tuple and a query string
queryParams = ()
queryFields = ()

# Validate the Lat, Lon, and DeviceId
LatE6Min = -80000000L
LatE6Max = +80000000L
LonE6Min = -180000000L
LonE6Max = +180000000L

# Ok, get the parameters
LAT_STR = "LatE6"
LON_STR = "LonE6"
# if LAT_STR in params:
#     LatE6 = longCheck(LAT_STR)
#     if (LatE6 < LatE6Min or LatE6 > LatE6Max):
#         print STATUS_400_STR
#         print 
#         print "Latitude out of bounds"
#         debuglog("Lat bounds")
#         sys.exit(1)
#     queryParams = queryParams + (LatE6,)
#     queryFields = queryFields + (LAT_STR,)

# if LON_STR in params:
#     LonE6 = longCheck(LON_STR)
#     if (LonE6 < LonE6Min or LonE6 > LonE6Max):
#         print STATUS_400_STR
#         print 
#         print "Longitude out of bounds"
#         debuglog("Lon bounds")
#         sys.exit(1)
#     queryParams = queryParams + (LonE6,)
#     queryFields = queryFields + (LON_STR,)

# PARAM: duration (integer number of minutes)
DURATION_STR = 'Duration'
DURATION_MAX = 36*60L
SQL_DATE_FMT_STR = '%Y-%m-%d %H:%M:%S'
EXPIRES_STR = 'Expires'
if DURATION_STR in params:
    duration = longCheck(DURATION_STR)
    if (duration < 0 or duration > DURATION_MAX):
        print STATUS_400_STR
        print
        print DURATION_STR + "must be positive and less than %s" % (DURATION_MAX)
        debuglog("Bad duration")
        sys.exit(1)
    debuglog("duration %d in params" % duration)
    now = datetime.datetime.now()
    # Expires
    delta = datetime.timedelta(minutes=duration)
    expires = now+delta
    expiresStr = expires.strftime(SQL_DATE_FMT_STR)

    queryParams = queryParams + (expiresStr,)
    queryFields = queryFields + (EXPIRES_STR,)

# The rest are all strings, so we can do the same thing.
def addIfIn(paramName):
    global queryParams, queryFields
    if paramName in params:
        paramValue = params.getvalue(paramName)
        if (paramValue.isspace()):
            paramValue = ""
        debuglog("%s = %s" % (paramName,paramValue))
        queryParams = queryParams + (paramValue,)
        queryFields = queryFields + (paramName,)

DETAILS_STR = 'Details'
WORKINGON_STR = 'WorkingOn'
TELEPHONE_STR = 'Telephone'
EMAIL_STR = 'Email'

addIfIn(DETAILS_STR)
addIfIn(WORKINGON_STR)
addIfIn(TELEPHONE_STR)
addIfIn(EMAIL_STR)

# Ok, try connecting to the server

try:
    con = mdb.connect(g.server, g.username, p.password, g.dbname);
    cur = con.cursor(cursorclass=mdb.cursors.DictCursor)

    # Check if this DeviceId is already at an existing beacon
    COUNT_STR = 'Count'
    cur.execute("SELECT count(1) AS " + COUNT_STR + " FROM devices WHERE DeviceId=%s AND BeaconId=%s", (DeviceId,BeaconId))
    row = cur.fetchone()
    # Shouldn't be anything else but just in case ...
    cur.nextset()

    debuglog("Found %d entries in devices with deviceid %s and beaconid %s" % (row[COUNT_STR],str(DeviceId),BeaconId))

    if row[COUNT_STR]==0:
        print STATUS_400_STR
        print
        print "Not at this beacon"
        debuglog("Not at this beacon")
        sys.exit(1)

    # Ok, can proceed.
    # Can this fail??
    if (len(queryFields)>0):
        setString = ", ".join( map( lambda s: s+'=%s'  , queryFields  ) )
        queryString = 'UPDATE beacons SET %s WHERE BeaconId=%%s' % setString
        debuglog("trying to UPDATE")
        debuglog("query string is %s" % queryString)
        nUpdate = cur.execute(queryString, queryParams + (BeaconId,))
        
        debuglog("nUpdate is %d" % (nUpdate))
        
        # Fast forward past the empty result set
        cur.nextset()

        debuglog("fast forwarded")

    nSelect = cur.execute("""
SELECT b.BeaconId AS BeaconId,LatE6,LonE6,Course,WorkingOn,Details,Telephone,Email,Created,Expires,count(DeviceId) AS Count
FROM devices d INNER JOIN beacons b
ON b.BeaconId=d.BeaconId
WHERE b.BeaconId=%s
GROUP BY b.BeaconId LIMIT 1;
""", (BeaconId,))

    debuglog("nSelect is %d" % (nSelect))

    editedRow = cur.fetchone()

    debuglog("got editedRow")

    # Success??
    print "Content-Type: application/json"
    print

    # JSON it out (see the JSONDateTimeEncoder.py)
    print j.dumps(editedRow,cls=jsondte.JSONDateTimeEncoder)
    
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
