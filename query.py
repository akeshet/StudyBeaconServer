#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb as mdb
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

# Get the passed CGI parameters
params = cgi.FieldStorage()

# Construct the query

# Get the courses requests
COURSE_STR = "course"
courses = params.getlist(COURSE_STR);

# The string for the course query
if len(courses) > 0:
    coursesOrString = " OR ".join(["Course=%s"]*len(courses))
else:
    coursesOrString = "Course IS NULL"

# Do the following for Lat/Lon
def valOr0(key):
    if key in params:
        return params.getvalue(key)
    else:
        return 0L
    
# Get the lat/long limiting information   
LAT_MIN_STR = "LatE6Min"
LAT_MAX_STR = "LatE6Max"
LON_MIN_STR = "LonE6Min"
LON_MAX_STR = "LonE6Max"

LatE6Min = valOr0(LAT_MIN_STR)
LatE6Max = valOr0(LAT_MAX_STR)
LonE6Min = valOr0(LON_MIN_STR)
LonE6Max = valOr0(LON_MAX_STR)

# The string for the lat/lon query
LatLonString = "LatE6 > %s AND LatE6 < %s AND LonE6 > %s AND LonE6 < %s"

# Here is the prepared query
queryPrep = "SELECT LatE6,LonE6,Course,Details,Contact,Created,Expires,count(DeviceId) AS count FROM devices d INNER JOIN beacons b ON b.BeaconId=d.BeaconId WHERE (%s) AND (%s) GROUP BY b.BeaconId;" % (coursesOrString, LatLonString)


# Put this in a try block because connecting to the server might fail
try:

    con = mdb.connect(g.server, g.username, 
        g.password, g.dbname);

    cur = con.cursor(cursorclass=mdb.cursors.DictCursor)

    cur.execute(queryPrep, tuple(courses)+(LatE6Min,LatE6Max,LonE6Min,LonE6Max))
    rows = cur.fetchall()

    # If we've made it this far, then everything is kosher! Print the results
    # HTTP Header
    # TODO Encoding?
    print "Content-Type: application/json"
    print
    
    # JSON it out (see the JSONDateTimeEncoder.py)
    print j.dumps(rows,cls=jsondte.JSONDateTimeEncoder)
    
except mdb.Error, e:
  
    # This would be in error
    print "Status: 502 Bad Gateway"
    print

    # TODO This is not JSON -- return an error code instead?
    print "Error %d: %s" % (e.args[0],e.args[1])
    sys.exit(1)
    
finally:    
        
    if con:    
        con.close()
