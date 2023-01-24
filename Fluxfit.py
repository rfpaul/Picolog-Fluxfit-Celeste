#!/usr/bin/env python
# Fluxfit.py

# This script takes the measurement time log and matches it up with
# the Picarro data log to give a ppm/s gas flux and R^2 correlation values
# of each measurement Fluxinterval
 
# Instructions
# Either run this file directly from an IDE (e.g. Spyder) or navigate to the
# directory in the console and--
# >>> from Fluxfit import Fluxfit
# Then create your own instance of the Fluxfit class:
# >>> myFlux = Fluxfit("path for your measurment log file", "path for output")
# The default values of the class assume you might be running this on the
# Picarro. If you aren't, be sure to preserve the directory tree reflecting
# DataLog_User, and update the data_path variable, e.g.:
# >>> myFlux.data_path = "/media/removable/SD_64GB/DataLog_User/"
# The response time, universal start offset, and universal end offset can be
# modified similarly:
# >>> myFlux.startOffset = 35
# To get the fluxes, run pull_fluxes from your Fluxfit class instance:
# >>> myFlux.pull_fluxes()
# To get graphs, run write_graphs from your Fluxfit class instance:
# >>> myFlux.write_graphs("/media/removable/SD_64GB/Documents/graphs.pdf")

# Copyright (C) 2014-2015 Robert Paul

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
#

## Package imports
import os
import glob
import platform
import datetime as dt
import re
import csv
import numpy as np
from scipy import stats
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

