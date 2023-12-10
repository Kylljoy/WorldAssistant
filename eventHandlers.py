import sqlite3
import mysql.connector
import socket
import re

from baseEssentials import *

def serveTimeline(cSock, dbConnection):
    cur = dbConnection.cursor()
    cur.execute("SELECT * FROM Timeline")
    row = cur.fetchone()
    rowCount = 0
    timelineString = "<tr>"
    while (row):
        timelineString += "<td onclick='window.location.replace(\"/events/" + str(row[0]) + "\")' class='timeline-event'><div class='timeline-event-name'>" + row[3] + "</div><div class='timeline-event-date'>" + str(row[4]) + "/" + str(row[5]) + "/" + str(row[6]) + "</div>" + row[2] + "</td>"
        rowCount += 1
        if (rowCount >= 3):
            rowCount = 0
            timelineString += "</tr><tr>"
        row = cur.fetchone()
    cur.close()
    timelineString += "</tr>"
    page = open("timelineTemplate.html")
    pageSource = page.read()
    page.close()
    pageSource = pageSource.replace("$TIMELINE", timelineString)

    #Send the Page Over
    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
    cSock.send(bytes(pageSource, encoding = "utf-8"))
    cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
    cSock.close()
    
    

def serveNewEvent(cSock, dbConnection, args, locationId):
    #Ensure the given location exists
    cur = dbConnection.cursor()
    cur.execute("SELECT Name FROM Locations WHERE LocationID = " + str(locationId))
    row = cur.fetchone()
    cur.close()
    if row is None:
        send404(cSock)
        return
    
    if ("name" in args.keys() and "blurb" in args.keys()):
        #Create a New Event
        cur = dbConnection.cursor()
        cur.execute("INSERT INTO Events (Name, Blurb, LocationID) VALUES ('" + args["name"] + "' , '" + args["blurb"] + "', " + str(locationId) + ')')
        cur.execute("SELECT MAX(EventID) FROM Events")
        row = cur.fetchone()
        cur.close()
        if (row):
            currentIndex = 0
            #Add all our wonderful participants
            cur = dbConnection.cursor()
            eventId = row[0]
            while (("p" + str(currentIndex)) in args.keys()):
                cur.execute("INSERT INTO Participants (EventID, CharacterID) VALUES (" + str(eventId) + ", " + str(args["p" + str(currentIndex)]) + ')')
                currentIndex += 1
            cur.close()
            redirectPage(cSock, "/locations/" + str(locationId))
        else:
            send404(cSock)
        return
    else:
        #Read The Template
        page = open("createEvent.html")
        pageSource = page.read()
        page.close()

        #Update The Info
        pageSource = pageSource.replace("$LOCATION_NAME", row[0])
        pageSource = pageSource.replace("$EVENT_NAME", "Insert New Name")
        pageSource = pageSource.replace("$EVENT_BLURB", "Insert New Blurb")
        pageSource = pageSource.replace("$BACK_URL", "/locations/" + str(locationId))
        pageSource = pageSource.replace("$PARTICIPANTS", "")
        pageSource = pageSource.replace("$DATE", "0")
        pageSource = pageSource.replace("$MONTH", "0")
        pageSource = pageSource.replace("$YEAR", "0")



        #Send the Page Over
        cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
        cSock.send(bytes(pageSource, encoding = "utf-8"))
        cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
        cSock.close()

