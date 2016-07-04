# The GoCD bot that posts to an XMPP room
# To build: sudo docker build [--no-cache=true] [--pull=true] --rm=true -t gobot .
# To run e.g: sudo docker run --name=gobot -d gobot -e "JID=myjid@chat" -e "JPASSWD=pwd" -e "JROOM=room" -e "JNICK=nick" -e "GODOMAIN=domain" -e "GOSTAGES=stage,names"

FROM ubuntu:16.04

MAINTAINER Eugene Venter

# install required packages
RUN apt-get update && \
    apt-get -y install python python-dev python-pip && \
    apt-get clean && \
    rm -rf /tmp/* /var/tmp/* /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash iamgobot

ADD . /gobot
RUN pip install -r /gobot/requirements.txt

USER iamgobot
WORKDIR /gobot
CMD ["/bin/sh", "/gobot/start_gobot.sh"]
