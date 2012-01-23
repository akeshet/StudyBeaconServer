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
import JSONDateTimeEncoder as jsondte

f = None
#f = open("./debugLog","a")


def debuglog(message):
#    f.write("%s %s\n" % (datetime.datetime.now().isoformat(), message) )
    f

con = None

# DEBUG Turn this off when done debugging
cgitb.enable(display=0, logdir=".")

# The 400 error code
STATUS_400_STR = "Status: 400 Bad Request"

# Get the passed CGI parameters
params = cgi.FieldStorage()

# Check that we have all the required inputs we need
COURSE_STR = "Course"
LAT_STR = "LatE6"
LON_STR = "LonE6"
DEV_ID_STR = "DeviceId"
if (COURSE_STR not in params or
    LAT_STR not in params or
    LON_STR not in params or
    DEV_ID_STR not in params):
    # Complain
    print STATUS_400_STR
    print
    print ("Must include " + COURSE_STR + ", " + LAT_STR + ", " +
           LON_STR + ", " + DEV_ID_STR )
    debuglog("Bad input params")
    sys.exit(1)

# Ok, get the parameters
course = params.getvalue(COURSE_STR)
# TODO: Any way to validate the course?

# Do the following for Lat, Lon, and DeviceId
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
LatE6 = longCheck(LAT_STR)
LonE6 = longCheck(LON_STR)
DeviceId = longCheck(DEV_ID_STR, base=16)

# Validate the Lat, Lon, and DeviceId
LatE6Min = -80000000L
LatE6Max = +80000000L
LonE6Min = -180000000L
LonE6Max = +180000000L

if (LatE6 < LatE6Min or LatE6 > LatE6Max or
    LonE6 < LonE6Min or LonE6 > LonE6Max):
    print STATUS_400_STR
    print 
    print "Latitude/Longitude out of bounds"
    debuglog("Lat/Lon bounds")
    sys.exit(1)

if (DeviceId < 0):
    print STATUS_400_STR
    print
    print "Invalid DeviceId"
    debuglog("Bad deviceId")
    sys.exit(1)

# The rest of the params are optional
    
# PARAM: duration (integer number of minutes)
DURATION_STR = 'Duration'
if DURATION_STR in params:
    duration = longCheck(DURATION_STR)
else:
    DURATION_DEFAULT = 4*60L
    duration = DURATION_DEFAULT

DURATION_MAX = 36*60L
if (duration < 0 or duration > DURATION_MAX):
    print STATUS_400_STR
    print
    print DURATION_STR + "must be positive and less than %s" % (DURATION_MAX)
    debuglog("Bad duration")
    sys.exit(1)

# PARAM Details
DETAILS_STR = 'Details'
if DETAILS_STR in params:
    Details = params.getvalue(DETAILS_STR)
else:
    DETAILS_DEFAULT = ""
    Details = DETAILS_DEFAULT

# PARAM Telephone
TELEPHONE_STR = 'Telephone'
if TELEPHONE_STR in params:
    Telephone = params.getvalue(TELEPHONE_STR)
else:
    TELEPHONE_DEFAULT = ""
    Telephone = TELEPHONE_DEFAULT

# PARAM Email
EMAIL_STR = 'Email'
if EMAIL_STR in params:
    Email = params.getvalue(EMAIL_STR)
else:
    EMAIL_DEFAULT = ""
    Email = EMAIL_DEFAULT

# Created
SQL_DATE_FMT_STR = '%Y-%m-%d %H:%M:%S'
now = datetime.datetime.now()
# Expires
delta = datetime.timedelta(minutes=duration)
expires = now+delta
expiresStr = expires.strftime(SQL_DATE_FMT_STR)

# Ok, try connecting to the server

try:
    con = mdb.connect(g.server, g.username, g.password, g.dbname);
    cur = con.cursor(cursorclass=mdb.cursors.DictCursor)

    # Check if this DeviceId is already at an existing beacon
    COUNT_STR = 'Count'
    cur.execute("SELECT count(1) AS " + COUNT_STR + " FROM devices WHERE DeviceId=%s", (str(DeviceId),))
    row = cur.fetchone()
    # Shouldn't be anything else but just in case ...
    cur.nextset()

    debuglog("Found %d entries in devices with deviceid %s" % (row[COUNT_STR],str(DeviceId)))

    if row[COUNT_STR]>0:
        print STATUS_400_STR
        print
        print "Already at a beacon"
        debuglog("Already at a beacon")
        sys.exit(1)

    # Ok, can proceed.
    # Can this fail??
    debuglog("trying to CALL")
    nInsert1 = cur.execute("CALL addBeacon(%s,%s,%s,%s,%s,%s,%s,%s,@BeaconId);",
                          (str(LatE6),str(LonE6), course, Details, Telephone, Email, expiresStr, str(DeviceId)))

    debuglog("nInsert1 is %d" % (nInsert1))
    
    # Fast forward past the empty result set
    cur.nextset()

    debuglog("fast forwarded")

    nInsert2 = cur.execute("""
SELECT b.BeaconId AS BeaconId,LatE6,LonE6,Course,Details,Telephone,Email,Created,Expires,count(DeviceId) AS Count
FROM devices d INNER JOIN beacons b
ON b.BeaconId=d.BeaconId
WHERE b.BeaconId=@BeaconId
GROUP BY b.BeaconId LIMIT 1;
""")

    debuglog("nInsert2 is %d" % (nInsert2))

    createdRow = cur.fetchone()

    debuglog("got createdRow")

    # Success??
    print "Content-Type: application/json"
    print

    # JSON it out (see the JSONDateTimeEncoder.py)
    print j.dumps(createdRow,cls=jsondte.JSONDateTimeEncoder)
    
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
