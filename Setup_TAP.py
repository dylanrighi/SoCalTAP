"""
TAP Setup.py

Master set up script for a TAP run

All the data required to set up and build TAP cubes + site.txt file should be in here

"""

import os, sys, datetime
import numpy as np

import netCDF4 as nc4	

RootDir =  os.path.split(__file__)[0]
print "Loading TAP Setup data from:", RootDir

## Cube Builder Data
ReceptorType = "Grid" # should be either "Grid" or "Polygons" (only grid is supported at the moment)
CubeType = "Volume" # should be either "Volume" or "Cumulative"

## CubeDataType options are: 'float32', 'uint16', or 'uint8'
##   float32 gives better precision for lots of LEs
##   uint8 saves disk space -- and is OK for about 1000 LEs
##   uint16 is a mid-point -- probably good to 10,000 LEs or so
CubeDataType = 'float32' 

# Files with time series records in them used by GNOME
# These are used to compute the possible time files. The format is:
# It is a list of one or more time files. each file is desribed with a tuple:
#  (file name, allowed_gap_length, type)
#    file_name is a string
#    allowed_gap_length is in hours. It indicates how long a gap in the time
#         series records you will allow GNOME to interpolate over.
#    type is a string describing the type of the time series file. Options
#         are: "Wind", "Hyd" for Wind or hydrology type files
# if set to None, model start an end times will be used
#TimeSeries = [("WindData.OSM", datetime.timedelta(hours = 6), "Wind" ),]
TimeSeries = None

# time span of your data set
# current data files on my laptop...change for Gonzo runs
# DataStartEnd = (datetime.datetime(1985, 1, 1, 14),
#                datetime.datetime(1985, 5, 10, 10) 
#                )
# first 100 ROMS data files
# DataStartEnd = (datetime.datetime(1985, 1, 1, 14),
#                 datetime.datetime(1986, 3, 21, 22)
#                 )
# All ROMS data files (on Gonzo)
DataStartEnd = (datetime.datetime(2004, 1, 1, 1),
                datetime.datetime(20013, 12, 31, 23)
                )


DataGaps = ( )
# Data_Dir = 'C:\Users\dylan.righi\Science\ArcticTAP\data_gnome\ROMS_h2ouv'   # Laptop
# Data_Dir = '/data/dylan/ArcticTAP/data_gnome/ROMS_h2ouv/'  # Gonzo
Data_Dir = '/data/dylan/SoCalTAP/Data/gnome_ucla/surface/'  # Gonzo/V_TAP cat dir
Data_DirW = '/data/dylan/SoCalTAP/Data/gnome_ucla/wind/'  # Gonzo/V_TAP cat dir


# specification for how you want seasons to be defined:
#  a list of lists:
#  [name, (months) ]
#    name is a string for the season name  
#    months is a tuple of integers indicating which months are in that season

# could do 
# Seasons = [["All_year", range(1,13) ],
#               ]

# # example for specifying season
# Seasons = [["Winter", [11, 12, 1, 2, 3]],
#          ["Summer",[4, 5, 6, 7, 8, 9, 10]],]
Seasons = [
          ["AllYear", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]],
          #["Ice", [12, 1, 2, 3, 4, 5]],
          #["NoIce",  [6, 7, 8, 9, 10, 11 ]], 
          # ["Winter", [12, 1, 2, 3, 4, 5]],
          # ["Summer",  [6, 7, 8, 9, 10, 11 ]], 
          # ["Spring",  [3, 4, 5 ]], 
          # ["Summer",  [6, 7, 8 ]], 
          # ["Faller",  [9, 10, 11]],
          ]              

# You don't need to do anything with this
StartTimeFiles = [(os.path.join(RootDir, s[0]+'Starts.txt'), s[0]) for s in Seasons]

# number of start times you want in each season:
NumStarts = 500
#RunStarts = range(0,NumStarts)
#RunStarts = range(0,50)

# kludge for iterating runs
r0= int(sys.argv[2])
r1= int(sys.argv[3])

print 'RunLims : ', r0,r1
RunStarts = range(r0,r1)

