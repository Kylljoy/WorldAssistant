import sqlite3
import mysql.connector
import socket
import re

from baseEssentials import *

def serveNewEvent(cSock, dbConnection, locationId):
    None

def serveEventPage(cSock, dbConnection, eventId):
      #Read The Template
    page = open("eventTemplate.html")
    pageSource = page.read()
    page.close()

    #Build Location Data
    cur = dbConnection.cursor()
    cur.execute("SELECT e.Name, e.Blurb, e.LocationID, l.Name FROM Events e JOIN Locations l ON l.LocationID = e.LocationID WHERE e.EventID = " + str(eventId))
    row = cur.fetchone()
    cur.close()

    if (row):
        pageSource = pageSource.replace("$EVENT_NAME", (row[0]))
        pageSource = pageSource.replace("$EVENT_BLURB", decodeString(row[1]))
        pageSource = pageSource.replace("$LOCATION_ID", str(row[2]))
        pageSource = pageSource.replace("$LOCATION_NAME", row[3])
    else:
        send404(cSock)
        return
    
    #Build the Character Table
    cur = dbConnection.cursor()
    cur.execute("SELECT c.CharacterID, c.Name, c.Bio FROM Characters c JOIN Participants p ON p.CharacterID = c.CharacterID JOIN Events e ON e.EventID = p.EventID WHERE e.EventID = " + str(eventId))
    characterTable = buildCharacterTable(cur)
    pageSource = pageSource.replace("$CHARACTER_LIST", characterTable)
    cur.close()


    #Send the Page Over
    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
    cSock.send(bytes(pageSource, encoding = "utf-8"))
    cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
    cSock.close()