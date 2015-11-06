"""pypopper: a file-based pop3 server
        source http://code.activestate.com/recipes/534131-pypopper-python-pop3-server/
        mofified by 0x25 11/2015
        info POP3 http://irp.nain-t.net/doku.php/180pop3:020_commandes
Useage:
    python pop3server.py <[host]:port> <path_to_folder_of_messages>
"""

import logging
import os
import socket
import sys
import traceback
from math import ceil

logging.basicConfig(format="%(name)s %(levelname)s - %(message)s")
log = logging.getLogger("pypopper")
#log.setLevel(logging.INFO)
log.setLevel(logging.DEBUG)

delList = {}

class ChatterboxConnection(object):
    END = "\n"
    def __init__(self, conn):
        self.conn = conn
    def __getattr__(self, name):
        return getattr(self.conn, name)
    def sendall(self, data, END=END):
        if len(data) < 50:
            log.debug("send: %r", data)
        else:
            log.debug("send: %r...", data[:50])
        data += END
        self.conn.sendall(data)
    def recvall(self, END=END):
        data = []
        while True:
            chunk = self.conn.recv(2048)
            if END in chunk:
                data.append(chunk[:chunk.index(END)])
                break
            if not chunk:
                break
            if len(data) > 1:
                pair = data[-2] + data[-1]
                if END in pair:
                    data[-2] = pair[:pair.index(END)]
                    data.pop()
                    break
        log.debug("recv: %r", "".join(data))
        return "".join(data)


class Message(object):
    def __init__(self, filename):
                if os.path.exists(filename):

                        msg = open(filename, "r")
                        try:
                                self.data = data = msg.read()
                                self.size = len(data)
                                self.top, bot = data.split("\n\n", 1)
                                self.bot = bot.split("\n")
                        finally:
                                msg.close()

class List(object):
        """return a list of files
        """
        def __init__(self, dir):
                files = {}
                for (i,filename) in enumerate(os.listdir(dir)):
                        files[i+1] = dir+filename

                self.files = files

def handleUser(data, files):
        """always allow user
        """
        log.info("USER")
        return "+OK user accepted"

def handlePass(data, files):
        """always allow password
        """
        log.info("PASS")
        return "+OK pass accepted"

def handleStat(data, files):
        """return number of message and global size
        """

        totalSizeBit = 0L
        for (i,filename) in files.iteritems():
                totalSizeBit = totalSizeBit + os.path.getsize(filename)

        size=len(files)
        totalSizeOctet = int(totalSizeBit/8)
        log.info("STAT")
        return "+OK "+str(size)+" "+str(totalSizeOctet)

def handleList(data, files):
        """return the list of mail <id> <sizeOctet>
        """

        nbFiles = 0
        filesToStr = ""
        size = 0L

        for (i,filename) in files.iteritems():
                size = os.path.getsize(filename)
                filesToStr += str(i)+" "+str(int(size/8))+"\n"

        nbFiles = len(files)
        log.info("LIST")
        return  "+OK "+str(nbFiles)+" messages:\n"+filesToStr+"."


def handleTop(data, files):
        """ header +  ligne
                data : TOP int int
        """
        if len(data.split())== 3:
                cmd, num, lines = data.split()
                lines = int(lines)
                num = int(num)
                if num in files:
                        msg=Message(files[num])
                        text = msg.top + "\r\n\r\n" + "\r\n".join(msg.bot[:lines])
                        log.info("TOP %i %i" % (num,lines))
                        return "+OK top of message follows\r\n%s\r\n." % text
                else:
                        return "-ERR wrong file number."
        else:
                return "-ERR TOP need 3 args : TOP 1 1."



def handleRetr(data, files):
        if len(data.split())== 2:
                cmd, num = data.split()
                num = int(num)
                if num in files:
                        msg=Message(files[num])
                        log.info("message %i sent" % num)
                        return "+OK %i octets\r\n%s\r\n." % (msg.size, msg.data)
                else:
                        return "-ERR no file id."
        else:
                return "-ERR fail args number : RETR int."


def handleDele(data, files):
        global delList
        if len(data.split())== 2:
                cmd, num = data.split()
                num = int(num)
                if num in files:
                        delList[num] = files[num]
                        del files[num]
                        return "+OK %i Marked to be deleted." % num
                else:
                        return "-ERR no file id."
        else:
                return "-ERR fail args."

def handleNoop(data, files):
        return "+OK"

def handleQuit(data, files):
        global delList
        for (i, item) in delList.iteritems():
                os.remove(item)
        return "+OK pypopper2 POP3 server signing off."

def handleRst(data, files):
        global delList
        for (i,name) in delList.iteritems():
                files[i] = name

        delList.clear()
        return "+OK."

dispatch = dict(
    USER=handleUser,
    PASS=handlePass,
    STAT=handleStat,
    LIST=handleList,
    TOP=handleTop,
    RETR=handleRetr,
    DELE=handleDele,
    NOOP=handleNoop,
    QUIT=handleQuit,
    RST=handleRst,
        )

def serve(host, port, dir):
    assert os.path.exists(dir)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    try:
        if host:
            hostname = host
        else:
            hostname = "localhost"
        log.info("pypopper POP3 serving '%s' on %s:%s", dir, hostname, port)
        while True:
            sock.listen(1)
            conn, addr = sock.accept()
            log.debug('Connected by %s', addr)
            try:
                myList = List(dir)
                conn = ChatterboxConnection(conn)
                conn.sendall("+OK pypopper file-based pop3 server ready")
                while True:
                    data = conn.recvall()
                    print str(data)+"\n"
                    if data.strip():
                        command = data.split(None, 1)[0]
                        try:
                                cmd = dispatch[command]
                        except KeyError:
                                conn.sendall("-ERR unknown command")
                        else:
                                conn.sendall(cmd(data, myList.files))
                                if cmd is handleQuit:
                                        break
            finally:
                conn.close()
                msg = None
    except (SystemExit, KeyboardInterrupt):
        log.info("pypopper stopped")
    except Exception, ex:
        log.critical("fatal error", exc_info=ex)
    finally:
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "USAGE: [<host>:]<port> <path_to_folder_of_messages>"
    else:
        _, port, dir = sys.argv
        if ":" in port:
            host = port[:port.index(":")]
            port = port[port.index(":") + 1:]
        else:
            host = ""
        try:
            port = int(port)
        except Exception:
            print "Unknown port:", port
        else:
            if os.path.exists(dir):
                serve(host, port, dir)
            else:
                print "File not found:", dir


