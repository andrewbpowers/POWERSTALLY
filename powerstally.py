#!/usr/bin/env python
# -*- coding: utf-8 -*-

# powerstally.py for POWERSTALLY
# Written by Andrew B. Powers
# www.andrewbpowers.com

#Changelog
#0.8    2020-02-27
#   First beta version for friends of the house ;-)
#0.9    2020-03-11
#   Alpha version for public - Use at your own risk :-)
#1.2	2020-08-14
#	If no communication has occurred in the past 30 seconds, pings to make sure connection still exists
#	If no connection, resets WiFi
#1.3    2020-08-26
#   Code cleanup, easier to read
#   Current scene name request timeout after 2 seconds
#   Fixed logging to wrong date file issue
#   If GPIO pins are already configured, user is given a chance to stop script


#ToDo
#	Fade to black transition will turn on Tally Light if a scene with the trigger char is loaded in preview

#make sure to pip3 install multiping socket thread signal

import sys
import time
import RPi.GPIO as GPIO
import logging
from pythonping import ping
import itertools
from multiping import MultiPing
import socket
import os
import signal

todaysDate = str(time.strftime("%Y-%m-%d"))

#################### Setup ##################

  #Comment out all but one of the following logFileNames.  The first will put all logs into a single file.  The second will create a new logfile for each day.
#logFileName = '/home/pi/tally.log'
logFileName = '/home/pi/tally_'+ todaysDate +'.log'

  #Set the GPIO Pins
tallyLightGPIO = 25
statusLightGPIO = 4

  #Set the trigger character
triggerChar = '+'

  #Set the number of seconds of no ping response before resetting
resetSeconds = 120 #Minimum 40 seconds
beginPingSeconds = 1

  #Set the websocket port (Should be 4444) and password (set in OBS Studio)
port = 4444
password = "328149"



#################### Functions ##################

