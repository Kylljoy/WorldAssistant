import sqlite3
import mysql.connector
import socket
import random
import re
import webbrowser
import traceback

from baseEssentials import *
from locationHandlers import *
from characterHandlers import *
from eventHandlers import *
from jobHandlers import *

dbConnection = mysql.connector.connect( host="localhost",
                                        user="app",
                                        password="dbAccess",
                                        database="worldAssistant")

fileMap = {"html" : "text/html", "js" : "a", "css":"text/css", "jpeg":"image/jpeg", "gif" : "image/gif", "png": "image/png", "txt":"text/plain", "ico":"image/vnd.microsoft.icon "}
port = 8080

def serveIndex(cSock):
    #Read The Template
    page = open("index.html")
    pageSource = page.read()
    page.close()

    #Send the Page Over
    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
    cSock.send(bytes(pageSource, encoding = "utf-8"))
    cSock.send(bytes("\r\n\r\n", encoding = "utf-8"))
    cSock.close()


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
                elif (len(path) == 2 and path[1] == "new"):
                    serveNewMasterLocation(cSock, dbConnection, args)
                elif (len(path) >= 2 and path[1].isdigit()):
                    if (len(path) == 3):
                        if (path[2] == "new"):
                            serveNewSublocation(cSock, dbConnection, args, int(path[1]))
                        elif (path[2] == "delete"):
                            serveDeleteLocation(cSock, dbConnection, int(path[1]))
                        elif (path[2] == "modify"):
                            serveModifyLocation(cSock, dbConnection,  args, int(path[1]))
                        elif (path[2] == "newcharacter"):
                            serveNewCharacter(cSock, dbConnection,  args, int(path[1]))
                        elif (path[2] == "newevent"):
                             serveNewEvent(cSock, dbConnection,  args, int(path[1]))
                        else:
                            send404(cSock)
                    
                    elif (len(path) == 2):
                        serveLocationPage(cSock, dbConnection, int(path[1]))
                    else:
                        send404(cSock)
                else:
                    send404(cSock)
            elif (path[0] == "characters" and len(path) <= 3):
                if (len(path) == 1):
                    send404(cSock)
                elif (path[1].isdigit()):
                    if (len(path) == 3):
                        if (path[2] == "modify"):
                            serveModifyCharacter(cSock, dbConnection, args, int(path[1]))
                        elif (path[2] == "delete"):
                            serveDeleteCharacter(cSock, dbConnection, int(path[1]))
                        elif (path[2] == "newjob"):
                            serveNewJob(cSock, dbConnection, args, int(path[1]))
                        else:
                            send404(cSock)
                    else:
                        serveCharacterPage(cSock, dbConnection, int(path[1]))
                else:
                    send404(cSock)
            elif (path[0] == "events" and len(path) <= 3):
                if (len(path) == 1):
                    serveTimeline(cSock, dbConnection)
                elif(path[1].isdigit()):
                    if (len(path) == 2):
                        serveEventPage(cSock, dbConnection, int(path[1]))
                    if (len(path) == 3):
                        if (path[2] == "modify"):
                            serveModifyEvent(cSock, dbConnection, args, int(path[1]))
                        elif (path[2] == "delete"):
                            serveDeleteEvent(cSock, dbConnection, int(path[1]))
                        else:
                            send404(cSock)
                else:
                    send404(cSock)

            elif (path[0] == "info"):
                if (len(path) == 1):
                    send404(cSock)
                else:
                    if(path[1] == "location"):
                        serveLocationData(cSock, dbConnection, args)
                    if(path[1] == "character"):
                        serveCharacterData(cSock, dbConnection, args)
                    else:
                        send404(cSock)
            elif (path[0] == "jobs"):
                if (len(path) == 1):
                    send404(cSock)
                elif (len(path) <= 3 and path[1].isdigit()):
                    if (len(path) == 2):
                        serveJobPage(cSock, dbConnection, int(path[1]))
                    elif (path[2] == "modify"):
                        serveModifyJob(cSock, dbConnection, args, int(path[1]))
                    elif (path[2] == "delete"):
                        serveDeleteJob(cSock, dbConnection, int(path[1]))
                    else:
                        send404(cSock)
                else:
                    send404(cSock)
            elif (fileName == "/"):
                serveIndex(cSock)
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
            traceback.print_tb(e.__traceback__)
            
        
            
        
