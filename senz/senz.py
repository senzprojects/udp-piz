###############################################################################
##
##  Senze parser for My Senosr Server/Client v0.01
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
import sys
import re
import os
sys.path.append(os.path.abspath('../utils'))
from myCrypto import *


class SenZ(object):

    """
    Keep senz message attributes in here. Senz parser will be generates this
    type of object when datagram recives.
    """
    def __init__(self,msg):
        self.users=list()
        self.sensors=list()
        self.command=""
        self.data={}
        self.sender=""
        self.signature=""
        self.senze=""
        self.fullSenze=msg

        tList=msg.split()
        state='CLEAR'
        sen=""
        commandList=["SHARE","UNSHARE","PUT","GET","DATA"]
        #print msg

        while tList:
            word=tList.pop(0)
            self.senze+=word

            if word.upper() in commandList:
                self.command=word
            elif word.startswith("#"):
                sen=word[1:]
                if not sen in self.sensors:
                    self.sensors.append(sen)
                state='DATA'
            elif word.startswith("@"):
                usr=word[1:]
                if not usr in self.users:
                    self.users.append(word[1:])
            elif word.startswith("^"):
                self.sender=word[1:]
                self.signature=tList.pop(0)
            else:
                if state=='DATA':
                    self.data[sen]=word
                    state='CLEAR'
                    #print word

    def getUsers(self):
        #     print re.findall(r'(?<=\W)[@]\S*',self.msg)
        return self.users

    def getSensors(self):
        return self.sensors

    def getData(self):
        return self.data

    def getCmd(self):
        return self.command

    def getSender(self):
        return self.sender

    def getSENZE(self):
        return self.senze

    def getFULLSENZE(self):
        return self.fullSenze

    def getSignature(self):
        return self.signature

#testData=["SHARE #pubkey LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlHZk1BMEdDU3FHU0liM0RRRUJBUVVBQTRHTkFEQ0JpUUtCZ1FDbit1eVpzcXIxeS93Y2hjTkh1MzducE5RSwpSRHFBOTl6REkxeUtzOTFLNUJvNWFKWG1qOXc2cUJwdnVPdkNZQUxHcEdXVC9NUm1Ka3pLOGZUclJhVFlyY1ZMCkJsbklkMXVneWUzZDJFM3lBRFREZlNWWGlOZXpKS2MrSkErN0ExV25FZ0tacXB6ZmYvalNhZXgrR25YcWZ5d0cKeVQvR201QnhwdTc2SXFkYU9RSURBUUFCCi0tLS0tRU5EIFBVQkxJQyBLRVktLS0tLQ== @mysensors ^home0 iT4zN85/JNaWiDw56gLqYFDpf6dwkfUOIkP/QlGvLOz4PF7KgJOhefEfH8xQXBmLQAOq3blIVuHIZC55CqTFevfovLcy4Ff42VEFAqMqj42Z3cmoApxgU6tzs/V5BjlrmQAry2TGQ0Qx18uqJANjuyvxMTMMwpiWRK1GM5jZch4="]
'''
testData=["SHARE #pubkey XXXXXXX #time t1 @mysensors ^kasun yyyyyyyyyy",
"DATA #msg ErrorCode @home0 #time t3 ^mysensors XXXXXXXXX",
"DATA #time t1 @mysensors ^kasun YYYYYY",
"SHARE #pubkey XXXXXXX #time t1 @home0 ^kasun yyyyyyyyyy",
"DATA #msg OK @home0 #time t3 ^kasun XXXXXXXXX",
"SHARE #gpio10 @kasun #time t2 ^home0 YYYYYYYYYYY",
"SHARE #lat #lon @home0 #time 2 ^kasun YYYYYYYYYYY",
"PUT #gpio10 ON @home0 #time t3 ^kasun XXXXXXXXX",
"DATA #gpio10 ON @kasun #time t4 ^home0 YYYYYYYYYYYYY",
"GET #lat #lon @kasun #time t3 ^home0 XXXXXXXXX",
"DATA #lat x #lon y @home0 #time t4 ^kasun YYYYYYYYYYYYY",
"PUT #cipher XXXgpio10ON @home0 #time t3 ^kasun XXXXXXXXX",
"DATA #cipher xxxgpio10ON @kasun #time t4 ^home0 YYYYYYYYYYYYY",
"GET #cipher xxxlatlon @kasun #time t3 ^home0 XXXXXXXXX"]

for l in testData:
  m= SenZ(l)

  print "User List: ",m.getUsers()
  print "Sensors: ", m.getSensors()
  print "Data: ", m.getData()
  print "Commands: ", m.getCmd()
  print "Sender: ", m.getSender()
  print "Sender: ", m.getSENZE()
  print "Signature:",m.getSignature()
  print "-------------------------"
  raw_input()
'''