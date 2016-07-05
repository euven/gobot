#!/usr/bin/env python

import os
import sys
import logging
import getpass
import argparse
import json
import random

import sleekxmpp
import websocket

import time

# ensure utf8 encoding
if sys.version_info < (3, 0):
    reload(sys)  # noqa
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
        self.plugin['xep_0045'].joinMUC(self.room, self.nick, wait=True)
        self.event('gocd_listen')

    def bot_message(self, msg):
        # prevent any infinite loops - we don't wanna respond to ourselves :D
        if msg['mucnick'] == self.nick or self.nick not in msg['body']:
            return

        # get random tagline and send :D
        tagfile = open('taglines.txt')
        tagline = next(tagfile)
        for num, aline in enumerate(tagfile):
            if random.randrange(num + 2):
                continue
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
                golink = 'https://{domain}/go/tab/pipeline/history/{pipe}'.format(
                    domain=self.godomain, pipe=pipename)
                if stage['state'] == 'Passed' and pipename in failedpipes:
                    failedpipes.remove(pipename)
                    self.send_message(
                        mto=self.room,
                        mbody="{pipe} ({stage}) fixed :) - {link}".format(
                            pipe=pipename, stage=stage['name'], link=golink),
                        mtype='groupchat')
                elif stage['state'] == 'Failed' and pipename not in failedpipes:
                    failedpipes.append(pipename)
                    self.send_message(
                        mto=self.room,
                        mbody='{pipe} ({stage}) broken :( - {link}'.format(
                            pipe=pipename, stage=stage['name'], link=golink),
                        mtype='groupchat')

        def gocd_error(ws, error):
            logging.error("GOCD ERROR!!!")
            logging.error(error)

        def gocd_close(ws):
            logging.info("### gocd ws closed ###")

        websocket.enableTrace(True)

        self.ws = websocket.WebSocketApp("ws://{domain}:8887/".format(domain=self.godomain),
                                         on_message=gocd_message,
                                         on_error=gocd_error,
                                         on_close=gocd_close)

        sleepsecs = 60
        while (1):
            try:
                self.ws.run_forever()
                logging.error("Trying websocket reconnect in {} seconds".format(sleepsecs))
                time.sleep(sleepsecs)
            except:
                logging.error("Unexpected error:", sys.exc_info()[0])
                logging.error("Trying websocket reconnect in {} seconds".format(sleepsecs))
                time.sleep(sleepsecs)

    def gocd_listen_stop(self, event):
        self.ws.close()


if __name__ == '__main__':
    # Setup the command line arguments.
    argp = argparse.ArgumentParser(description="GoCD bot")

    argp.add_argument('-q', '--quiet', help='set logging to ERROR',
                      action='store_const', dest='loglevel',
                      const=logging.ERROR, default=logging.INFO)
    argp.add_argument("-j", "--jabberid", dest="jabberid",
                      help="Jabber ID")
    argp.add_argument("-p", "--password", dest="password",
                      help="password (insecure, use env variable GOBOT_PASSWORD instead)")
    argp.add_argument("-n", "--nick", dest="nick",
                      help="Nickname")
    argp.add_argument("-r", "--room", dest="room",
                      help="Room to join")
    argp.add_argument("-g", "--godomain", dest="godomain",
                      help="GoCD domain to connect to")
    argp.add_argument("-s", "--stages", dest="stages",
                      help="comma-seperated list of stage names to report on")

    args = argp.parse_args()

    # Setup logging.
    logging.basicConfig(level=args.loglevel,
                        format='%(levelname)-8s %(message)s')

    if args.jabberid is None:
        args.jabberid = raw_input("Username: ")
    if args.password is None:
        if os.environ.get('GOBOT_PASSWORD'):
            args.password = os.environ.get('GOBOT_PASSWORD')
        else:
            args.password = getpass.getpass("Password: ")
    if args.nick is None:
        args.nick = raw_input("Nickname: ")
    if args.room is None:
        args.room = raw_input("Room: ")

    xmpp = GoBot(args.jabberid, args.password, args.room, args.nick, args.godomain, args.stages.split(','))
    xmpp.register_plugin('xep_0030')  # Service Discovery
    xmpp.register_plugin('xep_0045')  # Multi-User Chat
    xmpp.register_plugin('xep_0199')  # XMPP Ping

    if xmpp.connect():
        xmpp.process(block=True)
    else:
        logging.error("Failed to connect to XMPP...")
