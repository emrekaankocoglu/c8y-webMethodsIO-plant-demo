import json
import requests
import os
import time
import datetime
import sys
import configparser
from checkConnection import *
config = configparser.RawConfigParser()
config.read('wMioConfig.cfg')
wMconfDict = dict(config.items('WEBMETHODS'))
url=wMconfDict["url"]
headers = {
  'webhook_key': '',
  'Content-Type': 'application/json'}
headers['webhook_key']=wMconfDict["webhook_key"]
dataString=""
input=""
ledStatus=0
os.system('sudo sh -c "echo none > /sys/class/leds/led0/trigger"') #set built-in LED state to always off to gain control
template= {
    "id":"",
    "time":"" , 
    "data":""
}
#template to fit into Thin Edge JSON format

def checkValidity():
    global input
    if (input[0]!="~" or input[-1]!="."):
        raise ValueError("Incorrect payload")
    else:
        measurementArray=(input[1:].split("~")[0]).split("-")
        checksumArray=(input[1:].split("~")[1]).split(".")
        if(int(measurementArray[0])^int(measurementArray[1])!=int(checksumArray[1]) or int(measurementArray[2])^int(measurementArray[3])!=int(checksumArray[2])):
            raise ValueError("Checksum failed")
        else:
            return measurementArray
def convertAnalog(analogValue): #analog (0-1023) values to percentages converting block
    if analogValue>999:
        return "999"
    elif analogValue<100:
        return "0"+str(analogValue)
    else:
        return str(analogValue)
def fileHandler(): #fetch and send measurements from the folder to c8y
    dir_path = os.path.dirname(os.path.realpath(__file__))
    for files in os.listdir(dir_path):
        if files.endswith('.m'): #files that have '.m' extension are finished measurements read from the serial input
            try:
                c8ySend(files)
            except:
                pass
            os.remove(files) #remove after sending the measurements to c8y
def c8ySend(files):
    global input
    global ledStatus
    f=open(files,"r")
    input=f.read().strip()
    valueArray=checkValidity()
    template["time"]=files[:-2]
    template["id"]=wMconfDict["device_name"]
    dataString=convertAnalog(int(valueArray[0]))+convertAnalog(int(valueArray[1]))+"0"+valueArray[2]+"0"+valueArray[3]
    template["data"]=dataString
    payload=json.dumps(template)
    response = requests.request("POST", url, headers=headers, data=payload)
if (__name__=="__main__"):
    while True:
        if (checkConnection()):
            os.system('sudo sh -c "echo '+str(-ledStatus)+' > /sys/class/leds/led0/brightness"') #switch the LED to indicate transfer
            fileHandler()
            ledStatus=~ledStatus
        time.sleep(1)
