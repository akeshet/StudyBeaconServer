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

con = None

# DEBUG Turn this off when done debugging
cgitb.enable(display=0, logdir=".")

# The 400 error code
STATUS_400_STR = "Status: 400 Bad Request"

# Get the passed CGI parameters
params = cgi.FieldStorage()

# Check that we have all the required inputs we need
COURSE_STR = "course"
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
    sys.exit(1)

if (DeviceId < 0):
    print STATUS_400_STR
    print
    print "Invalid DeviceId"
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
    sys.exit(1)

# PARAM Details
DETAILS_STR = 'Details'
if DETAILS_STR in params:
    Details = params.getvalue(DETAILS_STR)
else:
    DETAILS_DEFAULT = ""
    Details = DETAILS_DEFAULT

# PARAM Contact
CONTACT_STR = 'Contact'
if CONTACT_STR in params:
    Contact = params.getvalue(CONTACT_STR)
else:
    CONTACT_DEFAULT = ""
    Contact = CONTACT_DEFAULT

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
    cur.execute("SELECT count(1) AS count FROM devices WHERE DeviceId=%s", (DeviceId))
    row = cur.fetchone()
    # Shouldn't be anything else but just in case ...
    cur.nextset()

    if row['count']>0:
        print STATUS_400_STR
        print
        print "Already at a beacon"
        sys.exit(1)

    # Ok, can proceed.
    # Can this fail??
    nInsert = cur.execute("INSERT INTO beacons (LatE6, LonE6, Course, " +
                          "Details, Contact, Created, Expires) " +
                          "VALUES (%s, %s, %s, %s, %s, now(), %s); " +
                          "INSERT INTO devices (DeviceId, BeaconId, Joined) " +
                          "VALUES (%s, LAST_INSERT_ID(), now()); " +
                          "SELECT b.BeaconId AS BeaconId,LatE6,LonE6,Course,Details,Contact," +
                          "Created,Expires,count(DeviceId) AS count " +
                          "FROM devices d INNER JOIN beacons b " +
                          "ON b.BeaconId=d.BeaconId " +
                          "WHERE b.BeaconId=LAST_INSERT_ID() " +
                          "GROUP BY b.BeaconId LIMIT 1;",
                          (LatE6, LonE6, course, Details, Contact, expiresStr, DeviceId))
    
    # Fast forward past the two insert statements
    cur.nextset()
    cur.nextset()

    createdRow = cur.fetchone()

    # Success??
    print "Content-Type: application/json"
    print

    # JSON it out (see the JSONDateTimeEncoder.py)
    print j.dumps(createdRow,cls=jsondte.JSONDateTimeEncoder)
    
except mdb.Error, e:

    print "Status: 502 Bad Gateway"
    print
    print "Error %d: %s" % (e.args[0],e.args[1])
    sys.exit(1)

finally:

    if con:
        con.close()

# # Do the following for Lat/Lon
# def valOr0(key):
#     if key in params:
#         return params.getvalue(key)
#     else:
#         return 0L
    
# # Get the lat/long limiting information   
# LAT_MIN_STR = "LatE6Min"
# LAT_MAX_STR = "LatE6Max"
# LON_MIN_STR = "LonE6Min"
# LON_MAX_STR = "LonE6Max"

# LatE6Min = valOr0(LAT_MIN_STR)
# LatE6Max = valOr0(LAT_MAX_STR)
# LonE6Min = valOr0(LON_MIN_STR)
# LonE6Max = valOr0(LON_MAX_STR)

# # The string for the lat/lon query
# LatLonString = "LatE6 > %s AND LatE6 < %s AND LonE6 > %s AND LonE6 < %s"

# # Here is the prepared query
# queryPrep = ("SELECT LatE6,LonE6,Course,Details,Contact,Created,Expires,count(DeviceId)" 
#              + " AS count FROM devices d INNER JOIN beacons b ON b.BeaconId=d.BeaconId "
#              + "WHERE (%s) AND (%s) GROUP BY b.BeaconId;" % (coursesOrString, LatLonString))


# # Put this in a try block because connecting to the server might fail
# try:

#     con = mdb.connect(g.server, g.username, g.password, g.dbname);

#     cur = con.cursor(cursorclass=mdb.cursors.DictCursor)

#     cur.execute(queryPrep, tuple(courses)+(LatE6Min,LatE6Max,LonE6Min,LonE6Max))
#     rows = cur.fetchall()

#     # If we've made it this far, then everything is kosher! Print the results
#     # HTTP Header
#     # TODO Encoding?
#     print "Content-Type: application/json"
#     print
    
#     # JSON it out (see the JSONDateTimeEncoder.py)
#     print j.dumps(rows,cls=jsondte.JSONDateTimeEncoder)
    
# except mdb.Error, e:
  
#     # This would be in error
#     print "Status: 502 Bad Gateway"
#     print

#     print "Error %d: %s" % (e.args[0],e.args[1])
#     sys.exit(1)
    
# finally:    
        
#     if con:    
#         con.close()
