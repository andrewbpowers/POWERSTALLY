# !/usr/bin/env python
# -*- coding: utf-8 -*-

# powerstally.py for POWERSTALLY
# Written by Andrew B. Powers
# www.andrewbpowers.com
# www.andrewbpowers.com/stories/2020/9/11/powerstally
# github.com/andrewbpowers/POWERSTALLY

# Changelog
# 0.8    2020-02-27
#    First beta version for friends of the house ;-)
# 0.9    2020-03-11
#    Alpha version for public - Use at your own risk :-)
# 1.0	2020-04-02
#    This version can be use for LED Tally Light or a high voltage Tally Light via relay board. Use what you like and prefer. 
#    Change the "TallyLightGPIOHighOrLowActiveOFF" and "TallyLightGPIOHighOrLowActiveOFF" value.

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

#####################################################################################
######################################## SETUP ######################################
#####################################################################################

# WEBSOCKET PORT (USALLY 4444) AND PASSWORD (ALSO SET IN THE OBS WEBSOCKET PLUG-IN)
port = 4444
password = "123456"

# SET THE TRIGGER CHARACTER
triggerChar = '+'

# SET THE GPIO PINS
TallyLightGPIO = 25
StatusLightGPIO = 4

# SET THE GPIO PIN VALUE FOR THE TALLYLIGHT - HIGH- OR LOW-ACTIVE
# VALUE FOR OFF
# 0 = FOR HIGH ACTIVE NORMALLY FOR LEDS
# 1 = LOW ACTIVE FOR RELAY BOARD FOR EXAMPLE
TallyLightGPIOHighOrLowActiveOFF = 0
# VALUE FOR ON
# 1 = FOR HIGH ACTIVE NORMALLY FOR LEDS
# 0 = LOW ACTIVE FOR RELAY BOARD FOR EXAMPLE
TallyLightGPIOHighOrLowActiveON = 1
	
# NUMBER OF SECONDS OF NO PING RESPONSE BEFORE RESETTING
# MIN. 40 SECONDS
resetSeconds = 120
beginPingSeconds = 1

# THIS LINE WILL PUT ALL LOGS INTO ONE SINGLE FILE
#logFileName = '/home/pi/powerstally.log'

# THIS LINE WILL CREATE A NEW LOGFILE FOR EACH DAY
logFileName = '/home/pi/powerstally_'+ todaysDate +'.log'

#####################################################################################
###################################### FUNCTIONS ####################################
#####################################################################################

