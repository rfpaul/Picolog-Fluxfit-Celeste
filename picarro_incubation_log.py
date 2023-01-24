# picarro_incubation_log

# This script does manual timestamps of
# the start and end of sampling times
# in the gas collars and announces measurement actions

import datetime as dt
import pyttsx # text-to-speech (TTS) module
import csv
import os
from collections import OrderedDict

# Windows path
filepath = "C:\\scripts\\output\\"

# OS X path (for testing only)
#filepath = "scripts/"

filename = "incubations.csv"

# Provide a TTS warning at x seconds
warnTimes = [20, 15, 10, 5, 4, 3, 2, 1]
# Number of minutes taken to wait for each action
actionTimes = OrderedDict([("lid on", 1),
                           ("lid off", 5)])
# Treatment labels
treatments = ["C_Initial", "F_Mid", "F_Final", "C_Mid", "C_Final"]
# Number of collars (5)
reps = range(1,6) # range is from start (inclusive) to end (non-inclusive)

# Change these if you had to interrupt and start where you left off
skipCollars = False
# Last completed collar before interrupt
lastCollar = ""

engine = pyttsx.init() # Initialize text-to-speech engine
engine.setProperty('rate', 150) # Set speech rate to 150 WPM

def get_mode():
    print("Select option:")
    print("1. Measuring all jars")
    print("2. Measuring mid and final jars")
    print("3. Measuring final jars only")
    modeCode = raw_input("==> ") # Take input as char
    if modeCode not in ('1', '2', '3'): # Check for valid selection
        print("Invalid input")
        modeCode = get_mode()
    return int(modeCode)
    
def initialize_paths_files():
    try:
        os.makedirs(filepath) # Try to create the folders for the log file
    except OSError:
        pass # The folder already exists
    
    try: # See if the file exists
        with open(filepath+filename, 'r'):
            pass
    except IOError: # If it doesn't, create a new one and start off with headers
        with open(filepath+filename, 'wb') as newfile:
            make_header = csv.writer(newfile, dialect='excel')
            make_header.writerow(["Unix Stamp", "Date", "Time", "CollarID", "Action"])

def send_to_count(treats):
    skip = skipCollars
    for label in treats:
        for collar in reps:
            if skip:
                print "Skipping", label+str(collar)
                if (label + str(collar)) == lastCollar:
                    skip = False
            else:
                for action in actionTimes:
                    print("{0} - Leading to {1}, {2}".format(dt.datetime.now(),
                                                            label+str(collar),
                                                            action))
                    countdown(label+str(collar), action, actionTimes[action])

# Run the coundown to the action prompt
def countdown(collarID, action, timeMins):
    currTime = dt.datetime.now() #The time now
    endTime = currTime + dt.timedelta(minutes=timeMins) #End time
    for warn in warnTimes: # At (End - Warn time), speak the countdown alert
        while dt.datetime.now() < (endTime - dt.timedelta(seconds=warn)):
            pass
        if warn >= 10: # Full alert for 10+ seconds left
            speak_item("{0} seconds to {1} for {2}".format(str(warn),
                                                           action, 
                                                           collarID.lower()))
        else:
            speak_item(str(warn)) # Speak seconds left only when below 10 seconds
    while dt.datetime.now() < endTime:
        pass
    speak_item("Go.")
    write_to_log(collarID, action, dt.datetime.now())        

def write_to_log(collarID, action, currTime):
    with open(filepath + filename, 'a+b') as logfile:
        log_csv = csv.writer(logfile, dialect='excel')
        # Current timestamp in UNIX epoch
        timestamp = int((currTime - dt.datetime(1970, 1, 1)).total_seconds())
        log_csv.writerow([timestamp, # Seconds into UNIX epoch
                         currTime.date(),
                         currTime.time(),
                         collarID,
                         action])

def speak_item(string):
    engine.say(string)
    engine.runAndWait()

def main():
    initialize_paths_files()
    
    mode = get_mode()
    
    useTreatments = []
    
    if mode == 1: # All treatments
        useTreatments = treatments

    elif mode == 2: # Mid and Final only
        useTreatments = [treatments[0:4]]
        
    else: # Final only
        useTreatments = [treatments[0:2]]
    
    print("Starting mode {}".format(mode))
    send_to_count(useTreatments)

# Run stuff
main()