from libgoods import curv_grid
reload(curv_grid)
import os
var_map = { 'time':'time',
           }  
          
roms = curv_grid.roms(os.path.join('ROMS_ucla','roms_grd.nc'))
roms.get_dimensions(var_map,get_time=False)

roms.data['lon'] = roms.data['lon_psi']
roms.data['lat'] = roms.data['lat_psi']
# roms.data['lonc'] = roms.data['lon_rho']
# roms.data['latc'] = roms.data['lat_rho']
# roms.grid['mask'] = roms.grid['mask_rho']
    
roms.get_grid_info()

in_dir = os.path.join('ROMS_ucla','surface')
flist = os.listdir(in_dir)

out_dir = 'roms_gnome'
out_dir = os.path.join('gnome_ucla','surface')
if not os.path.exists(out_dir):
    os.mkdir(out_dir)
if not os.path.exists(out_dir):
    os.mkdir(out_dir)
    
for f in flist:
    print f
    roms.update(os.path.join(in_dir,f))
    roms.get_dimensions(var_map,get_xy=False)
    roms.get_data(var_map)

    roms.dlx = 1

    roms.write_nc(os.path.join(out_dir,f))
    
