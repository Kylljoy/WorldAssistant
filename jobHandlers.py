import sqlite3
import mysql.connector
import socket
import re

from baseEssentials import *

def serveNewJob(cSock, dbConnection, args, characterId):
    #Ensure the given character exists
    cur = dbConnection.cursor()
    cur.execute("SELECT Name FROM Characters WHERE CharacterID = " + str(characterId))
    row = cur.fetchone()
    cur.close()
    if row is None:
        send404(cSock)
        return
    
    if ("name" in args.keys() and "blurb" in args.keys() and "rewards" in args.keys()):
        #Create a New Event

        cur = dbConnection.cursor()
        cur.execute("INSERT INTO Jobs (Name, Blurb, Rewards, CharacterID) VALUES ('" + encodeString(args["name"])[:50] +
            "' , '" + encodeString(args["blurb"])[:200] + "', '" + encodeString(args["rewards"])[:200] +
            "', " + str(characterId) + ")")
        cur.close()
        redirectPage(cSock, "/characters/" + str(characterId))
        return
    else:
        #Read The Template
        page = open("createJob.html")
        pageSource = page.read()
        page.close()

        
        #Update The Info
        pageSource = pageSource.replace("$CHARACTER_NAME", row[0])
        pageSource = pageSource.replace("$JOB_NAME", "Insert Job Name")
        pageSource = pageSource.replace("$JOB_BLURB", "Insert Job Description")
        pageSource = pageSource.replace("$JOB_REWARDS", "Insert Job Rewards")
        pageSource = pageSource.replace("$BACK_URL", "/characters/" + str(characterId))
        pageSource = pageSource.replace("$CHARACTER_ID", str(characterId))



        #Send the Page Over
        cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
        cSock.send(bytes(pageSource, encoding = "utf-8"))
        cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
        cSock.close()

def serveDeleteJob(cSock, dbConnection, jobId):
    #Ensure the given job exists
    cur = dbConnection.cursor()
    cur.execute("SELECT CharacterID FROM Jobs WHERE JobID = " + str(jobId))
    row = cur.fetchone()
    cur.close()
    if row is None:
        send404(cSock)
        return

    cur = dbConnection.cursor()
    cur.execute("DELETE FROM Jobs WHERE JobID = " + str(jobId))
    cur.close()

    if (row is None):
        redirectPage(cSock, "/")
    else:
        redirectPage(cSock, "/characters/" + str(row[0]))


def serveModifyJob(cSock, dbConnection, args, jobId):
    #Ensure the given character exists
    cur = dbConnection.cursor()
    cur.execute("SELECT j.Name, j.Blurb, j.Rewards, j.CharacterID, c.Name FROM Jobs j JOIN Characters c ON j.CharacterID = c.CharacterID WHERE j.JobID = " + str(jobId))
    row = cur.fetchone()
    cur.close()
    if row is None:
        send404(cSock)
        return
    
    if ("name" in args.keys() and "blurb" in args.keys() and "rewards" in args.keys()):
        #Create a New Event

        cur = dbConnection.cursor()
        cur.execute("UPDATE Jobs SET Name = '" + encodeString(args["name"])[:50] +
            "' , Blurb = '" + encodeString(args["blurb"])[:200] + "', Rewards = '" + encodeString(args["rewards"])[:200] +
            "' WHERE JobID = " + str(jobId))
        cur.close()
        redirectPage(cSock, "/jobs/" + str(jobId))
        return
    else:
        #Read The Template
        page = open("createJob.html")
        pageSource = page.read()
        page.close()

        
        #Update The Info
        pageSource = pageSource.replace("$CHARACTER_NAME", row[4])
        pageSource = pageSource.replace("$JOB_NAME", row[0])
        pageSource = pageSource.replace("$JOB_BLURB", row[1])
        pageSource = pageSource.replace("$JOB_REWARDS", row[2])
        pageSource = pageSource.replace("$BACK_URL", "/jobs/" + str(jobId))
        pageSource = pageSource.replace("$CHARACTER_ID", str(row[3]))



        #Send the Page Over
        cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
        cSock.send(bytes(pageSource, encoding = "utf-8"))
        cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
        cSock.close()

def serveJobPage(cSock, dbConnection, jobId):
    #Read The Template
    page = open("jobTemplate.html")
    pageSource = page.read()
    page.close()

    #Build Location Data
    cur = dbConnection.cursor()
    cur.execute("SELECT j.Name, j.Blurb, j.Rewards, j.CharacterID, c.Name FROM Jobs j JOIN Characters c ON c.CharacterID = j.CharacterID WHERE j.JobID = " + str(jobId))
    row = cur.fetchone()
    cur.close()

    if (row):
        pageSource = pageSource.replace("$JOB_NAME", (row[0]))
        pageSource = pageSource.replace("$JOB_BLURB", (row[1]))
        pageSource = pageSource.replace("$JOB_REWARDS", row[2])
        pageSource = pageSource.replace("$CHARACTER_ID", str(row[3]))
        pageSource = pageSource.replace("$CHARACTER_NAME", row[4])
        pageSource = pageSource.replace("$JOB_ID", str(jobId))
    else:
        send404(cSock)
        return
    


    #Send the Page Over
    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
    cSock.send(bytes(pageSource, encoding = "utf-8"))
    cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
    cSock.close()