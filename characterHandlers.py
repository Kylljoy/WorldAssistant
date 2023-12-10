import sqlite3
import mysql.connector
import socket
import re

from baseEssentials import *

def serveCharacterData(cSock, dbConnection, args):
    #Match the partial
    json_out = {"status":"failure"}
    if ("name" in args.keys()):
        json_out["status"] = "success";
        cur = dbConnection.cursor()
        cur.execute("SELECT CharacterID, Name FROM Characters WHERE Name LIKE '" + str(encodeString(args["name"])) + "%'")
        rows = cur.fetchmany(30)
        cur.close()
        if rows is not None:
            json_out["rows"] = len(rows)
            for i in range(0, len(rows)):
                json_out[i] = {"id":rows[i][0], "name":rows[i][1]}

    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type:application/json\r\n\r\n",encoding="utf-8"))
    cSock.send(bytes(json.dumps(json_out), encoding = "utf-8"))
    cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
    cSock.close()

def serveCharacterPage(cSock, dbConnection, characterId):
    #Read The Template
    page = open("characterTemplate.html")
    pageSource = page.read()
    page.close()

    #Build Location Data
    cur = dbConnection.cursor()
    cur.execute("SELECT c.Name, Bio, Species, Stats, l.Name, l.LocationID FROM Characters c JOIN Population p ON c.CharacterID = p.CharacterID JOIN Locations l ON l.LocationID = p.LocationID WHERE c.CharacterID = " + str(characterId))
    row = cur.fetchone()
    cur.close()
    if (row):
        pageSource = pageSource.replace("$CHARACTER_NAME", row[0])
        pageSource = pageSource.replace("$CHARACTER_ID", str(characterId))
        pageSource = pageSource.replace("$CHARACTER_BIO", row[1])
        pageSource = pageSource.replace("$CHARACTER_SPECIES", row[2])
        pageSource = pageSource.replace("$CHARACTER_STATS", row[3])
        pageSource = pageSource.replace("$LOCATION_ID", str(row[5]))
        pageSource = pageSource.replace("$LOCATION_NAME", row[4])

        #Build Event List
        cur = dbConnection.cursor()
        cur.execute("SELECT e.EventID, e.Name, e.Blurb FROM Events e JOIN Participants p ON p.EventID = e.EventID JOIN Characters c ON c.CharacterID = p.CharacterID WHERE c.CharacterID = " + str(characterId))
        eventTable = buildEventTable(cur)
        pageSource = pageSource.replace("$EVENT_LIST", eventTable)
        cur.close()
    else:
        send404(cSock)
        return


    #Send the Page Over
    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
    cSock.send(bytes(pageSource, encoding = "utf-8"))
    cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
    cSock.close()

def serveModifyCharacter(cSock, dbConnection, args, characterId):
     #Build Location Data
    cur = dbConnection.cursor()
    cur.execute("SELECT c.Name, Bio, Species, Stats, l.Name, l.LocationID FROM Characters c JOIN Population p ON c.CharacterID = p.CharacterID JOIN Locations l ON l.LocationID = p.LocationID WHERE c.CharacterID = " + str(characterId))
    row = cur.fetchone()
    cur.close()
    if (row is None):
        send404(cSock)
        return
    if ("name" in args.keys() and "bio" in args.keys() and "stats" in args.keys() and "species" in args.keys()):
        #Create a New Character linked to this location
        cur = dbConnection.cursor()
        cur.execute("UPDATE Characters SET Name = '" + encodeString(args["name"])[:50] + "', Species = '" + encodeString(args["species"])[:30] + "',Bio = '" + encodeString(args["bio"])[:200] + "', Stats = '" + encodeString(args["stats"])[:150] + "' WHERE CharacterID = " + str(characterId))
        cur.close()
        #Redirect
        redirectPage(cSock, "/characters/" + str(characterId))
    else:
        #Read The Template
        page = open("createCharacter.html")
        pageSource = page.read()
        page.close()
        pageSource = pageSource.replace("$CHARACTER_NAME", row[0])
        pageSource = pageSource.replace("$CHARACTER_BIO", row[1])
        pageSource = pageSource.replace("$CHARACTER_SPECIES", row[2])
        pageSource = pageSource.replace("$CHARACTER_STATS", row[3])
        pageSource = pageSource.replace("$LOCATION_ID", str(row[5]))
        pageSource = pageSource.replace("$LOCATION_NAME", row[4])
        pageSource = pageSource.replace("$BACK_URL", "/characters/" + str(characterId))

        #Build Event List
        cur = dbConnection.cursor()
        cur.execute("SELECT e.EventID, e.Name, e.Blurb FROM Events e JOIN Participants p ON p.EventID = e.EventID JOIN Characters c ON c.CharacterID = p.CharacterID WHERE c.CharacterID = " + str(characterId))
        eventTable = buildEventTable(cur)
        pageSource = pageSource.replace("$EVENT_LIST", eventTable)
        cur.close()
        

        #Send the Page Over
        cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
        cSock.send(bytes(pageSource, encoding = "utf-8"))
        cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
        cSock.close()

