import random

def send404(cSock):
    cSock.send(bytes("HTTP/1.1 404 File Not Found \r\nServer: WorldAssistant\r\nContent-Type: text/html \r\n\r\n", encoding = "utf=8"))
    page = open("404.html","r")
    text = page.read()
    message = random.choice(["ARMAGEDDON!", 
                            "RAGNAROK!",
                            "THE END TIMES ARE HERE!",
                            "THE DARK LORD HAS RISEN!",
                            "THE BLACK HOLE DRAWS NEAR!",
                            "THE DARK RAPTURE HAS BEGUN!",
                            "THE SKY CRIES BLOOD!",
                            "THE GODS HAVE LEFT US!",
                            "THE TWELFTH HOUR DRAWS NEAR",
                            "THE REAPER LURKS NEARBY!",
                            "THE EYE OF SAURON HAS TAKEN NOTICE!",
                            "CYBERPSYCHOSIS!",
                            "SAVING THROW FAILED!"])
    text = text.replace("$TITLE", message)
    cSock.send(bytes(text, encoding="utf-8"))
    cSock.send(bytes("\r\n\r\n", encoding="utf-8"))
    page.close()
    cSock.close()

def encodeString(s):
    out = s.replace("\\","\\\\")
    out = out.replace("\"", "\\\"")
    out = out.replace("\'", "\\\'")
    return out

def decodeString(s):
    out = s.replace("\n", "<br>")
    return out
    

def redirectPage(cSock, url):
    cSock.send(bytes("HTTP/1.1 200 Document follows \r\nServer: World Assistant\r\nContent-Type: text/html\r\n\r\n",encoding="utf-8"))
    cSock.send(bytes("<!DOCTYPE html><body></body><script>window.location.replace(\"" + url + "\");</script></html>", encoding="utf-8"))
    cSock.send(bytes("\r\n\r\n", encoding="utf-8"))
    cSock.close()

locationBlurbWidth = 50
def buildEventTable(cur):
    row = cur.fetchone()
    if (row):
        locationTable = "<table class='nameList'>"
        while row:
            blurb = row[2][:30] + ("..." if len(row[2]) > 30 else "")
            locationTable += "<tr><td><a href='/events/"+str(row[0])+"'>" + row[1] + "</a></td><td>" + blurb + "</td></tr>"
            row = cur.fetchone()
        locationTable += "</table>"
        return locationTable
    return ""

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
