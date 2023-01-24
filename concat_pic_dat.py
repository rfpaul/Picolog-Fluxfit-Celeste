# Concatenates (joins end-to-end) Picarro data files from a single
# day--this makes them easier to process

import os
import glob

myPath = "C:\UserData\DataLog_User\2015\09\28"

for root, dirs, files in os.walk(myPath):
    print("Root: {}\tDirs: {}\tFiles:{}".format(root, dirs, files))
    # Do we already have concatenated files? Skip if they're found
    if(len(glob.glob('*_conc.dat')) > 0):
        print("Concat file found. Passing directory.")
    else: 
        headerWritten = False
        for datFile in files:
            if datFile.endswith('User.dat'): # Yes, it is an original .dat file
                print("Processing {}".format(datFile))
                # Let's now open a file in the form "MM-DD_conc.dat"
                with open("{0}/{1}-{2}_conc.dat".format(root,
                                                        root[-5:-3],
                                                        root[-2:]), 'a') as fileOut:
                    with open(root+'/'+datFile, 'r') as readDat:
                        if headerWritten:
                            readDat.readline() # Skip header
                        else:
                            headerWritten = True
                        for line in readDat:
                            fileOut.write(line)
                print("Completed processing {}".format(datFile))
        print("Moving to next directory")
                    