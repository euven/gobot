# The GoCD bot that posts to an XMPP room
# To build: sudo docker build [--no-cache=true] [--pull=true] --rm=true -t gobot .
# To run e.g: sudo docker run --name=gobot -d gobot -e "JID=myjid@chat" -e "JPASSWD=pwd" -e "JROOM=room" -e "JNICK=nick" -e "GODOMAIN=domain" -e "GOSTAGES=stage,names"


FROM ubuntu:14.04

MAINTAINER Eugene Venter

# install required packages
RUN apt-get update && apt-get -y install git python python-dev python-pip


RUN useradd -ms /bin/bash iamgobot

USER iamgobot
WORKDIR /home/iamgobot

RUN git clone http://github.com/eugeneventer/gobot.git
RUN git config --global user.name gobot
RUN git config --global user.email gobothasnoemail

USER root
RUN pip install -r gobot/requirements.txt

USER iamgobot
ENTRYPOINT ["/bin/bash", "/home/iamgobot/gobot/start_gobot.sh"]
