#!/usr/bin/env python

import os, sys, string, math
import netCDF4 as nc4
from datetime import datetime, timedelta
# import importlib

import gnome
from gnome.spill import point_line_release_spill
from gnome.outputters import Renderer, NetCDFOutput

from datetime import datetime, timedelta

from TAP_Setup import setup
from gnome.model import Model
from gnome.utilities.remote_data import get_datafile
from gnome.map import MapFromBNA

from gnome.movers.py_current_movers import PyGridCurrentMover
from gnome.movers.py_wind_movers import PyWindMover
from gnome.movers.random_movers import IceAwareRandomMover
from gnome.environment import IceAwareCurrent, IceAwareWind

import gc

#from batch_gnome import batch_gnome

# create command file dir if it doesn't exist
print "RootDir is", setup.RootDir

def make_dir(name):
    path = os.path.join(setup.RootDir, name)
    if not os.path.exists(path):
        os.makedirs(path)

def make_model(base_dir='.'):
    #,images_dir=os.path.join(base_dir, 'images',gdat_dir='/data/dylan/ArcticTAP/data_gnome/ROMS_h2ouv/')):
    print 'initializing the model'
    print base_dir
    start_time = datetime(1985, 1, 1, 13, 31)
    # start with generic times...this will be changed when model is run
    model = Model(start_time=start_time,
                  duration=timedelta(hours=96),
                  time_step=120*60)
    mapfile = get_datafile(os.path.join(base_dir, 'arctic_coast3.bna'))
    print mapfile
    print 'adding the map'
    model.map = MapFromBNA(mapfile, refloat_halflife=0.0)  # seconds

    return model

# ## load up our run script
# sys.path.append(setup.RootDir)
# script = importlib.import_module(setup.PyGnome_script)
# print script
# print dir(script)
# # model = script.make_model(setup.RootDir)

# Instantiate a generic model
# model = make_model(setup.RootDir)

# do some finagling with the start times in the data files
fn = os.path.join(setup.Data_Dir,'arctic_filelist_cat.txt')
f = file(fn)
flist = []
for line in f:
    name = os.path.join(setup.Data_Dir, line)
    flist.append(name[:-1])   # Gonzo cat version
    # flist.append(name[:-1])   # laptop current version
Time_Map = []
for fn in flist:
    d = nc4.Dataset(fn)
    t = d['time']
    file_start_time = nc4.num2date(t[0], units=t.units)
    Time_Map.append( (file_start_time, fn) )


# load up the start positions
start_positions = open(os.path.join(setup.RootDir,
                                    setup.CubeStartSitesFilename)).readlines()
start_positions = [pos.split(',') for pos in start_positions]
start_positions = [( float(pos[0]), float(pos[1]) ) for pos in start_positions]

# model timing
release_duration = timedelta(hours=setup.ReleaseLength)
run_time = timedelta(hours=setup.TrajectoryRunLength)
# model.duration = run_time

NumStarts = setup.NumStarts


