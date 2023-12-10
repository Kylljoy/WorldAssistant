import sqlite3
import mysql.connector
import socket
import random
import re
import webbrowser

from baseEssentials import *
from locationHandlers import *
from characterHandlers import *

dbConnection = mysql.connector.connect( host="localhost",
                                        user="app",
                                        password="dbAccess",
                                        database="worldAssistant")

fileMap = {"html" : "text/html", "css":"text/css", "jpeg":"image/jpeg", "gif" : "image/gif", "png": "image/png", "txt":"text/plain", "ico":"image/vnd.microsoft.icon "}
port = 8080
#Builds an HTML Table Object From Cursor Result C

def redirectTo(cSock, url):
    cSock.send(bytes("<script>window.location.replace(\"" + url + "\");</script>", encoding = 'utf-8'))

def stripFormatting(s):
    i = 0
    o = s[::]
    while i < len(o):
        if (o[i] == "%"):
            if (o[i + 1 : i + 3] != '0D'):
                if (o[i + 1 : i + 3] == "0A"):
                    o = o[:i] + "\n" + o[i+3:]
                else:
                    o = o[:i] + chr(int(o[i + 1 : i + 3], base = 16)) + o[i+3:]
            else:
                o = o[:i] + o[i + 3:]
                continue
        if (o[i] == "+"):
            o = o[:i] + " " + o[i + 1:]
        i += 1
    return o




def addPopulation(cSock, args):
    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
    page = open("populationCreate.html",'r')
    text = page.read()
    optionsIndex = text.find("$OPTIONS$")
    
    page.close()
    cSock.send(bytes(text[:optionsIndex], encoding = 'utf-8'))
    cur = dbConnection.cursor()
    cur.execute("SELECT LocationID, Name FROM Locations")
    row = cur.fetchone()
    while row:
        cSock.send(bytes("<option value='"+str(row[0])+"'>"+row[1]+"</option>", encoding = 'utf-8'))
        row = cur.fetchone()
    cur.close()
    cSock.send(bytes(text[optionsIndex + 9:], encoding = 'utf-8'))
    if len(args.keys()) == 5:
        name = repr(args["name"])
        species = repr(args["species"])
        stats = repr(args["stats"])
        bio = repr(args["bio"])
        locationId = int(args["location"])
        cur = dbConnection.cursor()
        query = "INSERT INTO Characters SELECT MAX(CharacterID) + 1, "+ ",".join([name, species, stats, bio]) + " FROM Characters"
        print(query)
        cur.execute(query)
        if (locationId > 0):
            cur.execute("INSERT INTO Population SELECT "+ str(locationId) +", MAX(CharacterID) FROM Characters")
        cur.close()
        print(query)
        #cur.execute()
    cSock.close();




def indexPage(cSock, args):
    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
    index = open("index.html",'r')
    text = index.read()
    tableInsertIndex = text.find("$TABLE$")
    table = ""
    cSock.send(bytes(text[:tableInsertIndex], encoding = 'utf-8'))
    cSock.send(bytes(text[(tableInsertIndex + 7):], encoding = 'utf-8'))
    index.close()

    cSock.send(bytes("\r\n\r\n",encoding="utf-8"))
    cSock.close()

# Server Handling Code
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
success = False
while not success:
    try:
        server.bind(("localhost", port))
        success = True
    except OSError:
        port = 8000 + random.randint(1,1000)
webbrowser.open("localhost:" + str(port) + "/")
server.listen(5)
cSock = None
while True:
        try:
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
            #print(header)
            #print("\n\nFilename = " + fileName)
            args = {}
            if argMatches:
                #print("\n\nArgString = " + header[argMatches.start() + 1 : argMatches.end()])
                argString = header[argMatches.start() + 1 : argMatches.end()]
                argsList = argString.split("&")
                for pair in argsList:
                    values = pair.split("=")
                    if (len(values) > 1):
                        key = stripFormatting(values[0])
                        value = stripFormatting(values[1])
                        args[key] = value
            path = fileName.split("/")[1:]
            print("\n\nArgs =" + str(args))
            print("\n\nPath = " + " / ".join(path))
            suffix = fileName.split(".")[-1]


            #Location Handlers
            if (path[0] == "locations"):
                if (len(path) == 1):
                    serveMasterLocation(cSock, dbConnection)
                    #Master Location List
                elif (path[1] == "new"):
                    serveNewMasterLocation(cSock, dbConnection, args)
                elif (path[1].isdigit()):
                    if (len(path) > 2):
                        if (path[2] == "new"):
                            serveNewSublocation(cSock, dbConnection, args, int(path[1]))
                        elif (path[2] == "delete"):
                            serveDeleteLocation(cSock, dbConnection, int(path[1]))
                        elif (path[2] == "modify"):
                            serveModifyLocation(cSock, dbConnection,  args, int(path[1]))
                        elif (path[2] == "newcharacter"):
                            serveNewCharacter(cSock, dbConnection,  args, int(path[1]))
                        else:
                            send404(cSock)
                    
                    else:
                        serveLocationPage(cSock, dbConnection, int(path[1]))
                else:
                    send404(cSock)
            elif (path[0] == "characters"):
                if (len(path) == 1):
                    cSock.close()
                elif (path[1].isdigit()):
                    if (len(path) > 2):
                        if (path[2] == "modify"):
                            serveModifyCharacter(cSock, dbConnection, args, int(path[1]))
                        if (path[2] == "delete"):
                            serveDeleteCharacter(cSock, dbConnection, int(path[1]))
                        else:
                            send404(cSock)
                    else:
                        serveCharacterPage(cSock, dbConnection, int(path[1]))
                else:
                    send404(cSock)
            elif (fileName == "/"):
                cSock.close()
            elif (".." not in fileName and suffix != "py" and suffix != "db"):
                try:
                    newFile = open(fileName[1:], "rb")
                    
                    contentType = "text/plain"
                    if (suffix in fileMap.keys()):
                        contentType = fileMap[suffix]
                    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: " + contentType + "\r\n\r\n", encoding = "utf- 8"))
                    cSock.send(newFile.read())
                    cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
                    newFile.close()
                    cSock.close()
                except FileNotFoundError:
                    send404(cSock)
            else:
                send404(cSock)
        except KeyboardInterrupt:
            print("Shutting Down...")
            cSock.close()
            server.close()
            break
        except BrokenPipeError:
            cSock.close()
            None
        except Exception as e:
            print("Critical Exception: " + e.__repr__())
            print(e.__traceback__.__repr__())
            cSock.close()
            server.close()
            print("Server Closed!")
            break
        
            
        
