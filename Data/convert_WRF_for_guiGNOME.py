from libgoods import curv_grid
import os
import numpy as np
import datetime
from netCDF4 import date2num

var_map = { 'time':'time','u_velocity':'U10','v_velocity':'V10','longitude':'XLONG','latitude':'XLAT',
           'longitude':'XLONG','latitude':'XLAT'}  
          
wrf = curv_grid.cgrid(os.path.join('ROMS_ucla','wrf_grid.nc'))
wrf.get_dimensions(var_map,get_time=False)

wrf.data['lon'] = wrf.data['lon'].squeeze()
wrf.data['lat'] = wrf.data['lat'].squeeze()

in_dir = os.path.join('ROMS_ucla','wind')
flist = os.listdir(in_dir)

out_dir = os.path.join('gnome_ucla','wind')
if not os.path.exists(out_dir):
    os.mkdir(out_dir)
    
t_units = 'hours since 2004-01-01 00:00:00'
for f in flist[0:2]:
    print f
    wrf.update(os.path.join(in_dir,f))
    
    len_t = wrf.Dataset.variables['U10'].shape[0]
    syear,smonth = f.split('_')[1].split('.')[0].split('-')
    sdate = datetime.datetime(int(syear),int(smonth),1,0,0,0)
    dts = [sdate + x*datetime.timedelta(hours=1) for x in range(len_t)]
    wrf.data['time'] = date2num(dts,t_units)
    wrf.atts['time'] = {'units':t_units}
    wrf.get_data(var_map)
    
    wrf.atts['wind'] = True
    # wrf.data['lonc'] = wrf.data['lon_rho']
    # wrf.data['latc'] = wrf.data['lat_rho']
    # wrf.grid['mask'] = wrf.grid['mask_rho']
    
    wrf.dlx = 1

    wrf.write_nc(os.path.join(out_dir,f))
    
