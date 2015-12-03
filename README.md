# GoBot
A python XMPP bot that listens to GoCD and posts relevant messages to a room

### Requirements
* Python :)
* You must have the gocd-websocket-notifier plugin installed on your Go server - see https://github.com/matt-richardson/gocd-websocket-notifier

### Install
```
sudo pip install -r requirements.txt
```

### Run
e.g
````
python gobot.py -j eugene@some.jabber.domain -p yourpassword -r roomname@conference.somejabber.domain -n mybotnickname -g my.gocd.domain -s my,stage,names
````

### Docker
Checkout the Dockerfile for running this service in a container ;)

### Credits
* taglines obtained from http://www.textfiles.com
