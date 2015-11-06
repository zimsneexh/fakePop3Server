"""http://www.informit.com/articles/article.aspx?p=686162&seqNum=6
"""


import poplib
import sys

path="Maildir/"

if len(sys.argv) != 5:
        print "USAGE:python pop3Client.py host port user password"
else:
        _, server, port, user, password = sys.argv

        mServer = poplib.POP3(server,port)

        #Login to mail server
        mServer.user(user)
        mServer.pass_(password)

        #Get Stat
        msgCount, mailboxSize =  mServer.stat()
        print "currently %i message and %i octet" % (msgCount, mailboxSize)

        #Get the number of mail messages

        response, msgs, octets = mServer.list()
        numMessage = len(msgs)

        for str in msgs:
                num, octet = str.split()
                res, data, size = mServer.retr(int(num))
                print "message %s :" % num
                print "".join(data)
                print "\n"

        mServer.quit()