# section for defining already run Trajectory files for BuildCubes
RunFiles = []


# # Length of release in hours  (0 for instantaneous)
ReleaseLength = 14*24   # platforms


# name of the GNOME SAV file you want to use
# note: GNOME locks it (for a very brief time when loading) 
# which means you need a separate copy for each
# instance of GNOME you want to run (OR just don't start multiple GNOMES too quickly)
# PyGnome_script = "script_ArcticTAP_orrtap"

# number of Lagrangian elements you want in the GNOME run
NumLEs = 10000
                            
# we only have "MediumCrude"  in the data for now (see OilWeathering.py)
OilWeatheringType = None
# OilWeatheringType = 'FL_Straits_MediumCrude'  # use None for no weathering -- weathering can be
#                           # post-processed by the TAP viewer for instantaneous
#                           # releases

#If ReceptorType is Grid, you need these, it defines the GRID

class Grid:
	pass
Grid.min_lat = 30.0 # decimal degrees
Grid.max_lat = 36.0
Grid.dlat = 0.09       # makes 10km tall receptor cells I
Grid.min_long = 237.0   # -123
Grid.max_long = 244.0   # -116 
Grid.dlong = 0.1       # ~9km at 36N, ~10 at 30N

# Grid.num_lat = 45
# Grid.num_long = 90
Grid.num_lat = int(np.ceil(np.abs(Grid.max_lat - Grid.min_lat)/Grid.dlat) + 1)
Grid.num_long = int(np.ceil(np.abs(Grid.max_long - Grid.min_long)/Grid.dlong) + 1)


TrajectoriesPath = "Trajectories_n" + str(NumLEs) # relative to RootDir
# TrajectoriesPath = "Trajectories_n5000" # relative to RootDir
#TrajectoriesRootname = "FlStr_Traj"


CubesPath = "Cubes_n" + str(NumLEs)
CubesRootNames = ["SoCal_" for i in StartTimeFiles] # built to match the start time files

# CubeStartSitesFilename = os.path.join(RootDir, "Arctic_platforms_all2.txt")
CubeStartSitesFilename = os.path.join(RootDir, "SB_sites_all.txt")
# CubeStartSitesFilename = os.path.join(RootDir, "Arctic_pipelines.txt")
spos = open(os.path.join(RootDir,CubeStartSitesFilename)).readlines()

# kludge for iterating runs
r0= int(sys.argv[4])
r1= int(sys.argv[5])

print 'RunSites : ', r0,r1
RunSites = range(r0,r1)

# this code reads the file
CubeStartSites = [x.split("#", 1)[0].strip() for x in open(CubeStartSitesFilename).readlines()]
CubeStartSites = [x for x in CubeStartSites if x]

CubeStartFilter = []   # January

MapName = "Arctic TAP"
MapFileName, MapFileType = ("arctic_coast3.bna", "BNA")

# days = [1, 3, 5, 7, 10, 15, 20, 30, 50, 70, 90, 120, 180]
days = [1, 2, 3, 5, 7, 10, 15, 20, 24]
# days = [1, 2, 3]
OutputTimes = [24*i for i in days] # output times in hours(calculated from days

# output time in hours
# OutputTimes = [6, 12, 24, 48, 72]

# OutputUserStrings = ["1 day",
#                      "2 days",
#                      "3 days",
#                      ]

OutputUserStrings = ["1 day",
                     "2 days",
                     "3 days",
                     "5 days",
                     "7 days",
                     "10 days",
                     "15 days",
                     "20 days",
                     "24 days",
                     ]

# this is calculated from the OutputTimes
# TrajectoryRunLength = OutputTimes[-1]
TrajectoryRunLength = 24 * 24

PresetLOCS = ["5 barrels", "10 barrels", "20 barrels"]
PresetSpillAmounts = ["1000 barrels", "100 barrels"]

## TAP Viewer Data (for SITE.TXT file)
##
TAPViewerSource = RootDir # where the TAP view, etc lives.
## setup for the Viewer"

TAPViewerPath = "TapView_" + str(NumLEs)
print TAPViewerPath
# TAPViewerPath = "TapView_n5000"