# # loop through seasons
for Season in setup.StartTimeFiles:
    SeasonName = Season[1]
    start_times = open(Season[0],'r').readlines()[:setup.NumStarts]
    #start_times = open(os.path.join(setup.RootDir, "All_yearStarts.txt")).readlines()

    make_dir(os.path.join(setup.RootDir,setup.TrajectoriesPath,SeasonName))
    print Season

    # get and parse start times in this season
    start_dt = []
    for start_time in start_times:
        start_time = [int(i) for i in start_time.split(',')]
        start_time = datetime(start_time[2],
                              start_time[1],
                              start_time[0],
                              start_time[3],
                              start_time[4],
                              )
        start_dt.append(start_time)


    # for time_idx, start_time in enumerate(start_dt):
    for time_idx in setup.RunStarts:
        gc.collect()    # Jay addition

        start_time = start_dt[time_idx]
        end_time = start_time + run_time
        print start_time, end_time  

        # set up the model with the correct forcing files for this time/duration
        file_list = []
        i = 0
        for i in range(0, len(Time_Map) - 1):
            curr_t, curr_fn = Time_Map[ i ]
            next_t, next_fn = Time_Map[ i+1 ]
            if next_t > start_time:
                file_list.append( curr_fn )
                if next_t > end_time:
                    break
        file_list.append( next_fn )    # pad the list with next file to cover special case of last file. 
                                        #   awkward. fix later
        print 'number of ROMS files :: ', len(file_list)
        print file_list
        
        # for i in range(0, 1000 ):
        #     curr_t, curr_fn = Time_Map[i]
        #     file_list.append( curr_fn )


        # set up model for this start_time/duration, adding required forcing files
        model = make_model(setup.RootDir)
        model.duration = run_time
        # model.movers.clear()

        print 'creating MFDataset'
        ds = nc4.MFDataset(file_list)
        
        print 'adding an Ice CurrentMover (Trapeziod/RK4):'
        ice_aware_curr = IceAwareCurrent.from_netCDF(filename=file_list,
                                                     dataset=ds,
                                                     grid_topology={'node_lon':'lon','node_lat':'lat'})
        i_c_mover = PyGridCurrentMover(current=ice_aware_curr, default_num_method='Trapezoid')
        model.movers += i_c_mover

        print 'adding an Ice WindMover (Euler):'
        ice_aware_wind = IceAwareWind.from_netCDF(filename=file_list,
                                                  dataset=ds,
                                                  grid = ice_aware_curr.grid)
        i_w_mover = PyWindMover(wind = ice_aware_wind, default_num_method='Euler')
        model.movers += i_w_mover
        
        print 'adding an Ice RandomMover:'
        model.movers += IceAwareRandomMover(ice_conc_var = ice_aware_wind.ice_conc_var, diffusion_coef=50000)



        # for pos_idx, start_position in enumerate(start_positions):
        for pos_idx in setup.RunSites:
            start_position = start_positions[pos_idx]

            OutDir = os.path.join(setup.RootDir,setup.TrajectoriesPath,SeasonName,'pos_%03i'%(pos_idx+1))
            make_dir(OutDir)

            print pos_idx, time_idx
            print "Running: start time:", start_time,
            print "At start location:",   start_position

            ## set the spill to the location
            spill = point_line_release_spill(num_elements=setup.NumLEs,
                                             start_position=( start_position[0], start_position[1], 0.0 ),
                                             end_position=( start_position[0]+0.4, start_position[1]+0.2, 0.0 ),
                                             release_time=start_time,
                                             end_release_time=start_time+release_duration
                                             )

            # set up the renderer location
            image_dir = os.path.join(setup.RootDir, 'Images',SeasonName, 'images_pos_%03i-time_%03i'%(pos_idx+1, time_idx))
            renderer = Renderer(os.path.join(setup.RootDir, setup.MapFileName),
                                image_dir,
                                image_size=(800, 600),
                                output_timestep=timedelta(hours=12))
            renderer.graticule.set_DMS(True)
            #renderer.viewport = ((-120.6666, 33.75),(-119.25, 34.5)) 
            make_dir(image_dir)

            # print "adding netcdf output"
            netcdf_output_file = os.path.join(OutDir,
                                              'pos_%03i-t%03i_%08i.nc'%(pos_idx+1, time_idx,
                                                int(start_time.strftime('%y%m%d%H'))),
                                              )


            model.start_time = start_time

            ## clear the old outputters
            model.outputters.clear()
#            model.outputters += renderer
            model.outputters += NetCDFOutput(netcdf_output_file,output_timestep=timedelta(hours=12))

            # clear out the old spills:
            model.spills.clear()
            model.spills+=spill

            model.full_run(rewind=True)
            # for i, step in enumerate(model):
            #     print i, step
                # print
                # for sc in model.spills.items():
                #     print "status_codes:", sc['status_codes']
                #     print "positions:", sc['positions']
                #     print "lw positions:", sc['last_water_positions']