def setLogger(fname):
  for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
  logging.basicConfig(filename=logFileName,level=logging.DEBUG, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',  datefmt='%y-%m-%d %H:%M:%S %Z')
  print("Logging to: " + logFileName)

# INITIALIZE LOGGING
setLogger(logFileName)
logging.debug('Yeah! POWERSTALLY is BOOTED!')

sys.path.append('../')
from obswebsocket import obsws, events, requests  # noqa: E402

# TRY TO LOAD LAST GOOD IP ADDRESS FROM THE PC WITH OBS STUDIO
lastKnownOBSStudioIP = ""
try:
    logging.debug('Opening obsaddress.log')
    ipAddressHistory = open("obsaddress.log","r")
    logging.debug('Reading last known OBS Studio IP Address')
    lastKnownOBSStudioIP = ipAddressHistory.readline()
    logging.debug('Last known OBS Studio IP address: ' + lastKnownOBSStudioIP)
    ipAddressHistory.close()
except:
	logging.debug('COULD NOT LOAD last good IP address from OBS Studio')

# TRACK THE LAST COMMUNICATION TIME
lastCommunicationTime = time.time()

# 2HZ SLOW BLINKING (INACTIVE STREAM/NOT RECORDING BUT CONNECTED TO OBS STUDIO)
def delayBlinkLED(count):
    count *= 2
    while count:
      GPIO.output(StatusLightGPIO, GPIO.LOW)
      time.sleep(0.25)
      GPIO.output(StatusLightGPIO, GPIO.HIGH)
      time.sleep(0.25)
      count -= 1

# 4HZ FAST BLINKING (ACTIVE SCENE WITH "+" IN THE SCENENAME)
nextBlink = 0
def fastBlink(count):
  global nextBlink
  if time.time() > nextBlink:
    nextBlink = time.time() + 2
    while(count):
      GPIO.output(StatusLightGPIO, GPIO.HIGH)
      time.sleep(0.02)
      GPIO.output(StatusLightGPIO, GPIO.LOW)
      if count > 1:
        time.sleep(0.23)
      count -= 1

# SHUTTING DOWN AND RESTART WLAN
def resetWiFi():
    logging.debug("SHUTTING DOWN WLAN!")
    print("SHUTTING DOWN WLAN!")
    cmd = 'ifconfig wlan0 down'
    os.system(cmd)
    print("Bringing up WLAN in 5")
    delayBlinkLED(5)
    print("Now!")
    logging.debug("Bringing up WLAN!")
    cmd = 'ifconfig wlan0 up'
    os.system(cmd)
    delayBlinkLED(5)
    
# RETURNS TUPLE OF AVAILABLE IP ADDRESSES
def scan_all_ip():
  ipRange = []
  logging.debug("Pinging all IP addresses")
  for i in range(1,253):
    ipRange.append("192.168.0."+str(i))
    ipRange.append("192.168.1."+str(i))
    ipRange.append("192.168.2."+str(i))
    ipRange.append("192.168.178."+str(i))
    ipRange.append("10.0.0."+str(i))
  mp = MultiPing(ipRange)
  try:
    mp.send()
    responses, no_responses = mp.receive(2)
  except:
    logging.debug("FAILURE! UNABLE to ping IP address!")
    print("FAILURE! UNABLE to ping IP address")
    return ""
  for addr, rtt in responses.items():
  	logging.debug ("%s responded in %f seconds" % (addr, rtt))
  return responses

# PING THE TARGET IP ADDRESS
def pingHost(ipToPing):
  p = []
  p.append(ipToPing)
  mp = MultiPing(p)
  try:
    mp.send()
    responses, no_responses = mp.receive(2)
  except:
    logging.debug("Ping " + ipToPing + " FAILURE! UNABLE to ping IP address!")
    print("Ping " + ipToPing + " FAILURE! UNABLE to ping IP address!")
    return False
  if ipToPing in responses:
    logging.debug("Ping " + ipToPing + " SUCCESSFUL!")
    print("Ping " + ipToPing + " SUCCESSFUL!")
    return True
    logging.debug("Ping " + ipToPing + ": NO RESPONSE!")
    print("Ping " + ipToPing + ": NO RESPONSE!")
  return False
	
# RETURNS IP ADDRESS OF THE PC WITH OBS STUDIO
# OR "" IF A PC WITH OBS STUDIO IS NOT FOUND
def find_open_socket():
  global lastCommunicationTime
  preferredIP = ""
  responses = scan_all_ip()	  
  if responses != "":
    for addr, rtt in responses.items():
      if str(addr) == lastKnownOBSStudioIP:
        preferredIP = addr
        print("Preferred IP address loaded: " + lastKnownOBSStudioIP + " " + str(addr))
    for addr, rtt in responses.items():
      if connected == False:
        if preferredIP != "":
          print("Attempting to connect to " + preferredIP + "(last known IP address of OBS Studio)")
          logging.debug ("Attempting to connect " + preferredIP + "(last known IP address of OBS Studio)")
          sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          result = sock.connect_ex((preferredIP,port))
          sock.close
          if result == 0:
            logging.debug("Yeah! OBS Studio Websocket found!")
            print("Yeah! OBS Studio Websocket found!")
            return preferredIP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Attempting to connect to " + addr)
        logging.debug ("Attempting to connect to " + addr)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((addr,port))
        sock.close
        if result == 0:
          logging.debug("OBS Studio Websocket found!")
          print("OBS Studio Websocket found!")
          lastCommunicationTime = time.time()
          return addr
  return ""

def signal_handler(signum, frame):
    raise Exception("TIMED OUT!")

# ASK OBS STUDIO VIA OBS WEBSOCKET FOR CURRENT SCENE NAME
# TIMES OUT AFTER TWO SECONDS
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
    print("NO RESPONSE!")
    logging.debug("NO RESPONSE to current scene name request!")
  signal.signal(signal.SIGALRM, signal.SIG_IGN)
  signal.alarm(0)

# FUNCTION CALLED IF ANY OBS WEBSOCKET MESSAGE RECEIVED.
def on_event(message):
  global connected, lastCommunicationTime
  logging.debug(u"Got message: {}".format(message))
  print(u"Got message: {}".format(message))
  if format(message).find("SourceDestroyed event") > -1:
    connected = False
  else:
    lastCommunicationTime = time.time()

# FUNCTION CALLED IF SCENE CHANGED
def on_switch(message):
  global LEDstate, lastCommunicationTime, currentSceneName
  logging.debug(u"Scene Changed To {}".format(message.getSceneName()))
  lastCommunicationTime = time.time()
  currentSceneName = format(message.getSceneName())
  setLEDfromSceneName()

# PARSES SCENE NAME FROM OBS WEBSOCKET MESSAGE
def getSceneName(message):
    sn = str(message)[str(message).find("name"):]
    sn = sn[:sn.find(",")]
    return sn

# SAVING IP ADDRESS TO FILE FOR THE NEXT SESSION
def saveGoodIP(addr):
  try:
    ipAddressHistory = open("obsaddress.log","w+")
    ipAddressHistory.write(addr)
    ipAddressHistory.close()
    logging.debug("Saved OBS Studio new IP address: " + str(addr))
  except:
    pass
  lastKnownOBSStudioIP = str(addr)

# SETS THE STATUS FOR THE TALLY LIGHT/"ON AIR"/"RECODING"-SIGN FROM THE SCENE NAME
# RELAY BOARD VERSION - LOW ACTIVE GPIO
def setLEDfromSceneName():
  global currentSceneName, LEDstate
  if currentSceneName.find(triggerChar) > -1:
    GPIO.output(TallyLightGPIO, TallyLightGPIOHighOrLowActiveON)
    logging.debug("LED ON/RELAY ACTIVE")
    print("LED ON/RELAY ACTIVE")
    LEDstate = 1
  else:
    GPIO.output(TallyLightGPIO, TallyLightGPIOHighOrLowActiveOFF)
    logging.debug("LED OFF/RELAY NOT ACTIVE")
    print("LED OFF/RELAY NOT ACTIVE")
    LEDstate = 0

#####################################################################################
###################################### MAIN LOOP ####################################
#####################################################################################

# SETUP THE GPIO PINS
GPIO.setmode(GPIO.BCM)
if GPIO.gpio_function(StatusLightGPIO) == 0:
  print('*** WARNIN!G *** WARNING! *** WARNING! *** WARNING! *** WARNING! ***')
  print('GPIO pins are ALREADY in USE!')
  print('Please PRESS CTRL-C IMMEDIATELY to STOP the script!')
  time.sleep(1)
  print('You have 10 seconds to comply!')
  time.sleep(4)
  print('...here s Johnny! ;-)')
  time.sleep(6)
GPIO.setup(StatusLightGPIO, GPIO.OUT)
GPIO.output(StatusLightGPIO, GPIO.HIGH)
GPIO.setup(TallyLightGPIO, GPIO.OUT)

connected = False
LEDstate = 0
currentSceneName = ""
try:
    while 1:
	
# START ATTEMPTING TO FIND AND CONNECT TO OBS STUDIO
# GET THE IP ADDRESS OBS Studio
        addr = find_open_socket()
        if addr != "":	
#IF OBS STUDIO WAS FOUND
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
              print("Hey, WRONG logfile date!! Changing from " + todaysDate + " to " + str(time.strftime("%Y-%m-%d")))
              logging.debug("Hey, WRONG logfile date! Changing from " + todaysDate + " to " + str(time.strftime("%Y-%m-%d")))
              if logFileName != '/home/pi/powerstally.log':
                todaysDate = str(time.strftime("%Y-%m-%d"))
                logFileName = '/home/pi/powerstally_'+ todaysDate +'.log'
                setLogger(logFileName)
                logging.debug("WAS logging to the wrong logfile date! Changed from " + todaysDate + " to " + str(time.strftime("%Y-%m-%d")))
          except:
            logging.debug("Connection Refused")
            print("Connection Refused")

# CONNECTED
        while connected:	
# BLINK STATUS LED - ONCE FOR CONNECTED, TWICE FOR CONNECTED AND TALLY LIGHT/"ON AIR"/"RECORDING"-SIGN IS ON
                if lastCommunicationTime + beginPingSeconds < time.time():
                  logging.debug("Haven't heard from OBS Studio in " + str(time.time()-lastCommunicationTime) + " seconds, Pinging!")
                  print("Haven't heard from OBS Studio in " + str(time.time()-lastCommunicationTime) + " seconds, Pinging!")   
                  if pingHost(addr):
                    requestCurrentSceneName()
                    setLEDfromSceneName()
                  else:
                    time.sleep(2)
                    if lastCommunicationTime + resetSeconds < time.time():
                      logging.debug("*** TIMEOUT! *** TIMEOUT! *** TIMEOUT! ***")
                      print("*** TIMEOUT! *** TIMEOUT! *** TIMEOUT! ***")
                      resetWiFi()
                      connected = False
                if lastCommunicationTime + resetSeconds / 2 < time.time():
                  fastBlink(4)
                elif LEDstate == 1:
                  fastBlink(2)
                else:
                  fastBlink(1)

# CONNECTION FAILED OR OBS STUDIO NOT FOUND
        try:
          GPIO.output(TallyLightGPIO, TallyLightGPIOHighOrLowActiveOFF)
          ws.disconnect()
        except:
          pass
        logging.debug("COULD NOT find OBS Studio! Waiting 2 seconds and try re-attempting...")
        print("COULD NOT find OBS Studio! Waiting 2 seconds and try re-attempting...")
        time.sleep(2)

# SCRIPT STOPPED BY CTRL-C
except KeyboardInterrupt: 
    GPIO.output(TallyLightGPIO, TallyLightGPIOHighOrLowActiveOFF)
    try:
      ws.disconnect()
    except:
      pass

# CLEANUP
logging.debug("SHUTTING DOWN! - Elvis has left the building... ;-)")
print("SHUTTING DOWN! - Elivs has left the building... ;-) ")
GPIO.output(TallyLightGPIO, TallyLightGPIOHighOrLowActiveOFF)
GPIO.cleanup()
