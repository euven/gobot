#!/usr/bin/env python

import sys
import logging
import getpass
from optparse import OptionParser
import json
import random

import sleekxmpp
import websocket

import time

# ensure utf8 encoding
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input


class GoBot(sleekxmpp.ClientXMPP):

    def __init__(self, jabberid, password, room, nick, godomain, stages):
        sleekxmpp.ClientXMPP.__init__(self, jabberid, password)

        self.room = room
        self.nick = nick
        self.godomain = godomain
        self.stages = stages

        self.add_event_handler("session_start", self.start)

        self.add_event_handler("groupchat_message", self.bot_message)

        self.add_event_handler('gocd_listen', self.gocd_listen, threaded=True)

        self.add_event_handler('disconnected', self.gocd_listen_stop)

    def start(self, event):
        self.get_roster()
        self.send_presence()
        self.plugin['xep_0045'].joinMUC(self.room,
                                        self.nick,
                                        wait=True)

        self.event('gocd_listen')

    def bot_message(self, msg):
        # prevent any infinite loops - we don't wanna respond to ourselves :D
        if msg['mucnick'] == self.nick or self.nick not in msg['body']:
            return

        # get random tagline and send :D
        tagfile = open('taglines.txt')
        tagline = next(tagfile)
        for num, aline in enumerate(tagfile):
            if random.randrange(num + 2): continue
            tagline = aline
        tagfile.close()

        self.send_message(mto=msg['from'].bare,
                          mbody=tagline.rstrip(),
                          mtype='groupchat')

    def gocd_listen(self, event):
        failedpipes = []
        def gocd_message(ws, message):
            msg = json.loads(message)
            pipename = msg['pipeline']['name']
            stage = msg['pipeline']['stage']
            if stage['name'] in self.stages:
                golink = 'https://%s/go/tab/pipeline/history/%s' % (self.godomain, pipename)
                if stage['state'] == 'Passed' and pipename in failedpipes:
                    failedpipes.remove(pipename)
                    self.send_message(mto=self.room,
                                      mbody="%s (%s) fixed :) - %s" % (pipename, stage['name'], golink),
                                      mtype='groupchat')
                elif stage['state'] == 'Failed' and pipename not in failedpipes:
                    failedpipes.append(pipename)
                    self.send_message(mto=self.room,
                                      mbody='%s (%s) broken :( - %s' % (pipename, stage['name'], golink),
                                      mtype='groupchat')


        def gocd_error(ws, error):
            logging.error("GOCD ERROR!!!")
            logging.error(error)

        def gocd_close(ws):
            logging.info("### gocd ws closed ###")

        websocket.enableTrace(True)

        self.ws = websocket.WebSocketApp("ws://%s:8887/" % self.godomain,
                                    on_message = gocd_message,
                                    on_error = gocd_error,
                                    on_close = gocd_close)

        sleepsecs = 60
        while (1):
            try:
                self.ws.run_forever()
                logging.error("Trying websocket reconnect in %s seconds" % sleepsecs)
                time.sleep(sleepsecs)
            except:
                logging.error("Unexpected error:", sys.exc_info()[0])
                logging.error("Trying websocket reconnect in %s seconds" % sleepsecs)
                time.sleep(sleepsecs)

    def gocd_listen_stop(self, event):
        self.ws.close()


if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()

    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option("-j", "--jabberid", dest="jabberid",
                    help="Jabber ID")
    optp.add_option("-p", "--password", dest="password",
                    help="password")
    optp.add_option("-n", "--nick", dest="nick",
                    help="Nickname")
    optp.add_option("-r", "--room", dest="room",
                    help="Room to join")
    optp.add_option("-g", "--godomain", dest="godomain",
                    help="GoCD domain to connect to")
    optp.add_option("-s", "--stages", dest="stages",
                    help="comma-seperated list of stage names to report on")

    opts, args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jabberid is None:
        opts.jabberid = raw_input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")
    if opts.nick is None:
        opts.nick = raw_input("Nickname: ")
    if opts.room is None:
        opts.room = raw_input("Room: ")

    xmpp = GoBot(opts.jabberid, opts.password, opts.room, opts.nick, opts.godomain, opts.stages.split(','))
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0045') # Multi-User Chat
    xmpp.register_plugin('xep_0199') # XMPP Ping

    if xmpp.connect():
        xmpp.process(block=True)
    else:
        logging.error("Failed to connect to XMPP...")
