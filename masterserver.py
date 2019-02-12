import socket
import threading
import datetime
import time
import traceback

SERVERS = [{"ip": "163.158.182.243", "port": 19711, "last":datetime.datetime.now()}, {"ip": "73.181.147.35", "port": 19711, "last": datetime.datetime.now()}]

def main():
    listen_ip = "0.0.0.0"

    registersock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    registersock.bind((listen_ip, 27900))
    print("Listening on", listen_ip, 27900)

    querysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    querysock.bind((listen_ip, 28900))
    print("Listening on", listen_ip, 28900)
    querysock.listen(5)

    registerthread = threading.Thread(target=registerloop, args=(registersock,))
    querythread = threading.Thread(target=queryloop, args=(querysock,))
    cleanthread = threading.Thread(target=cleanloop)

    querythread.start()
    registerthread.start()
    cleanthread.start()

    querythread.join()
    registerthread.join()
    cleanthread.join()


def queryloop(querysock):
    while True:
        (clientsocket, (_, _)) = querysock.accept()
        print("A new client has come")
        b = b''
        for i in range(len(SERVERS)):
            b += "{:02d}".format(i).encode("ascii")
            b += b'\xac'
            b += SERVERS[i]["ip"].encode("ascii")
            b += b'\xac'
            b += str(SERVERS[i]["port"]).encode("ascii")
            b += b'\x00'
        print("Sending back", b)
        clientsocket.send(b)

def registerloop(registersock):
    while True:
        data, (ip, port) = registersock.recvfrom(1024)
        try:
            gameport = data[1:].decode("ascii")
            if int(gameport):
                tempsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                tempsocket.settimeout(5)
                tempsocket.sendto("\\status\\".encode("ascii"), (ip, port))
                tempsocket.recvfrom(1024)
                server = next((x for x in SERVERS if x["ip"] == ip and x["port"] == gameport), None)
                if not server:
                    SERVERS.append({"ip": ip, "port": gameport, "last": datetime.datetime.now()})
                    print("New server: %s:%s" % (ip, gameport))
                else:
                    server["last"] = datetime.datetime.now()
                    print("Keepalive from: %s:%s" % (ip, gameport))
                tempsocket.close()
            else:
                print("Fuck it, wasn't int: ", data)
        except Exception as e:
            print("Exception")
            traceback.print_exc()

def cleanloop():
    while True:
        now = datetime.datetime.now()
        for server in SERVERS:
            if now > server["last"] + datetime.timedelta(minutes=2):
                if server["ip"] == "163.158.182.243" or server["ip"] == "73.181.147.35":
                    # do not remove usual dedicated servers
                    continue
                print("Deleting %s:%s" % (server["ip"], server["port"]))
                try:
                    SERVERS.remove(server)
                except ValueError:
                    pass
        time.sleep(10)


if __name__ == '__main__':
    main()