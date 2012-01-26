#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb as mdb
import datetime
import sys

import sqlGlobals as g
import sqlPassword as p

con = None

try:
    con = mdb.connect(g.server, g.username, p.password, g.dbname);
    cur = con.cursor(cursorclass=mdb.cursors.DictCursor)

    cur.execute("DROP PROCEDURE IF EXISTS addBeacon;")

    cur.execute(
"""
CREATE PROCEDURE addBeacon
(IN pLatE6 INT,
IN pLonE6 INT,
IN pCourse VARCHAR(255),
IN pWorkingOn VARCHAR(255),
IN pDetails VARCHAR(255),
IN pTelephone VARCHAR(255),
IN pEmail VARCHAR(255),
IN pExpiresStr VARCHAR(255),
IN pDeviceId BIGINT UNSIGNED,
OUT pBeaconId BIGINT UNSIGNED)
MODIFIES SQL DATA
BEGIN
  INSERT INTO beacons
    (LatE6, LonE6, Course, WorkingOn, Details, Telephone, Email, Created, Expires)
  VALUES
    (pLatE6, pLonE6, pCourse, pWorkingOn, pDetails, pTelephone, pEmail, NOW(), pExpiresStr);

  SET pBeaconId=LAST_INSERT_ID();

  INSERT INTO devices
    (DeviceId, BeaconId, Joined)
  VALUES
    (pDeviceId, pBeaconId, NOW());
END
""")

except mdb.Error, e:

    print "Something went wrong!"
    print
    print "Error %d: %s" % (e.args[0],e.args[1])

finally:

    if con:
        con.close()
