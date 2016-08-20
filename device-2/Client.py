#!/usr/bin/env python

###############################################################################
##
##  My Sensor UDP Client v1.0
##  @Copyright 2014 MySensors Research Project
##  SCoRe Lab (www.scorelab.org)
##  University of Colombo School of Computing
##
##  Licensed under the Apache License, Version 2.0 (the "License");
##  you may not use this file except in compliance with the License.
##  You may obtain a copy of the License at
##
##      http://www.apache.org/licenses/LICENSE-2.0
##
##  Unless required by applicable law or agreed to in writing, software
##  distributed under the License is distributed on an "AS IS" BASIS,
##  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
##  See the License for the specific language governing permissions and
##  limitations under the License.
##
###############################################################################

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import datetime
import socket
import time
import sys
import thread
import re
import hashlib

import os.path
lib_path = os.path.abspath('../utils')
lib_path = os.path.abspath('../senz')
sys.path.append(lib_path)
from myHandler import *
from myCrypto import *
from myDriver import *
from myCamDriver import *

from senz import *
from myCrypto import *
import hashlib
#from PIL import Image

lib_path1 = os.path.abspath('../')
sys.path.append(lib_path1)
from myConfig import *

#Public key of the SenZ switch
serverPubKey = ""
#Public key of the device
pubkey = ""
aesKeys = {}


class mySensorDatagramProtocol(DatagramProtocol):
  
    def __init__(self, host,port,reactor):
        self.ip= socket.gethostbyname(host)
        self.port = port
        self.state="INITIAL"
        #self._reactor=reactor
        #self.ip=reactor.resolve(host)

    def sendPing(self):
       senze="DATA #msg PING"
       self.sendDatagram(senze)
       reactor.callLater(600,self.sendPing)

    def readSenze(self):
        while True:
             response=raw_input("Enter your Senze:")
             self.sendDatagram(response)

    def startProtocol(self):
        self.transport.connect(self.ip,self.port)
        if self.state=='INITIAL':
           #If system is at the initial state, it will send the device creation Senze
           self.register()
        else:
           #thread.start_new_thread(self.showPhoto,("p1.jpg",))
           #reactor.callLater(5,self.sendPing)
           thread.start_new_thread(self.readSenze,()) 
           #response=raw_input("Enter your Senze:")
           #self.sendDatagram(response)

    def stopProtocol(self):
        #on disconnect
        #self._reactor.listenUDP(0, self)
        print "STOP **************"

    def register(self):
        global server
        global pubkey
        senze ='SHARE #pubkey %s @%s' %(pubkey,server)
        self.sendDatagram(senze)

    def sendDatagram(self, senze):
        global device
        cry = myCrypto(name=device)
        senze = cry.signSENZE(senze)
        print(senze)
        self.transport.write(senze)

    def datagramReceived(self, datagram, host):
        global device
        global server

        print 'Datagram received: ', repr(datagram)
        senz = SenZ(datagram)
        handler=myHandler(self.transport,device,senz)
        cry = myCrypto(device)

        if self.state == "INITIAL":
            if senz.sender==server:
                self.state=handler.registrationDone()
            if self.state=="READY":
                if not bootSenz:
                    reactor.callLater(1,self.readSenze)
                else:
                    for s in bootSenz:
                        reactor.callLater(3,self.sendDatagram,bootSenz[s])
        elif self.state == "READY":
            if serverPubKey != "" and senz.sender == server:
                if cry.verifySENZE(senz,serverPubKey):
                    handler.handleServerResponse(senz)
                else:
                    print ("SENZE Verification failed")
            else:
                if senz.sender != "":
                    recipient = myCrypto(senz.sender)
                    if os.path.isfile(recipient.pubKeyLoc):
                        pub = recipient.loadRSAPubKey()
                    else:
                        pub = ""
                    if pub != "" and cry.verifySENZE(senz,pub):
                        print ("SENZE Verified")
                        handler.handleDeviceResponse(senz)
                    else:
                        print ("SENZE Verification failed")
        else:
            print ("Unknown Sate")




def init():
    #cam=myCamDriver()
    global device
    global pubkey
    global serverPubKey
    global server
    #Here we will generate public and private keys for the device
    #These keys will be used to perform authentication and key exchange
    try:
      cry=myCrypto(name=device)
      #If keys are not available yet
      if not os.path.isfile(cry.pubKeyLoc):
         # Generate or loads an RSA keypair with an exponent of 65537 in PEM format
         # Private key and public key was saved in the .devicenamePriveKey and .devicenamePubKey files
         cry.generateRSA(bits=1024)
      pubkey=cry.loadRSAPubKey()
      print "DEVICE KEY : ", pubkey

    except:
        print "ERRER: Cannot genereate private/public keys for the device."
        raise SystemExit

    #Here we will load the public key of the server
    try:
        cry=myCrypto(name=server)
        #If keys are not available yet
        if os.path.isfile(cry.pubKeyLoc):
            serverPubKey=cry.loadRSAPubKey()
        print "SERVER KEY: ", serverPubKey
    except:
        print "ERRER: Cannot load server public key."
        raise SystemExit

    #Check the network connectivity.
    #check_connectivity(ServerName)

def main():
    global host
    global port
    protocol = mySensorDatagramProtocol(hostName,port,reactor)
    reactor.listenUDP(0, protocol)
    reactor.run()

if __name__ == '__main__':
    init()
    main()
