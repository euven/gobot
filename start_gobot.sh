#!/bin/bash

# first, ensure git repo is up to date
cd /home/iamgobot/gobot && git pull
python gobot.py -j $JID -p $JPASSWD -r $JROOM -n $JNICK -g $GODOMAIN -s $GOSTAGES
