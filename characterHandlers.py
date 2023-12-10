import sqlite3
import mysql.connector
import socket
import re

def serveCharacterPage(cSock, dbConnection, characterId):
    #Read The Template
    page = open("characterTemplate.html")
    pageSource = page.read()
    page.close()

    #Build Location Data
    cur = dbConnection.cursor()
    cur.execute("SELECT Name, Bio FROM Characters WHERE CharacterID = " + str(characterId))
    row = cur.fetchone()
    cur.close()
    if (row):
        pageSource = pageSource.replace("$CHARACTER_NAME", row[0])
        pageSource = pageSource.replace("$CHARACTER_BIO", row[1])
    else:
        send404(cSock)
        return


    #Send the Page Over
    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
    cSock.send(bytes(pageSource, encoding = "utf-8"))
    cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
    cSock.close()
