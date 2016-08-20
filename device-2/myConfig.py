import ConfigParser as cp

config = cp.RawConfigParser()
config.read('./config.cfg')

hostName=config.get("switch","switch-uri")
port=config.getint("switch","port")
server=config.get("switch","switch-name")

owner=config.get("device","owner-name")
device=config.get("device","device-name")

#Senzies to be sent at the start
bootSenz={}
if config.has_section("senz"):
    senzies=config.items("senz")
    for s in senzies:
        #print ports[0],ports[1]
        bootSenz[s[0]]=s[1]


GPIO=False
sws={}
if config.has_section("gpio"):
   GPIO=True
   gpioPorts=config.items("gpio")
   for ports in gpioPorts:
       #print ports[0],ports[1]
       sws[ports[0]]=int(ports[1])

#print 'Switch-URL',host
#print 'Port Number',port
#print state
#print 'Switch Name',server
#print 'Owner Name',userName
#print 'Device Name',homeName
if GPIO: print 'GPIO ports',gpioPorts
#print dstate