def setLogger(fname):
#https://stackoverflow.com/questions/12158048/changing-loggings-basicconfig-which-is-already-set
  for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
  logging.basicConfig(filename=logFileName,level=logging.DEBUG, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',  datefmt='%y-%m-%d %H:%M:%S %Z')
  print("Logging to: " + logFileName)

  #Initialize logging
setLogger(logFileName)
logging.debug('Tally Light BOOTED')

  #Not sure what this does...
sys.path.append('../')
from obswebsocket import obsws, events, requests  # noqa: E402

  #Try load last good IP address
lastKnownOBSStudioIP = ""
try:
    logging.debug('Opening obsAddr.log')
    ipAddressHistory = open("obsAddr.log","r")
    logging.debug('Reading last known OBS Studio IP Address')
    lastKnownOBSStudioIP = ipAddressHistory.readline()
    logging.debug('Last known OBS Studio IP: ' + lastKnownOBSStudioIP)
    ipAddressHistory.close()
except:
	logging.debug('Could not load last good IP')

#Keep track of last communication time
lastCommunicationTime = time.time()

#2hz Long Blink
def delayBlinkLED(count):
    count *= 2
    while count:
      GPIO.output(statusLightGPIO, GPIO.LOW)
      time.sleep(0.25)
      GPIO.output(statusLightGPIO, GPIO.HIGH)
      time.sleep(0.25)
      count -= 1

#4hz Fast Blink
nextBlink = 0
def fastBlink(count):
  global nextBlink
  if time.time() > nextBlink:
    nextBlink = time.time() + 2
    while(count):
      GPIO.output(statusLightGPIO, GPIO.HIGH)
      time.sleep(0.02)
      GPIO.output(statusLightGPIO, GPIO.LOW)
      if count > 1:
        time.sleep(0.23)
      count -= 1

#Shutdown and restart WiFi
def resetWiFi():
    logging.debug("Shutting down WiFi")
    print("Shutting down WiFi")
    cmd = 'ifconfig wlan0 down'
    os.system(cmd)
    print("Bringing up WiFi in 5")
    delayBlinkLED(5)
    print("Now!")
    logging.debug("Bringing up WiFi")
    cmd = 'ifconfig wlan0 up'
    os.system(cmd)
    delayBlinkLED(5)
    

#Returns tuple of available IP addresses
def scan_all_ip():
  ipRange = []
  logging.debug("Pinging all IP addresses")
  for i in range(1,253):
    ipRange.append("192.168.0."+str(i))
    ipRange.append("192.168.1."+str(i))
    ipRange.append("192.168.2."+str(i))
    ipRange.append("192.168.178."+str(i))
  mp = MultiPing(ipRange)
  try:
    mp.send()
    responses, no_responses = mp.receive(2)
  except:
    logging.debug("Failure to ping addresses")
    print("Failure to ping addresses")
    return ""
  for addr, rtt in responses.items():
  	logging.debug ("%s responded in %f seconds" % (addr, rtt))
  return responses

#Ping a target IP
def pingHost(ipToPing):
  p = []
  p.append(ipToPing)
  mp = MultiPing(p)
  try:
    mp.send()
    responses, no_responses = mp.receive(2)
  except:
    logging.debug("Ping " + ipToPing + " Failure - Unable To Ping")
    print("Ping " + ipToPing + " Failure - Unable To Ping")
    return False
  if ipToPing in responses:
    logging.debug("Ping " + ipToPing + " Successful")
    print("Ping " + ipToPing + " Successful")
    return True
    logging.debug("Ping " + ipToPing + ": No Response")
    print("Ping " + ipToPing + ": No Response")
  return False
	
#Returns IP of OBS Studio (or "" if OBS Studio not found)
def find_open_socket():
  global lastCommunicationTime
  prefferedIP = ""
  responses = scan_all_ip()	  
  if responses != "":
    for addr, rtt in responses.items():
      if str(addr) == lastKnownOBSStudioIP:
        prefferedIP = addr
        print("Preffered IP loaded: " + lastKnownOBSStudioIP + " " + str(addr))
    for addr, rtt in responses.items():
      if connected == False:
        if prefferedIP != "":
          print("Attempting to connect to " + prefferedIP + "(last known IP of OBS Studio)")
          logging.debug ("Attempting to connect " + prefferedIP + "(last known IP of OBS Studio)")
          sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          result = sock.connect_ex((prefferedIP,port))
          sock.close
          if result == 0:
            logging.debug("OBS Studio Websocket Found!")
            print("OBS Studio Websocket Found!")
            return prefferedIP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Attempting to connect to " + addr)
        logging.debug ("Attempting to connect to " + addr)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((addr,port))
        sock.close
        if result == 0:
          logging.debug("OBS Studio Websocket Found!")
          print("OBS Studio Websocket Found!")
          lastCommunicationTime = time.time()
          return addr
  return ""

def signal_handler(signum, frame):
    raise Exception("Timed out!")

#Asks OBS Studio for current scene name, times out after 2 seconds
def requestCurrentSceneName():
  global currentSceneName, lastCommunicationTime 
  message = ""
  signal.signal(signal.SIGALRM, signal_handler)
  signal.alarm(2)
  print("Requesting current scene name - ",end="")
  try:
    message = ws.call(requests.GetCurrentScene())
    currentSceneName = getSceneName(message)
    print("Response: " + currentSceneName)
    logging.debug("Current scene name: " + currentSceneName)
    lastCommunicationTime = time.time()
  except:
    print("No response!")
    logging.debug("No response to current scene name request!")
  signal.signal(signal.SIGALRM, signal.SIG_IGN)
  signal.alarm(0)

#Function called if any Websocket Message rec'd
def on_event(message):
  global connected, lastCommunicationTime
  logging.debug(u"Got message: {}".format(message))
  print(u"Got message: {}".format(message))
  if format(message).find("SourceDestroyed event") > -1:
    connected = False
  else:
    lastCommunicationTime = time.time()

#Function called if scene changed
def on_switch(message):
  global LEDstate, lastCommunicationTime, currentSceneName
  logging.debug(u"Scene Changed To {}".format(message.getSceneName()))
  lastCommunicationTime = time.time()
  currentSceneName = format(message.getSceneName())
  setLEDfromSceneName()

#Parses scene name from websocket message
def getSceneName(message):
    sn = str(message)[str(message).find("name"):]
    sn = sn[:sn.find(",")]
    return sn

#Saves IP address to file for next time
def saveGoodIP(addr):
  try:
    ipAddressHistory = open("obsAddr.log","w+")
    ipAddressHistory.write(addr)
    ipAddressHistory.close()
    logging.debug("Saved new OBS Studio IP: " + str(addr))
  except:
    pass
  lastKnownOBSStudioIP = str(addr)

#Sets the LED status from the scene name
def setLEDfromSceneName():
  global currentSceneName, LEDstate
  if currentSceneName.find(triggerChar) > -1:
    GPIO.output(tallyLightGPIO, 1)
    logging.debug("LED ON")
    print("LED ON")
    LEDstate = 1
  else:
    GPIO.output(tallyLightGPIO, 0)
    logging.debug("LED OFF")
    print("LED OFF")
    LEDstate = 0

#################### Main Loop ##################
#Setup GPIO pins

GPIO.setmode(GPIO.BCM)
if GPIO.gpio_function(statusLightGPIO) == 0:
  print('!!!!! WARNING !!!!! WARNING !!! WARNING !!! WARNING !!! WARNING !!!')
  print('GPIO pins are already in use!')
  print('Please press CTRL-C immediately to stop script!')
  time.sleep(1)
  print('You have 8 seconds to comply!')
  time.sleep(2)
  print('Yes, baby... daddy is home  ;-)')
  time.sleep(5)
GPIO.setup(statusLightGPIO, GPIO.OUT)
GPIO.output(statusLightGPIO, GPIO.HIGH)
GPIO.setup(tallyLightGPIO, GPIO.OUT)

connected = False
LEDstate = 0
currentSceneName = ""
try:
    while 1:
#Begin attempting to find and connect to OBS Studio
        addr = find_open_socket()	#Get the address of OBS Studio
        if addr != "":	#If OBS Studio found
          ws = obsws(addr, port, password)
          ws.register(on_event)
          ws.register(on_switch, events.SwitchScenes)
          try:
            ws.connect()
            requestCurrentSceneName()
            setLEDfromSceneName()
            connected = True
            saveGoodIP(addr)
            if todaysDate != str(time.strftime("%Y-%m-%d")):
              print("Wrong logfile date!! Changing from " + todaysDate + " to " + str(time.strftime("%Y-%m-%d")))
              logging.debug("Wrong logfile date!! Changing from " + todaysDate + " to " + str(time.strftime("%Y-%m-%d")))
              if logFileName != '/home/pi/tally.log':
                todaysDate = str(time.strftime("%Y-%m-%d"))
                logFileName = '/home/pi/tally_'+ todaysDate +'.log'
                setLogger(logFileName)
                logging.debug("WAS logging to wrong logfile date!! Changed from " + todaysDate + " to " + str(time.strftime("%Y-%m-%d")))
          except:
            logging.debug("Connection Refused")
            print("Connection Refused")
#Connected!  
        while connected:	#blink status LED once for connected, twice for connected and Tally Light ON
                if lastCommunicationTime + beginPingSeconds < time.time():
                  logging.debug("Haven't heard from OBS in " + str(time.time()-lastCommunicationTime) + " seconds, Pinging!")
                  print("Haven't heard from OBS in " + str(time.time()-lastCommunicationTime) + " seconds, Pinging!")   
                  if pingHost(addr):
                    requestCurrentSceneName()
                    setLEDfromSceneName()
                  else:
                    time.sleep(2)
                    if lastCommunicationTime + resetSeconds < time.time():
                      logging.debug("TIMEOUT!!!")
                      print("TIMEOUT!!!")
                      resetWiFi()
                      connected = False
                if lastCommunicationTime + resetSeconds / 2 < time.time():
                  fastBlink(4)
                elif LEDstate == 1:
                  fastBlink(2)
                else:
                  fastBlink(1)
#Connection failed (or OBS studio not found!)
        try:
          GPIO.output(tallyLightGPIO, 0)
          ws.disconnect()
        except:
          pass
        logging.debug("Could not find OBS Studio - Waiting 2 seconds and re-attempting")
        print("Could not find OBS Studio - Waiting 2 seconds and re-attempting")
        time.sleep(2)

#Script stopped by ctl-C
except KeyboardInterrupt: 
    GPIO.output(tallyLightGPIO, 0)
    try:
      ws.disconnect()
    except:
      pass

#Cleanup
logging.debug("Shutting Down")
print("Shutting Down")
GPIO.output(tallyLightGPIO, 0)
GPIO.cleanup()