def serveModifyEvent(cSock, dbConnection, args, eventId):
    #Ensure the given location exists
    cur = dbConnection.cursor()
    cur.execute("SELECT e.Name, e.Blurb, e.LocationID, l.Name, e.Date, e.Month, e.Year FROM Events e JOIN Locations l ON l.LocationID = e.LocationID WHERE e.EventID = " + str(eventId))
    row = cur.fetchone()
    cur.close()

    if row is None:
        send404(cSock)
        return
    
    if ("name" in args.keys() and "blurb" in args.keys() and "date" in args.keys() and "month" in args.keys() and "year" in args.keys()):
        #Create a New Event
        cur = dbConnection.cursor()
        cur.execute("UPDATE Events SET Name = '" + args["name"] + "' , Blurb = '" + 
            args["blurb"] + "', Date = " + str(args["date"]) + ", Month = " + str(args["month"]) + 
            ", Year = " + str(args["year"]) + " WHERE EventID = " + str(eventId))
        cur.execute("DELETE FROM Participants WHERE EventID = " + str(eventId))
        currentIndex = 0
        #Add all our wonderful participants
        cur = dbConnection.cursor()
        while (("p" + str(currentIndex)) in args.keys()):
            cur.execute("INSERT INTO Participants (EventID, CharacterID) VALUES (" + str(eventId) + ", " + str(args["p" + str(currentIndex)]) + ')')
            currentIndex += 1
        cur.close()
        redirectPage(cSock, "/events/" + str(eventId))
        return
    else:
        #Read The Template
        page = open("createEvent.html")
        pageSource = page.read()
        page.close()



        #Update The Info
        pageSource = pageSource.replace("$LOCATION_NAME", row[3])
        pageSource = pageSource.replace("$EVENT_NAME", row[0])
        pageSource = pageSource.replace("$EVENT_BLURB", row[1])
        pageSource = pageSource.replace("$BACK_URL", "/events/" + str(eventId))
        pageSource = pageSource.replace("$DATE", str(row[4]))
        pageSource = pageSource.replace("$MONTH", str(row[5]))
        pageSource = pageSource.replace("$YEAR", str(row[6]))

        #Add Existing Participants
        participants = []
        cur = dbConnection.cursor()
        cur.execute("SELECT c.Name, p.CharacterID FROM Participants p JOIN Characters c ON c.CharacterID = p.CharacterID WHERE p.EventID = " + str(eventId))
        row = cur.fetchone()
        while row:
            participants.append("[" + row[0].__repr__() + ", " + str(row[1]) + "]")
            row = cur.fetchone()
        cur.close()
        pageSource = pageSource.replace("$PARTICIPANTS", ",".join(participants))



        #Send the Page Over
        cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
        cSock.send(bytes(pageSource, encoding = "utf-8"))
        cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
        cSock.close()

def serveDeleteEvent(cSock, dbConnection, eventId):
    #Ensure the given location exists
    cur = dbConnection.cursor()
    cur.execute("SELECT * FROM Events WHERE EventID = " + str(eventId))
    row = cur.fetchone()
    cur.close()
    if row is None:
        send404(cSock)
        return

    cur = dbConnection.cursor()
    cur.execute("SELECT LocationID FROM Events WHERE EventID = " + str(eventId))
    row = cur.fetchone()
    cur.close()
    
    cur = dbConnection.cursor()
    cur.execute("CALL purgeEvent(" + str(eventId) + ")")
    cur.close()

    if (row is None):
        redirectPage(cSock, "/")
    else:
        redirectPage(cSock, "/locations/" + str(row[0]))

def serveEventPage(cSock, dbConnection, eventId):
      #Read The Template
    page = open("eventTemplate.html")
    pageSource = page.read()
    page.close()

    #Build Location Data
    cur = dbConnection.cursor()
    cur.execute("SELECT e.Name, e.Blurb, e.LocationID, l.Name, e.Date, e.Month, e.Year FROM Events e JOIN Locations l ON l.LocationID = e.LocationID WHERE e.EventID = " + str(eventId))
    row = cur.fetchone()
    cur.close()

    if (row):
        pageSource = pageSource.replace("$EVENT_NAME", (row[0]))
        pageSource = pageSource.replace("$EVENT_BLURB", decodeString(row[1]))
        pageSource = pageSource.replace("$LOCATION_ID", str(row[2]))
        pageSource = pageSource.replace("$LOCATION_NAME", row[3])
        pageSource = pageSource.replace("$DATE", str(row[4]))
        pageSource = pageSource.replace("$MONTH", str(row[5]))
        pageSource = pageSource.replace("$YEAR", str(row[6]))
        pageSource = pageSource.replace("$EVENT_ID", str(eventId))
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