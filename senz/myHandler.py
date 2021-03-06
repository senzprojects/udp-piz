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
import os.path
lib_path = os.path.abspath('../utils')
sys.path.append(lib_path)
lib_path = os.path.abspath('../drivers')
sys.path.append(lib_path)
from myCrypto import *
from myDriver import *
from myCamDriver import *

from senz import *

buf=''
aesKeys={}

class myHandler(DatagramProtocol):
  
    def __init__(self,transport,device,senz):
        self.tp= transport
        self.senz = senz
        self.device=device
        #self._reactor=reactor
        #self.ip=reactor.resolve(host)

    def saveRootKey(self,capubkey):
        cry = myCrypto(name=self.senz.sender)
        cry.saveRSAPubKey(capubkey)

    def registrationDone(self):
        cry = myCrypto(name=self.device)
        state="INITIAL"
        if 'msg' in self.senz.sensors and 'pubkey' in self.senz.sensors:
            if cry.verifySENZE(self.senz,self.senz.data['pubkey']):
                if 'REG_DONE' in self.senz.data['msg']:
                    self.saveRootKey(self.senz.data['pubkey'])
                    state='READY'
                    print (self.device + " was created at the server.")
                    print ("You should execute the program again with READY state.")
                elif 'REG_ALR' in self.senz.data['msg']:
                    print (self.device + " was already created at the server.")
                    state="READY"
                else:
                    print ("This user name is already taken")
                    print ("You can try it again with different username")
                    print ("The system halted!")
            else:
                print ("SENZE Verification failed")
        else:
            print ("Unknown server response")
        return state

    def sendDatagram(self, senze):
        cry = myCrypto(name=self.device)
        senze = cry.signSENZE(senze)
        print(senze)
        self.tp.write(senze)

    #Senze response should be built as follows by calling the functions in the driver class
    def sendDataSenze(self,sensors,data,recipient):
        response='DATA'
        driver=myDriver()
        cry=myCrypto(self.device)
        for sensor in sensors:
            #If temperature is requested
            if "tp" == sensor:
                response ='%s #tp %s' %(response,driver.readTp())
            #If AES key is requested
            elif "key" == sensor:
                if recipient not in aesKeys:
                    aeskey=""
                    #Generate AES Key
                    if cry.generateAES(driver.readTime()):
                        aeskey=cry.key
                        #Save AES key
                        aesKeys[recipient]=aeskey
                else:
                    aeskey=aesKeys[recipient]
                #AES key is encrypted by the recipient public key
                rep=myCrypto(recipient)
                encKey=rep.encryptRSA(b64encode(aeskey))
                response ='%s #key %s' %(response,encKey)

            #If photo is requested
            elif "photo" == sensor:
                cam=myCamDriver()
                cam.takePhoto()
                photo=cam.readPhotob64()

                response ='%s #photo ON @%s' %(response,recipient)
                self.sendDatagram(response)
                n = 256
                res=[photo[k:k+n] for k in xrange(0, len(photo),n)]
                for s in res:
                    response='DATA #photo %s @%s' %(s,recipient)
                    self.sendDatagram(response)
                response ='DATA #photo OFF'

            #If time is requested
            elif "time" == sensor:
                response ='%s #time %s' %(response,driver.readTime())

            #If gps is requested
            elif "gps" == sensor:
                #if AES key is available, gps data will be encrypted
                gpsData='%s' %(driver.readGPS())
                if recipient in aesKeys:
                    rep=myCrypto(recipient)
                    rep.key=aesKeys[recipient]
                    gpsData=rep.encrypt(gpsData)
                response ='%s #gps %s' %(response,gpsData)

            #If gpio is requested
            elif "gpio" in sensor:
                m=re.search(r'\d+$',sensor)
                pinnumber=int(m.group())
                print pinnumber
                response ='%s #gpio%s %s' %(response,pinnumber,driver.readGPIO(port=pinnumber))

            else:
                response ='%s #%s NULL' %(response,sensor)
       
        response="%s @%s" %(response,recipient)
        self.sendDatagram(response)


    #Handle the GPIO ports by calling the functions in the driver class
    def handlePUTSenze(self,sensors,data,recipient):
       response='DATA'
       driver=myDriver()
       cry=myCrypto(self.device)
       for sensor in sensors:
          #If GPIO operation is requested
          if "gpio" in sensor:
              pinnumber=0
              #search for gpio pin number
              m=re.search(r'\d+$',sensor)
              if m :
                 pinnumber=int(m.group())
            
              if pinnumber>0 and pinnumber<=16:
                 if data[sensor]=="ON":
                     ans=driver.handleON(port=pinnumber)
                 else:
                     ans=driver.handleOFF(port=pinnumber)
                 response='%s #gpio%s %s' %(response,pinnumber,ans)
              else: 
                 response='%s #gpio%d UnKnown' %(response,pinnumber)
          elif "time" in sensors:
              print "Received time :",data["time"]
          else:
              response='%s #%s UnKnown' %(response,sensor)
       print "******",response
       response="%s @%s" %(response,recipient)
       self.sendDatagram(response)


    def handleServerResponse(self,senz):
        data=senz.getData()
        sensors=senz.getSensors()
        cmd=senz.getCmd()
 
        if cmd=="DATA":
           if 'msg' in sensors and 'UserRemoved' in data['msg']:
              cry=myCrypto(self.device)
              try:
                 os.remove(cry.pubKeyLoc)
                 os.remove(cry.privKeyLoc)
                 print "Device was successfully removed"
              except OSError:
                 print "Cannot remove user configuration files"

           elif 'pubkey' in sensors and data['pubkey']!="" and 'name' in sensors and data['name']!="":
                 recipient=myCrypto(data['name'])
                 if recipient.saveRSAPubKey(data['pubkey']):
                    print "Public key=> "+data['pubkey']+" Saved."
                 else:
                    print "Error: Saving the public key."


    def handleDeviceResponse(self,senz):
        sender=senz.getSender()
        data=senz.getData()
        sensors=senz.getSensors()
        cmd=senz.getCmd()
        global buf,aesKeys
        if cmd=="DATA":
            for sensor in sensors:
                print sensor+"=>"+data[sensor]
       
                if sensor=='photo':
                    if data['photo']=='ON':
                        buf=''
                    elif data['photo']=='OFF':
                        cam=myCamDriver()
                        cam.savePhoto(buf,"photo.jpg")
                        #cam.showPhoto("photo.jpg")
                        thread.start_new_thread(cam.showPhoto,("photo.jpg",))
                        buf=''
                    else:
                        buf="%s%s" %(buf,data['photo'])

                #Received and saved the AES key
                elif sensor=='key' and data['key']!="":
                    #Key need to be decrypted by using the private key
                    cry=myCrypto(self.device)
                    dec=cry.decryptRSA(data['key'])
                    aesKeys[sender]=b64decode(dec)
                
                #Decrypt and show the gps data
                elif sensor=='gps' and data['gps']!="":
                    gpsData=data['gps']
                    if sender in aesKeys:
                        rep=myCrypto(sender)
                        rep.key=aesKeys[sender]
                        gpsData=rep.decrypt(gpsData)
                    print "** GPS=>"+gpsData


        elif cmd=="SHARE":
           print "This should be implemented"

        elif cmd=="UNSHAR":
           print "This should be implemented"

        elif cmd=="GET":
           #If GET Senze was received. The device must handle it.
           reactor.callLater(1,self.sendDataSenze,sensors=sensors,data=data,recipient=sender) 
        elif cmd=="PUT":
           reactor.callLater(1,self.handlePUTSenze,sensors=sensors,data=data,recipient=sender)
        else:
           print "Unknown command"