def serveDeleteCharacter(cSock, dbConnection, characterId):
    #Ensure the given location exists
    cur = dbConnection.cursor()
    cur.execute("SELECT * FROM Characters WHERE CharacterID = " + str(characterId))
    row = cur.fetchone()
    cur.close()
    if row is None:
        send404(cSock)
        return

    cur = dbConnection.cursor()
    cur.execute("SELECT LocationID FROM Population WHERE CharacterID = " + str(characterId))
    row = cur.fetchone()
    cur.close()
    
    cur = dbConnection.cursor()
    cur.execute("CALL purgeCharacter(" + str(characterId) + ")")
    cur.close()

    if (row is None):
        redirectPage(cSock, "/")
    else:
        redirectPage(cSock, "/locations/" + str(row[0]))

def serveNewCharacter(cSock, dbConnection, args, locationId):
    if ("name" in args.keys() and "bio" in args.keys() and "stats" in args.keys() and "species" in args.keys()):
        #Create a New Character linked to this location
        cur = dbConnection.cursor()
        cur.execute("INSERT INTO Characters (Name, Species, Bio, Stats) VALUES ('" + encodeString(args["name"])[:50] + "', '" + encodeString(args["species"])[:30] + "', '" + encodeString(args["bio"])[:200] + "', '" + encodeString(args["stats"])[:150] + "')")
        cur.execute("SELECT MAX(CharacterID) FROM Characters")
        row = cur.fetchone()
        newId = row[0]
        cur.execute("INSERT INTO Population (LocationID, CharacterID) VALUES (" + str(locationId) + ", " + str(newId) + ")")
        cur.close()
        #Redirect
        redirectPage(cSock, "/characters/" + str(newId))
    else:
        #Read The Template
        page = open("createCharacter.html")
        pageSource = page.read()
        page.close()

        #Build Character Data
        cur = dbConnection.cursor()
        cur.execute("SELECT Name FROM Locations WHERE LocationID = " + str(locationId))
        row = cur.fetchone()
        cur.close()
        if (row):
            pageSource = pageSource.replace("$LOCATION_NAME", row[0])
            pageSource = pageSource.replace("$LOCATION_ID", str(locationId))
            pageSource = pageSource.replace("$BACK_URL", "/locations/" + str(locationId))
            pageSource = pageSource.replace("$CHARACTER_SPECIES", "Insert Species")
            pageSource = pageSource.replace("$CHARACTER_NAME", "Insert New Name")
            pageSource = pageSource.replace("$CHARACTER_BIO", "Insert New Bio")
            pageSource = pageSource.replace("$CHARACTER_STATS", "Insert New Stats")
            pageSource = pageSource.replace("$EVENTS_LIST", "<i>None</i>")
        else:
            send404(cSock)
            return


        #Send the Page Over
        cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
        cSock.send(bytes(pageSource, encoding = "utf-8"))
        cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
        cSock.close()

