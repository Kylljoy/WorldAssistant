import sqlite3
import mysql.connector
import socket
import re

import json

from baseEssentials import *


locationBlurbWidth = 50
def buildLocationTable(cur):
    row = cur.fetchone()
    if (row):
        locationTable = "<table class='nameList'>"
        while row:
            blurb = row[2][:locationBlurbWidth] + ("..." if len(row[2]) > locationBlurbWidth else "")
            locationTable += "<tr><td><a href='/locations/"+str(row[0])+"'>" + row[1] + "</a></td><td>" + blurb + "</td></tr>"
            row = cur.fetchone()
        locationTable += "</table>"
        return locationTable
    return ""


def buildCharacterTable(cur):
    row = cur.fetchone()
    if (row):
        locationTable = "<table class='nameList'>"
        while row:
            blurb = row[2][:30] + ("..." if len(row[2]) > 30 else "")
            locationTable += "<tr><td><a href='/characters/"+str(row[0])+"'>" + row[1] + "</a></td><td>" + blurb + "</td></tr>"
            row = cur.fetchone()
        locationTable += "</table>"
        return locationTable
    return ""

locationPathWidth = 60
def buildLocationPath(dbConnection, locationId):
    cur = dbConnection.cursor()
    cur.execute("CALL findLocationPath(" + str(locationId) + ")")
    cur.execute("SELECT * FROM locationPath ORDER BY LocationID")
    rows = cur.fetchall()
    cur.close()
    rowCount = len(rows)
    perLocWidth = max(locationPathWidth // (1 + rowCount), 1)
    locationPath = "<a href='/locations'>" + "Locations"[:perLocWidth] + (".." if perLocWidth < 9 else "") + "</a> &rarr; "
    for row in rows[:-1]:
        label = decodeString(row[1])[:perLocWidth] + (".." if perLocWidth < len(row[1]) else "")
        locationPath += "<a href='/locations/" + str(row[0]) + "'>" + label + "</a> &rarr; "
    row = rows[-1]
    locationPath += decodeString(row[1])
    cur.close()
    return locationPath

def serveLocationData(cSock, dbConnection, args):
    #Match the partial
    json_out = {"status":"failure"}
    if ("name" in args.keys()):
        json_out["status"] = "success";
        cur = dbConnection.cursor()
        cur.execute("SELECT LocationID, Name FROM Locations WHERE Name LIKE '" + str(encodeString(args["name"])) + "%'")
        rows = cur.fetchmany(30)
        cur.close()
        if rows is not None:
            json_out["rows"] = len(rows)
            for i in range(0, len(rows)):
                json_out[str(i)] = {"id":rows[i][0], "name":rows[i][1]}

    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type:application/json\r\n\r\n",encoding="utf-8"))
    cSock.send(bytes(json.dumps(json_out), encoding = "utf-8"))
    cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
    cSock.close()


def serveDeleteLocation(cSock, dbConnection, locationId):
    #Ensure the given location exists
    cur = dbConnection.cursor()
    cur.execute("SELECT * FROM Locations WHERE LocationID = " + str(locationId))
    row = cur.fetchone()
    cur.close()
    if row is None:
        send404(cSock)
        return

    cur = dbConnection.cursor()
    cur.execute("SELECT ParentID FROM Sublocations WHERE ChildID = " + str(locationId))
    row = cur.fetchone()
    cur.close()
    
    cur = dbConnection.cursor()
    cur.execute("CALL purgeLocation(" + str(locationId) + ")")
    cur.close()

    if (row is None):
        redirectPage(cSock, "/locations")
    else:
        redirectPage(cSock, "/locations/" + str(row[0]))

def serveModifyLocation(cSock, dbConnection, args, locationId):
    #Ensure the given location exists
    cur = dbConnection.cursor()
    cur.execute("SELECT * FROM Locations WHERE LocationID = " + str(locationId))
    row = cur.fetchone()
    cur.close()
    if row is None:
        send404(cSock)
        return

    if ("name" in args.keys() and "blurb" in args.keys()):
        
        #Redirect
        cur = dbConnection.cursor()
        cur.execute("UPDATE Locations SET Name='" + encodeString(args["name"])[:100] + "', Blurb='" + encodeString(args["blurb"])[:200] + "' WHERE LocationID = " + str(locationId)) 
        cur.close()
        redirectPage(cSock, "/locations/" + str(locationId))
        return
    else:
        #Read The Template
        page = open("createLocation.html")
        pageSource = page.read()
        page.close()

        #Update The Info
        pageSource = pageSource.replace("$LOCATION_NAME", row[1])
        pageSource = pageSource.replace("$LOCATION_BLURB", row[2])
        pageSource = pageSource.replace("$BACK_URL", "/locations/" + str(locationId))

        #Build Sublocation List
        cur = dbConnection.cursor()
        cur.execute("SELECT l.LocationID, l.Name, l.Blurb FROM Locations l JOIN Sublocations s ON s.ChildID = l.LocationID WHERE s.ParentID = " + str(locationId))
        sublocationTable = buildLocationTable(cur)
        pageSource = pageSource.replace("$SUBLOCATION_LIST", sublocationTable)
        cur.close()

        #Build Character List
        cur = dbConnection.cursor()
        cur.execute("SELECT c.CharacterID, c.Name, c.Bio FROM Characters c JOIN Population p ON p.CharacterID = c.CharacterID WHERE p.LocationID = " + str(locationId))
        sublocationTable = buildCharacterTable(cur)
        pageSource = pageSource.replace("$CHARACTER_LIST", sublocationTable)
        cur.close()


        #Send the Page Over
        cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
        cSock.send(bytes(pageSource, encoding = "utf-8"))
        cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
        cSock.close()

def serveMasterLocation(cSock, dbConnection):
    #Read The Template
    page = open("locationsMasterList.html")
    pageSource = page.read()
    page.close()

    #Build Location List
    cur = dbConnection.cursor()
    cur.execute("CALL findAllMasterLocations()")
    cur.execute("SELECT LocationID, Name, Blurb FROM allMasterLocations")
    locationTable = buildLocationTable(cur)
    cur.close()
    locationTable += "</table>"
    pageSource = pageSource.replace("$LOCATION_TABLE", locationTable)

    #Send the Page Over
    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
    cSock.send(bytes(pageSource, encoding = "utf-8"))
    cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
    cSock.close()

def serveNewMasterLocation(cSock, dbConnection, args):
    
    if ("name" in args.keys() and "blurb" in args.keys()):
        #Create a New Location
        cur = dbConnection.cursor()
        cur.execute("INSERT INTO Locations (Name, Blurb) VALUES ('" + encodeString(args["name"])[:100] + "' , '" + encodeString(args["blurb"])[:200] +"')")
        cur.close()

        #Redirect
        redirectPage(cSock, "/locations")
    else:
        #Read The Template
        page = open("createLocation.html")
        pageSource = page.read()
        page.close()

        #Update The Info
        pageSource = pageSource.replace("$LOCATION_NAME", "Insert New Name")
        pageSource = pageSource.replace("$LOCATION_BLURB", "Insert New Blurb")
        pageSource = pageSource.replace("$CHARACTER_LIST", "<i>None</i>")
        pageSource = pageSource.replace("$EVENT_LIST", "<i>None</i>")
        pageSource = pageSource.replace("$SUBLOCATION_LIST", "<i>None</i>")
        pageSource = pageSource.replace("$BACK_URL", "/locations")



        #Send the Page Over
        cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
        cSock.send(bytes(pageSource, encoding = "utf-8"))
        cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
        cSock.close()

def serveNewSublocation(cSock, dbConnection, args, parentLocation):
    #Ensure the given location exists
    cur = dbConnection.cursor()
    cur.execute("SELECT * FROM Locations WHERE LocationID = " + str(parentLocation))
    row = cur.fetchone()
    cur.close()
    if row is None:
        send404(cSock)
        return

    if ("name" in args.keys() and "blurb" in args.keys()):
        #Create a New Location
        cur = dbConnection.cursor()
        cur.execute("INSERT INTO Locations (Name, Blurb) VALUES ('" + encodeString(args["name"])[:100] + "' , '" + encodeString(args["blurb"])[:200] +"')")
        cur.close()

        #Add the Sublocation
        cur = dbConnection.cursor()
        cur.execute("INSERT INTO Sublocations SELECT " + str(parentLocation) +", MAX(LocationID) FROM Locations")
        cur.close()

        #Redirect
        redirectPage(cSock, "/locations/" + str(parentLocation))
    else:
        #Read The Template
        page = open("createLocation.html")
        pageSource = page.read()
        page.close()

        #Update The Info
        pageSource = pageSource.replace("$LOCATION_NAME", "Insert New Name")
        pageSource = pageSource.replace("$LOCATION_BLURB", "Insert New Blurb")
        pageSource = pageSource.replace("$CHARACTER_LIST", "<i>None</i>")
        pageSource = pageSource.replace("$EVENT_LIST", "<i>None</i>")
        pageSource = pageSource.replace("$SUBLOCATION_LIST", "<i>None</i>")
        pageSource = pageSource.replace("$BACK_URL", "/locations/" + str(parentLocation))



        #Send the Page Over
        cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
        cSock.send(bytes(pageSource, encoding = "utf-8"))
        cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
        cSock.close()

def serveLocationPage(cSock, dbConnection, locationId):
    #Read The Template
    page = open("locationTemplate.html")
    pageSource = page.read()
    page.close()

    #Build Location Data
    cur = dbConnection.cursor()
    cur.execute("SELECT Name, Blurb FROM Locations WHERE LocationID = " + str(locationId))
    row = cur.fetchone()
    cur.close()
    if (row):
        pageSource = pageSource.replace("$LOCATION_NAME", (row[0]))
        pageSource = pageSource.replace("$LOCATION_BLURB", decodeString(row[1]))
        pageSource = pageSource.replace("$LOCATION_ID", str(locationId))
    else:
        send404(cSock)
        return

    #Build Location Path
    locationPath = buildLocationPath(dbConnection, locationId)
    pageSource = pageSource.replace("$LOCATION_PATH", locationPath)
    
    #Build Sublocation List
    cur = dbConnection.cursor()
    cur.execute("SELECT l.LocationID, l.Name, l.Blurb FROM Locations l JOIN Sublocations s ON s.ChildID = l.LocationID WHERE s.ParentID = " + str(locationId))
    sublocationTable = buildLocationTable(cur)
    pageSource = pageSource.replace("$SUBLOCATION_LIST", sublocationTable)
    cur.close()

    #Build Character List
    cur = dbConnection.cursor()
    cur.execute("SELECT c.CharacterID, c.Name, c.Bio FROM Characters c JOIN Population p ON p.CharacterID = c.CharacterID WHERE p.LocationID = " + str(locationId))
    sublocationTable = buildCharacterTable(cur)
    pageSource = pageSource.replace("$CHARACTER_LIST", sublocationTable)
    cur.close()



    #Send the Page Over
    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
    cSock.send(bytes(pageSource, encoding = "utf-8"))
    cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
    cSock.close()