## Class definition
class Fluxfit(object):
# A class that handles fitting linear regression flux values for
# a detected measurement interval. Requires paths of measurement logs
# and output files.
    # Where is the root directory with the analyzer data logs?
    data_path = "C:\\UserData\\DataLog_User\\"
    
    # # What's the serial number of the Picarro analyzer?
    # serial = "JFAADS2021"
    # # Data log date & time format: YYYYMMDD-HHMMSS
    # # datetime's strftime formatting: "%Y%m%d-%H%M%S"
    # dataLogFormat = serial+"-{0}-DataLog_User.dat"
    
    # Which labels are we getting?
    getLabels = ["CO2_dry", "CH4_dry", "N2O_dry", "NH3"]
    
    # Regex at the end of the "Action" text field defining the start of
    # measurement
    # Breakdown of default regex value
    # .*: any characters
    # [-_ ]: matches a dash, underscore, or space
    # on: match the text "on"
    # $: end of string
    # |: or
    # ^on$: match the entire string "on"
    # This will match with: "lid_on" "Lid On" "ON"
    # Will NOT match with: "observation" "+on"
    beginRead = '.*[-_ ]on$|^on$'
    # Regex at the end of the "Action" field defining the end of measurement
    endRead = '.*[-_ ]off$|^off$'
    
    # Response time between sample being drawn and measurement (in seconds)
    responseTime = 8
    
    # Additional universal offsets for start/end times (in seconds)
    startOffset = 0
    endOffset = 0
    
    def __init__(self, log_path, output_path):
    # Class initializer
        self.log_path = log_path
        self.output_path = output_path
    
    # Boolean from checking if the filepath is valid
    def is_valid_filepath(self, filepath):
        try:
            return os.path.isfile(filepath)
        except Exception as e:
            print("***ERROR*** {}".format(e))
    
    def load_log(self):
        if self.is_valid_filepath(self.log_path):
            try:
                log_df = pd.read_csv(self.log_path, header=0)
                log_df = log_df.set_index("Unix stamp")
                return log_df
            except:
                raise RuntimeError(self.log_path + " exists but did not parse " +
                    "properly. This was not recognized as a log file. Check " +
                    "for typos or verify the file data then try again.")
        else:
            raise FileNotFoundError(self.log_path + " is an invalid filepath." + 
                " Check for typos and try again.")
    
    def zippedStartEnd(self, log):
    # Zip together start and end times found in the Action field of the log
        # Get list of start times (defined by regex in beginRead)
        startList = list(log[log["Action"].str.contains(
            self.beginRead, re.IGNORECASE)].index)
        # Get list of end times (defined by regex in endRead)
        endList = list(log[log["Action"].str.contains(
            self.endRead, re.IGNORECASE)].index)
        # What if the start and end times don't match? Invoke as an error.
        if len(startList) != len(endList):
            raise RuntimeError("Action column mismatch. Number of start " +
                "times parsed: {}\tNumber of end times parsed: {}".format(
                    len(startList), len(endList)))
        else:
            # Now zip them together
            zipStEndTimes = zip(startList, endList)
            return zipStEndTimes
        
    def which_separator(self):
    # Defines the type of character for directory separation in file paths
        if platform.system() == "Windows":
            separator = '\\'
        else:
            separator = '/'
        return separator
    
    def file_list(self, startTime, endTime):
    # Get the list of files for the specified interval
        dirSep = self.which_separator()
        # Container for file paths that have the data we need
        targets = []
        
        stDate = dt.datetime.utcfromtimestamp(startTime)
        endDate = dt.datetime.utcfromtimestamp(endTime)
        
        # Get files associated with start and end dates
        for i in [stDate, endDate]:
            year = i.year
            # zfill to add leading zeroes
            month = str(i.month).zfill(2)
            day = str(i.day).zfill(2)
            # Where will we be looking for .dat files?
            # data_path/year/month/day/*.dat
            trailingPath = "{0}{1}{2}{1}{3}{1}*.dat".format(
                year, dirSep, month, day)
            globSearchPattern = self.data_path + trailingPath
            # Add the paths which match the search pattern
            targets.extend(glob.glob(globSearchPattern))
        
        # Remove duplicates using "set" and sort the list
        targets = sorted(list(set(targets)))
        # List comprehension to collect filepaths within interval
        targets = [self.file_within_interval(f, startTime, endTime) for f in targets]
        # Filter out 'None' values
        targets = list(filter(None, targets))
        # Return list of .dat files for the specified interval
        return targets
    
    def file_within_interval(self, filepath, startTime, endTime):
        firstStamp, lastStamp = self.file_timestamps(filepath)
        if startTime <= lastStamp and endTime >= firstStamp:
            return filepath
    
    def file_timestamps(self, filepath):
    # Get the start and end timestamps of a measurement data log file
        # Open in read-only binary mode
        with open(filepath, 'rb') as f:
            # Ignore header
            f.readline()
            # Get first data line
            firstLine = f.readline()
            # Take EPOCH timestamp value (hard-coded, 6th item)
            firstStamp = float(firstLine.decode().split()[5])
            # Go to the second-to-last character
            f.seek(-2, os.SEEK_END)
            # Keep going backwards until the last line is reached
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
            # Read the last line
            lastLine = f.readline()
            # Take EPOCH timestamp value (hard-coded, 6th item)
            lastStamp = float(lastLine.decode().split()[5])
        # Return the first and last timestamp values of the data log
        return firstStamp, lastStamp
    
    def parse_file_datetime(self, filepath):
        # Soft-coded version -- deprecated
        # dirSep = self.which_separator()
        # filename = filepath[filepath.rindex(dirSep)+1:len(filepath)]
        # fileDate =  filename[filename.index('-')+1:filename.rindex('-')]
        # Hard-coded version -- let's assume the date and time will always be
        # at the same position away from the filepath
        fileDate = filepath[-32:-17]
        # Parse formatting into datetime object
        # YYYYmmdd-HHMMSS => datetime
        return dt.datetime.strptime(fileDate, "%Y%m%d-%H%M%S")
        
    
    def grab_data(self, startTime, endTime):
    # Get the data directly from the analyzer log files, return it as dataframe
        # Adjust to real start and end time
        realStartdt = startTime + self.responseTime
        realEnddt = endTime + self.responseTime
        # Grab analyzer data files included in the interval
        dataFileList = self.file_list(realStartdt, realEnddt)
        # Empty list to hold dataframes
        dataList = []
        for dataPath in dataFileList:
            # Read in the .dat; last line is sometimes incomplete, handle error
            datadf = pd.read_csv(
                dataPath, header=0, delim_whitespace=True,
                error_bad_lines=True)
            # Set index on Unix time
            datadf = datadf.set_index('EPOCH_TIME')
            dataList.append(datadf)
        # Concatenate the dataframes in the list
        datadf = pd.concat(dataList)
        # Drop NA/NAN values; that screws up the index slicing!
        datadf = datadf.dropna()
        # Get the index locations for measurement start and end
        startIndex = datadf.index.get_loc(
            (startTime + self.responseTime + self.startOffset),
            method = 'nearest')
        endIndex = datadf.index.get_loc(
            (endTime + self.responseTime - self.endOffset),
            method = 'nearest')
        # Get the subset of the dataframe from start to end of measurement
        subset = datadf.iloc[startIndex:endIndex]
        return subset
    
    def pull_fluxes(self):
    # Get the fluxes from the data based on log times and write it to file
    # To-do: overwrite option
        log = self.load_log()
        zipStEnd = self.zippedStartEnd(log)
        
        for stTime, endTime in zipStEnd:
            # Get data frame for this interval
            data = self.grab_data(stTime, endTime)
            distance = data.index[-1] - data.index[0]
            print("Getting fluxes for {0} to {1} ({2}s)".format(
                data.index[0], data.index[-1], round(distance, 2)))
            # Line at the beginning of the current measurement
            first = log.loc[stTime]
            line = [stTime + self.responseTime,
                first["UTC Date"],
                first["UTC Time"],
                first["Group ID"],
                first["Unique ID"]]
            for label in self.getLabels:
                fluxFrame = data[label]
                slope, intercept, r_value = self.slope_int_Rval(fluxFrame)
                line.extend([slope, r_value])
            # Write line to file
            self.write_flux(line)

    def slope_int_Rval (self, df):
    # Slope and R value from a linear regression of the dataframe
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            list(df.index),
            list(df))
        # r_value is Pearson's r, return R^2 correlation coefficient
        return slope, intercept, r_value**2
    
    def write_flux(self, line):
    # Write the flux to the results file at output path
        # Windows is stupid and needs to write text as a binary stream
        if platform.system() == 'Windows':
            modeAppend = 'b'
        else:
            modeAppend = ''
        # Does the output file exist? If not, make a new one
        if not self.is_valid_filepath(self.output_path):
            with open(self.output_path, 'w'+modeAppend) as newfile:
                writeLabels = ["Epoch",
                            "UTC_Date",
                            "UTC_Time",
                            "GroupID",
                            "UniqueID"]
                # Columns to pull from the data; saved as a concentration rise
                # rate (ppm/s) and correlation coefficient R^2
                for label in self.getLabels:
                    writeLabels.extend([label+"_ppm/s", label+"_R^2"])
                make_header = csv.writer(newfile, dialect='excel')
                make_header.writerow(writeLabels)
        with open(self.output_path, 'a'+modeAppend) as file:
            thisRow = csv.writer(file, dialect='excel')
            thisRow.writerow(line)
    
    def write_graphs(self, graphOutputPath):
    # Save a PDF containing graphs of the measurement intervals at the specified
    # file path. Will overwrite any existing file at that path.
        # To do: pass these into the function as ...*args, *kwargs)
        # font = {'family' : 'sans-serif',
        #         'size'   : 9}
        # 
        # textSize = 9 # Default text size
        # titleSize = 12 # Title text size
        figureW = 4 # Figure width (in inches)
        figureH = 2.5 # Figure height (in inches)
        linWid = 0.8 # Line width (in points)
        
        # Use ggplot style
        plt.style.use('ggplot')
        
        # Get the measurement log
        log = self.load_log()
        # Get start and end times
        zipStEnd = self.zippedStartEnd(log)
        # Begin writing to the PDF via matplotlib's PDF backend
        with PdfPages(graphOutputPath) as pdf:
            # Go through each start and end interval
            for start_t, end_t in zipStEnd:
                # Load the data interval
                data = self.grab_data(start_t, end_t)
                distance = data.index[-1] - data.index[0]
                print("Graphing inverval from {0} to {1} ({2}s)".format(
                    data.index[0], data.index[-1], round(distance, 2)))
                for label in self.getLabels:
                    # Initialize a plot figure (width, height)
                    fig = plt.figure(figsize=(figureW, figureH))
                    # Prepare title with identifying information
                    titleText = "{0}: {1}, {2}, {3}".format(
                        start_t, # Start time
                        log["Group ID"].loc[start_t], # Group ID
                        log["Unique ID"].loc[start_t], # Individual ID
                        label) # Label
                    # Give title and axis labels
                    plt.title(titleText)
                    plt.xlabel("time (s)")
                    plt.ylabel("concentration (ppm)")
                    # Shift graph to 0-index
                    x_coords = np.asarray(data.index) - start_t - \
                        self.startOffset - self.responseTime
                    # Get fit line parameters
                    # slope, intercept, r_value = self.slope_int_Rval(data[label])
                    # Write the graph to the figure
                    plt.plot(x_coords,
                        np.asarray(data[label]),
                        linewidth=linWid)
                    # Add the fit line
                    slope, intercept, r_value = self.slope_int_Rval(data[label])
                    plt.plot(x_coords,
                        slope*data.index + intercept, # m*x + b format
                        color='black', linewidth=linWid/2)
                    # Use tight layout margins and spacing
                    fig.tight_layout()
                    # Save figure to PDF
                    pdf.savefig(fig)
                    # Close the figure
                    plt.close()
