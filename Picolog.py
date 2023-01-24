#!/usr/bin/env python

# Picolog.py
# Module with a class that handles logging UTC timestamps of measurement actions
# This should work in both Python 2 and 3. Tested on 2; no guarantees on 3.
# This script is also multi-platform to make it portable.

# some example usage... To load--
# >>> from Picolog import Picolog
# --while in working directory containing the script, check using
# os.getcwd() command, move with os.chdir("path goes here").
# More simply, "run file" this script directly from an IDE (e.g. Spyder)
# Prep a Picolog:
# >>> myLog = Picolog("C:\\scripts\\output\\measurements.csv")
# Create a new Picolog at path (will NOT overwrite existing file by default):
# >>> myLog.make_logfile()
# Log a measurement:
# >>> myLog.log("control upland_site", 3, "lid on")

# Copyright (C) 2015 Robert Paul

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

## Package imports

import csv
import datetime as dt
import os
import platform

## Class definition

class Picolog(object):
# Class containing methods of creating and updating measurement log file
    # Header of csv file
    header = ['Unix stamp', # Seconds into UNIX epoch
              'UTC Date', # UTC date YYYY-MM-DD
              'UTC Time', # UTC time HH::MM::SS
              'Group ID', # Major classification ID(s)
              'Unique ID', # Secondary ID of individual experimental unit
              'Action', # Action performed
              'Notes'] # Additional information
    
    # Initialize class with filepath argument
    def __init__(self, filepath):
        self.filepath = filepath
    
    # Boolean from checking if the filepath is valid
    def is_valid_filepath(self):
        try:
            return os.path.isfile(self.filepath)
        except Exception as e:
            print("ERROR: {}".format(e))
    
    # When called, checks to see if the file exists. If it doesn't exist or
    # overwrite is True, create new CSV log
    def make_logfile(self, overwrite=False):
        if not self.is_valid_filepath() or overwrite:
            try:
                # Windows is stupid and needs to write text as a binary stream
                if platform.system() == "Windows":
                    openMode = 'wb'
                else:
                    openMode = 'w'
                # Write a new CSV file with just the header
                with open(self.filepath, openMode) as newfile:
                    make_header = csv.writer(newfile, dialect='excel')
                    make_header.writerow(self.header)
            except Exception as e:
                #pass
                print("ERROR: {0}\n{1} could not be created".format(e, 
                    self.filepath))
    
    # Print out the last line of log file
    # This will take a long time if the log file is large
    def tail(self):
        try:
            # Read through the file line-by-line until the end
            with open(self.filepath, 'r') as file:
                for line in file:
                    pass
                # Print last line as tab-delimited without the newline character
                print(line[:-1].replace(',', '\t'))
        except Exception as e:
            print("ERROR: {}".format(e))

    # Write a measurement start or end time to the log
    # Note: this can be run manually from the console, e.g.
    # >>> myLog.log("dry", 3, "lid on")
    def log(self, groupID, uniqueID, action, note=None):
        try:
            # We'll align the data on Unix time; using UTC is preferable
            # To do: Maybe add time zone support?
            currTime = dt.datetime.utcnow()
            # Windows is stupid and needs to write text as a binary stream
            if platform.system() == "Windows":
                openMode = 'ab'
            else:
                openMode = 'a'
            # Open log file in write append mode
            with open(self.filepath, openMode) as logfile:
                log_csv = csv.writer(logfile, dialect='excel')
                # Current timestamp in UNIX epoch
                # Python 2.x's datetime does not have a simple method for this
                # Integer number of seconds since 1970-01-01 00:00:00
                timestamp = int((
                    currTime - dt.datetime(1970, 1, 1)).total_seconds())
                
                newRow = [timestamp, # Seconds into UNIX epoch
                       currTime.date(), # UTC date YYYY-MM-DD
                       currTime.time(), # UTC time HH::MM::SS
                       groupID, # Major classification ID(s)
                       uniqueID, # Secondary ID of individual experimental unit
                       action, # Action performed
                       note] # Additional information
                
                # Sanitize inputs for commas--unexpected commas break CSV format
                # User input is at indices 3, 4, 5, 6
                for index in range(3, len(newRow)):
                    if str(newRow[index]).find(',') != -1:
                        print("Comma(s) removed from \"{}\"".format(
                            newRow[index]))
                        # Replace commas with empty string
                        newRow[index] = newRow[index].replace(",", "")
                
                log_csv.writerow(newRow)
        except Exception as e:
            print("ERROR: {}".format(e))