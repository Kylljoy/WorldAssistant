import sqlite3
import mysql.connector
import socket
import re

dbConnection = mysql.connector.connect(
                                        host="localhost",
                                        user="app",
                                        password="dbAccess",
                                        database="worldAssistant")

#Builds an HTML Table Object From Cursor Result C
def buildTable(cSock, cur):
    cSock.send(bytes("<table>", encoding = 'utf-8'))
    cSock.send(bytes("<tr>", encoding = 'utf-8'))
    for column in cur.description:
        cSock.send(bytes("<th>", encoding = 'utf-8'))
        cSock.send(bytes(column[0], encoding = 'utf-8'))
        cSock.send(bytes("</th>", encoding = 'utf-8'))
    cSock.send(bytes("<tr>", encoding = 'utf-8'))
    row = cur.fetchone()
    while row:
        cSock.send(bytes("<tr>", encoding = 'utf-8'))
        for value in row:
            cSock.send(bytes("<td>"+str(value)+"</td>", encoding = 'utf-8'))
        cSock.send(bytes("</tr>", encoding = 'utf-8'))
        row = cur.fetchone()
    cur.close()
    cSock.send(bytes("</table>", encoding = 'utf-8'))

#Build Location Table
def buildLocationTable(cSock, cur):
    cSock.send(bytes("<table>", encoding = 'utf-8'))
    cSock.send(bytes("<tr>", encoding = 'utf-8'))
    for column in ["Name", "Blurb", "Actions"]:
        cSock.send(bytes("<th>", encoding = 'utf-8'))
        cSock.send(bytes(column, encoding = 'utf-8'))
        cSock.send(bytes("</th>", encoding = 'utf-8'))
    cSock.send(bytes("<tr>", encoding = 'utf-8'))
    row = cur.fetchone()
    while row:
        cSock.send(bytes("<tr>", encoding = 'utf-8'))
        for value in row[1:3]:
            cSock.send(bytes("<td>"+str(value)+"</td>", encoding = 'utf-8'))
        cSock.send(bytes("<td>"+"<a href='/sublocations?id="+ str(row[0])+"'>Sublocations</a>  <a href='/population?id="+ str(row[0])+"'>Characters</a>"+"</td>", encoding = 'utf-8'))
        cSock.send(bytes("</tr>", encoding = 'utf-8'))
        row = cur.fetchone()
    cur.close()
    cSock.send(bytes("</table>", encoding = 'utf-8'))

    

def stripFormatting(s):
    i = 0
    o = s[::]
    while i < len(o):
        if (o[i] == "%"):
            if (o[i + 1 : i + 3] != '0D'):
                o = o[:i] + chr(int(o[i + 1 : i + 3], base = 16)) + o[i+3:]
            else:
                o = o[:i] + o[i + 3:]
                continue
        if (o[i] == "+"):
            o = o[:i] + " " + o[i + 1:]
        i += 1
    return o

def locationSearch(cSock, args):
    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
    page = open("locationSearch.html",'r')
    text = page.read()
    page.close()
    tableInsertIndex = text.find("$TABLE$")
    table = ""
    cSock.send(bytes(text[:tableInsertIndex], encoding = 'utf-8'))
    if len(args.keys()) > 0:
        partial = args["name"]
        partial = repr(partial)[1:-1]
        cur = dbConnection.cursor()
        cur.execute("SELECT * FROM Locations WHERE Name LIKE \"%" + partial + "%\"")
        buildLocationTable(cSock, cur)
        None
    cSock.send(bytes(text[(tableInsertIndex + 7):], encoding = 'utf-8'))
    cSock.close();


def sublocationSearch(cSock, args):
    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
    page = open("sublocationSearch.html",'r')
    text = page.read()
    page.close()
    tableInsertIndex = text.find("$TABLE$")
    table = ""
    cSock.send(bytes(text[:tableInsertIndex], encoding = 'utf-8'))
    if len(args.keys()) > 0:
        i = args["id"]
        cur = dbConnection.cursor()
        print("CALL findAllSublocations(" + i + ")")
        cur.execute("CALL findAllSublocations(" + i + ")")
        cur.execute("SELECT l.locationID, l.Name, l.Blurb  FROM Locations l JOIN allSublocations s ON l.LocationID = s.ChildID")
        buildLocationTable(cSock, cur)
        None
    cSock.send(bytes(text[(tableInsertIndex + 7):], encoding = 'utf-8'))
    cSock.close();

def populationSearch(cSock, args):
    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
    page = open("sublocationSearch.html",'r')
    text = page.read()
    page.close()
    tableInsertIndex = text.find("$TABLE$")
    table = ""
    cSock.send(bytes(text[:tableInsertIndex], encoding = 'utf-8'))
    if len(args.keys()) > 0:
        i = args["id"]
        cur = dbConnection.cursor()
        cur.execute("CALL findLocalPopulation(" + i + ")")
        cur.execute("SELECT * FROM localPopulation")
        buildTable(cSock, cur)
        None
    cSock.send(bytes(text[(tableInsertIndex + 7):], encoding = 'utf-8'))
    cSock.close();



def indexPage(cSock, args):
    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
    index = open("index.html",'r')
    text = index.read()
    tableInsertIndex = text.find("$TABLE$")
    table = ""
    cSock.send(bytes(text[:tableInsertIndex], encoding = 'utf-8'))
    if len(args.keys()) > 0:
        cur = dbConnection.cursor()
        cur.execute("SELECT * FROM Locations")
        buildTable(cSock, cur)
    cSock.send(bytes(text[(tableInsertIndex + 7):], encoding = 'utf-8'))
    index.close()

    cSock.send(bytes("\r\n\r\n",encoding="utf-8"))
    cSock.close()

# Server Handling Code
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("localhost", 8061))
server.listen(5)

while True:
        (cSock, addr) = server.accept()
        st = b''
        while True:
            s = cSock.recv(1024)
            if s:
                st += s
                if (len(s) < 1024):
                    break
            else:
                break
        header = st.decode("utf-8")
        header = header[:header.find("\r\n\r\n")]
        header = header[:header.find("\r\n")]
        regEx = re.compile("GET [^\s\?]*")
        argsregEx = re.compile("\?[\S]*")
        matches = regEx.match(header)
        argMatches = argsregEx.search(header)
        if matches == None:
            cSock.close()
            continue
        fileName = header[matches.start() + 4 : matches.end()]
        print(header)
        print("\n\nFilename = " + fileName)
        args = {}
        if argMatches:
            print("\n\nArgString = " + header[argMatches.start() + 1 : argMatches.end()])
            argString = header[argMatches.start() + 1 : argMatches.end()]
            argsList = argString.split("&")
            for pair in argsList:
                values = pair.split("=")
                key = stripFormatting(values[0])
                value = stripFormatting(values[1])
                args[key] = value

        print("\n\nArgs = " + str(args))
        if (fileName == "/locations"):
            locationSearch(cSock, args)
        elif(fileName == "/sublocations"):
            sublocationSearch(cSock, args)
        elif(fileName == "/population"):
            populationSearch(cSock, args)
        else:
            indexPage(cSock, args)
