import numpy as np
import xarray as xr
import dask.array as da
import scipy
import pyproj
from skimage.segmentation import find_boundaries
import warnings
from metpy import calc as mpcalc

'''

From sea_breeze v1.2: https://github.com/andrewbrown31/sea_breeze/tree/v1.2

'''

def kinematic_frontogenesis(q,u,v):

    """
    Calculate 2D kinematic frontogenesis using water vapour mixing ratio.

    Identifies regions where moisture fronts are increasing or decreasing due to flow deformation, including sea breeze fronts.

    Uses MetPy formulation but implemented with numpy/xarray for efficiency.
    https://unidata.github.io/MetPy/latest/api/generated/metpy.calc.frontogenesis.html

    Parameters
    ----------
    q : xarray.DataArray
        Water vapour mixing ratio (or any scalar field), with lat/lon/time coordinates in units kg/kg.
    u : xarray.DataArray
        U wind component, with matching coordinates.
    v : xarray.DataArray
        V wind component, with matching coordinates.

    Returns
    -------
    xarray.Dataset
        2D kinematic frontogenesis in units (g/kg) / 100 km / 3h.

    Notes
    -----
    The input data is rechunked in lat/lon dimensions for gradient calculations.
    """

    #Rechunk data in one lat and lon dim
    q = q.chunk({"lat":-1,"lon":-1})
    u = u.chunk({"lat":-1,"lon":-1})
    v = v.chunk({"lat":-1,"lon":-1})

    #Convert specific humidity to g/kg
    q = q*1000

    #Calculate grid spacing in km using metpy, in x and y
    x, y = np.meshgrid(q.lon,q.lat)
    dx, dy = mpcalc.lat_lon_grid_deltas(x,y)

    #Convert the x and y grid spacing arrays into xarray datasets. Need to interpolate to match the original grid
    dx = xr.DataArray(np.array(dx),dims=["lat","lon"],coords={"lat":q.lat.values, "lon":q.lon.values[0:-1]}).\
            interp({"lon":q.lon,"lat":q.lat},method="linear",kwargs={"fill_value":"extrapolate"}).\
            chunk({"lat":q.chunksizes["lat"][0], "lon":q.chunksizes["lon"][0]})
    dy = xr.DataArray(np.array(dy),dims=["lat","lon"],coords={"lat":q.lat.values[0:-1], "lon":q.lon.values}).\
            interp({"lon":q.lon,"lat":q.lat},method="linear",kwargs={"fill_value":"extrapolate"}).\
            chunk({"lat":q.chunksizes["lat"][0], "lon":q.chunksizes["lon"][0]})

    #Calculate horizontal moisture gradient
    ddy_q = (xr.DataArray(da.gradient(q,axis=q.get_axis_num("lat")), dims=q.dims, coords=q.coords) / dy)
    ddx_q = (xr.DataArray(da.gradient(q,axis=q.get_axis_num("lon")), dims=q.dims, coords=q.coords) / dx)
    mag_dq = np.sqrt( ddy_q**2 + ddx_q**2)

    #Calculate horizontal U and V gradients, as well as divergence and deformation 
    #Following https://www.ncl.ucar.edu/Document/Functions/Contributed/shear_stretch_deform.shtml
    ddy_u = (xr.DataArray(da.gradient(u,axis=q.get_axis_num("lat")), dims=q.dims, coords=q.coords) / dy)
    ddx_u = (xr.DataArray(da.gradient(u,axis=q.get_axis_num("lon")), dims=q.dims, coords=q.coords) / dx)
    ddy_v = (xr.DataArray(da.gradient(v,axis=q.get_axis_num("lat")), dims=q.dims, coords=q.coords) / dy)
    ddx_v = (xr.DataArray(da.gradient(v,axis=q.get_axis_num("lon")), dims=q.dims, coords=q.coords) / dx)
    div = ddx_u + ddy_v
    strch_def = ddx_u - ddy_v
    shear_def = ddx_v + ddy_u
    tot_def = np.sqrt(strch_def**2 + shear_def**2)

    #Calculate the angle between axis of dilitation and isentropes
    psi = 0.5 * np.arctan2(shear_def, strch_def)
    beta = np.arcsin((-ddx_q * np.cos(psi) - ddy_q * np.sin(psi)) / mag_dq)

    F = 0.5 * mag_dq * (tot_def * np.cos(2 * beta) - div) * 1.08e9

    out = xr.Dataset({"F":F})
    out["F"] = out["F"].assign_attrs(
        units = "g/kg/100km/3hr",
        long_name = "Moisture frontogenesis",
        description = "2d kinematic moisture frontogenesis parameter.")  

    return out

def rotate_wind(u,v,theta):

    """
    Rotate u and v wind components to cross-shore and along-shore directions based on coastline orientation.

    Parameters
    ----------
    u : xarray.DataArray
        U-component of wind (east-west) in m/s.
    v : xarray.DataArray
        V-component of wind (north-south) in m/s.
    theta : xarray.DataArray
        Coastline orientation angles from North, in degrees.

    Returns
    -------
    uprime : xarray.DataArray
        Wind component parallel to the coast (along-shore).
    vprime : xarray.DataArray
        Wind component perpendicular to the coast (cross-shore).
    """

    #Rotate angle to be perpendicular to theta, from E (i.e. mathamatical angle definition)
    rotated_angle=(((theta)%360-90)%360) + 90   
    
    #Define normal angle vectors, pointing onshore
    cx, cy = [-np.cos(np.deg2rad(rotated_angle)), np.sin(np.deg2rad(rotated_angle))]
    
    #Define normal angle vectors, pointing alongshore
    ax, ay = [-np.cos(np.deg2rad(rotated_angle - 90)), np.sin(np.deg2rad(rotated_angle - 90))]    
    
    #Calculate the wind component perpendicular and parallel to the coast by using the normal unit vectors
    uprime = ((u*ax) + (v*ay))
    vprime = ((u*cx) + (v*cy))

    return uprime, vprime    

def interpolate_variance(angle_ds):

    """
    From a dataset of coastline variance, interpolate across the coastline.

    This is used because the result of get_coastline_angle_kernel() is not defined along the coastline.
    """

    xx,yy = np.meshgrid(angle_ds.lon,angle_ds.lat)

    points = angle_ds.variance.values.ravel()
    valid = ~np.isnan(points)
    points_valid = points[valid]
    xx_rav, yy_rav = xx.ravel(), yy.ravel()
    xxv = xx_rav[valid]
    yyv = yy_rav[valid]
    interpolated_variance = scipy.interpolate.griddata(np.stack([xxv, yyv]).T, points_valid, (xx, yy), method="linear").reshape(xx.shape)     
    interpolated_variance_da = xr.DataArray(interpolated_variance,dims=angle_ds.dims,coords=angle_ds.coords)

    angle_ds["variance_interp"] = interpolated_variance_da

    return angle_ds

def interpolate_angles(angle_ds):

    """
    From a dataset of coastline angles, interpolate across the coastline.

    This is used because the result of get_coastline_angle_kernel() is not defined along the coastline.
    """

    xx,yy = np.meshgrid(angle_ds.lon,angle_ds.lat)

    mean_complex = angle_ds.mean_abs * da.exp(1j*angle_ds.mean_angles)
    points = mean_complex.values.ravel()
    valid = ~np.isnan(points)
    points_valid = points[valid]
    xx_rav, yy_rav = xx.ravel(), yy.ravel()
    xxv = xx_rav[valid]
    yyv = yy_rav[valid]
    interpolated_angles = scipy.interpolate.griddata(np.stack([xxv, yyv]).T, points_valid, (xx, yy), method="linear").reshape(xx.shape) 

    interpolated_angles = da.rad2deg(da.angle(interpolated_angles))
    interpolated_angle_da = xr.DataArray(interpolated_angles - 90,coords={"lat":angle_ds.lat,"lon":angle_ds.lon})
    interpolated_angle_da = xr.where(interpolated_angle_da < 0, interpolated_angle_da+360, interpolated_angle_da)  

    angle_ds = angle_ds.drop_vars(["mean_abs","mean_angles"])
    angle_ds["angle_interp"] = interpolated_angle_da

    return angle_ds

def get_weights(x, p=4, q=2, R=5, slope=-1, r=10000):
    """
    Calculate weights for averaging angles between pixels and coastlines.
    This function computes weights based on the distance from a coastline, using a piecewise function with different inverse powers before and after a specified distance `R`. The weights smoothly transition at `R` with a specified slope, and are set to zero beyond a cutoff distance `r`.
    Parameters
    ----------
    x : array_like
        Distance(s) from the coastline.
    p : float, optional
        Inverse power to decrease weights after distance `R`. Default is 4.
    q : float, optional
        Inverse power to decrease weights before distance `R`. Default is 2.
    R : float, optional
        Distance at which the inverse weighting power changes from `p` to `q`. Default is 5.
    slope : float, optional
        Slope of the function at point `R`. Default is -1.
    r : float, optional
        The distance at which the weights go to zero (to avoid overflows). Default is 10000.
    Returns
    -------
    y : array_like
        Calculated weights for each input distance.
    Notes
    -----
    The function is based on a method by Ewan Short. 
    
    Method
    -------
    Continuity and smoothness is ensured at `x = R` by equating the function and its derivative at that point.

    Let y1 = m1 * (x / R) ** (-p) for x > R.
    Let y2 = S - m2 * (x / R) ** (q) for x <= R.
    Equate y1 and y2 and their derivative at x = R to get
    S = m1 + m2
    slope = -p * m1 = -q * m2 => m1 = -slope/p and m2 = -slope/q
    Thus specifying p, q, R, and the function's slope at x=R determines m1, m2 and S.

    """

    m1 = -slope/p
    m2 = -slope/q
    S = m1 + m2
    y = da.where(x>R,  m1 * (x / R) ** (-p), S - m2 * (x / R) ** (q))
    y = da.where(x==0, np.nan, y)
    y = da.where(x>r, 0, y)
    return y

def smooth_angles(angles,sigma):
    """
    Smooth angles using a gaussian filter
    Angles is an xarray dataarray from 0 to 360.
    Sigma is the sigma of the gaussian filter
    """
    z = np.exp(1j * np.deg2rad(angles.values))
    z = np.rad2deg(np.angle(scipy.ndimage.gaussian_filter(z, sigma))) % 360
    return xr.DataArray(z,dims=angles.dims,coords=angles.coords)

def get_coastline_angle_kernel(lsm=None,R=20,latlon_chunk_size=10,k=0,compute=True,path_to_load=None,save=False,path_to_save=None,lat_slice=None,lon_slice=None,smooth=False,sigma=4):

    """
    If compute is True, calculate the dominant coastline angle for each point in the domain based on a land-sea mask.

    Otherwise just loads the angles from disk.

    If computing, constructs a "kernel" for each point based on the angle between that point and coastline points, then takes a weighted average. There is an option to restrict the kernel to only the k nearest coastline points to reduce memory usage (see k parameter).
     
    The weighting function can be customised, but is by default an inverse parabola to distance R, then decreases by distance**4. The weights are set to zero at a distance of 10,000 km, and are undefined at the coast (where linear interpolation is done to fill in the coastline gaps).

    Parameters
    ----------
    lsm : xarray.DataArray, optional
        Binary land-sea mask with latitude ("lat") and longitude ("lon") information.
    R : int, default=20
        The distance (in km) at which the weighting function is changed from 1/p to 1/q. Around 2 times the grid spacing of the lsm seems appropriate based on initial tests.
    latlon_chunk_size : int, default=10
        The size of the chunks over the latitude/longitude dimension for computation.
    k : int, default=0
        The number of nearest coastline points to use for each point in the domain. If k=0, then all coastline points are used (memory intensive). If k is None, then a reasonablely large k is chosen based on grid spacing.
    compute : bool, default=True
        Whether to compute the angles or load from disk.
    path_to_load : str, optional
        File path to previous output that can be loaded if compute is False.
    save : bool, default=False
        Whether to save the computed angles output if compute is True.
    path_to_save : str, optional
        File path to save output if save is True.
    lat_slice : slice or array-like, optional
        Latitude indices or values to slice when loading angles from disk.
    lon_slice : slice or array-like, optional
        Longitude indices or values to slice when loading angles from disk.
    smooth : bool, default=False
        Whether to smooth the interpolated angles output using a Gaussian filter.
    sigma : float, default=4
        Sigma value for the Gaussian filter if smoothing.

    Returns
    -------
    xarray.Dataset
        Dataset containing arrays of coastline angles (0-360 degrees from North), as well as an array of angle variance as an estimate of uncertainty. Includes additional fields for coastline mask and minimum distance to the coast.

    Notes
    -----
    Thank you to Ewan Short and Jarrah Harrison-Lofthouse for help developing this method.
    """

    if save:
        if path_to_save is None:
            raise AttributeError("Saving but no path speficfied")
        
    if compute:

        assert np.in1d([0,1],np.unique(lsm)).all(), "Land-sea mask must be binary"
        
        warnings.simplefilter("ignore")

        #From the land sea mask define the coastline and a label array
        coast_label = find_boundaries(lsm)*1
        land_label = lsm.values

        #Get lat lon info for domain and coastline, and convert to lower precision
        lon = lsm.lon.values
        lat = lsm.lat.values
        xx,yy = np.meshgrid(lon,lat)
        xx = xx.astype(np.float32)
        yy = yy.astype(np.float32)    

        if k == 0:
            #If k is 0 then use all coastline points. This is memory intensive but accurate. Creates complex arrays of shape (n_coast_points, n_lat, n_lon)

            #Define coastline x,y indices from the coastline mask
            xl, yl = np.where(coast_label)

            #Get coastline lat lon vectors
            yy_t = np.array([yy[xl[t],yl[t]] for t in np.arange(len(yl))])
            xx_t = np.array([xx[xl[t],yl[t]] for t in np.arange(len(xl))])

            #Repeat the 2d lat lon array over a third dimension (corresponding to the coast dim). Also repeat the yy_t and xx_t vectors over the spatial arrays
            yy_rep = da.moveaxis(da.stack([da.from_array(yy)]*yl.shape[0],axis=0),0,-1).rechunk({0:-1,1:-1,2:latlon_chunk_size})
            xx_rep = da.moveaxis(da.stack([da.from_array(xx)]*xl.shape[0],axis=0),0,-1).rechunk({0:-1,1:-1,2:latlon_chunk_size})
            xx_t_rep = (xx_rep * 0) + xx_t
            yy_t_rep = (yy_rep * 0) + yy_t

        else:
            #If k is not 0, then only use the k nearest coastline points to each point in the domain. 
            #If k is not provided, then choose a reasonably large k based on grid spacing (based on k=1000 for a 0.25 degree grid). This
            # choice of k was tested on ERA5 grid spacing and found to give similar results to using all coastline points, except where coastline variance is large

            if k is None:
                dx = np.abs(lon[1]-lon[0]) * 100 #Approx km per degree at equator
                k = int(1000 * (25/dx))

            #Define coastline lat lon points from the coastline mask and define NN lookup
            coast_x, coast_y = np.where(coast_label)
            coast_lon = lon[coast_y]
            coast_lat = lat[coast_x]
            coast_X = np.array([coast_lat, coast_lon]).T
            coast_kdt = scipy.spatial.KDTree(coast_X)
            _,coast_ind = coast_kdt.query(np.array([yy.flatten(),xx.flatten()]).T, k)
            target_lon_coast = coast_lon[coast_ind.reshape((lat.shape[0],lon.shape[0])+(k,))]
            target_lat_coast = coast_lat[coast_ind.reshape((lat.shape[0],lon.shape[0])+(k,))]        

            #Repeat the 2d lat lon array k times.
            yy_rep = da.moveaxis(da.stack([da.from_array(yy)]*k,axis=0),0,-1).rechunk({0:-1,1:-1,2:latlon_chunk_size})
            xx_rep = da.moveaxis(da.stack([da.from_array(xx)]*k,axis=0),0,-1).rechunk({0:-1,1:-1,2:latlon_chunk_size})
            xx_t_rep = da.array(target_lon_coast).rechunk({0:-1,1:-1,2:latlon_chunk_size})
            yy_t_rep = da.array(target_lat_coast).rechunk({0:-1,1:-1,2:latlon_chunk_size})        

        #Calculate the distance and angle between coastal points and all other points using pyproj, then convert to complex space.
        geod = pyproj.Geod(ellps="WGS84")
        def calc_dist(lon1,lat1,lon2,lat2):
            fa,_,d = geod.inv(lon1,lat1,lon2,lat2)
            return d/1e3 * np.exp(1j * np.deg2rad(fa))
        
        stack = da.map_blocks(
                    calc_dist,
                    xx_t_rep,
                    yy_t_rep,
                    xx_rep,
                    yy_rep,
                    dtype=np.complex64,
                    meta=np.array((), dtype=np.complex64))
        del xx_t_rep, yy_t_rep, yy_rep, xx_rep
        
        #Move axes around for convenience later
        stack = da.moveaxis(stack, -1, 0)

        #Get back distance by taking absolute value
        stack_abs = da.abs(stack,dtype=np.float32)
        
        #Create an inverse distance weighting function
        weights = get_weights(stack_abs, p=4, q=2, R=R, slope=-1)

        #Take the weighted mean and convert complex numbers to an angle and magnitude
        print("INFO: Take the weighted mean and convert complex numbers to an angle and magnitude...")
        mean_angles = da.mean((weights*stack), axis=0).persist()
        mean_abs = da.abs(mean_angles)
        mean_angles = da.angle(mean_angles)    

        #Flip the angles inside the coastline for convention, and convert range to 0 to 2*pi
        mean_angles = da.where(land_label==1,(mean_angles+np.pi) % (2*np.pi),mean_angles % (2*np.pi))

        #Calculate the weighted circular variance
        print("INFO: Calculating the sum of the weights...")
        total_weight = da.sum(weights, axis=0).persist()
        print("INFO: Calculating variance...")
        variance = (1 - da.abs(da.sum( (weights/total_weight) * (stack / stack_abs), axis=0))).persist()
        del stack, weights, total_weight 

        #Calculate minimum distance to the coast
        print("INFO: Calculating minimum distance to the coast...")
        min_coast_dist = stack_abs.min(axis=0).persist()

        #Convert angles to degrees, and from bearing to orientation of coastline.
        #Also create an xr dataarray object
        angle_da = xr.DataArray(da.rad2deg(mean_angles) - 90,coords={"lat":lat,"lon":lon})
        angle_da = xr.where(angle_da < 0, angle_da+360, angle_da)      

        #Convert variance and coast arrays to xr dataarrays
        var_da = xr.DataArray(variance,coords={"lat":lat,"lon":lon})
        coast = xr.DataArray(coast_label,coords={"lat":lat,"lon":lon})
        mean_abs = xr.DataArray(mean_abs,coords={"lat":lat,"lon":lon})
        mean_angles = xr.DataArray(mean_angles,coords={"lat":lat,"lon":lon})
        min_coast_dist = xr.DataArray(min_coast_dist,coords={"lat":lat,"lon":lon})

        #Create an xarray dataset
        angle_ds =  xr.Dataset({
            "angle":angle_da,
            "variance":var_da,
            "coast":coast,
            "mean_abs":mean_abs,
            "mean_angles":mean_angles,
            "min_coast_dist":min_coast_dist})

        #Do the interpolation across the coastline
        angle_ds = interpolate_angles(angle_ds)
        angle_ds = interpolate_variance(angle_ds)

        #Attributes
        angle_ds["angle"] = angle_ds["angle"].assign_attrs(
            units = "degrees",
            long_name = "Angle of coastline orientation",
            description = "The angle of dominant coastline orientation in degrees from North. Points with a dominant north-south coastline with ocean to the east will have an angle of 0 degrees. The dominant coastline for each point is determined by the weighted mean of the angles between that point and all coastline points in the domain. The weighting function is an inverse parabola to distance R, then decreases by distance**4. The weights are set to zero at a distance of 2000 km, and are undefined at the coast."
            )
        
        angle_ds["variance"] = angle_ds["variance"].assign_attrs(
            units = "[0,1]",
            long_name = "Variance of coastline angles",
            description = "For each point, the variance of the coastline angles in the domain. This is a measure of how many coastlines are influencing a given point. A value of 0 indicates that coastlines are generally in agreement, and a value of 1 indicates that the point is influenced by coastlines in all directions."
            )
        
        angle_ds["coast"] = angle_ds["coast"].assign_attrs(
            units = "[0,1]",
            long_name = "Coastline mask",
            description = "A binary mask of the coastline determined from the land-sea mask. 1 indicates a coastline point, and 0 indicates a non-coastline point."
            )
        
        angle_ds["min_coast_dist"] = angle_ds["min_coast_dist"].assign_attrs(
            units = "km",
            long_name = "Minimum distance to the coast",
            description = "The minimum distance to the coast for each point in the domain."
            )
        
        angle_ds["angle_interp"] = angle_ds["angle_interp"].assign_attrs(
            units = "degrees",
            long_name = "Interpolated coastline orientation",
            description = "The angle of dominant coastline orientation in degrees from North. Points with a dominant north-south coastline with ocean to the east will have an angle of 0 degrees. The dominant coastline for each point is determined by the weighted mean of the angles between that point and all coastline points in the domain. The weighting function is an inverse parabola to distance R, then decreases by distance**4. The weights are set to zero at a distance of 2000 km, and are undefined at the coast, where linear interpolation is then done."
            )
        
        angle_ds["variance_interp"] = angle_ds["variance_interp"].assign_attrs(
            units = "[0,1]",
            long_name = "Interpolated variance of coastline angles",
            description = "For each point, the variance of the coastline angles in the domain. This is a measure of how many coastlines are influencing a given point. A value of 0 indicates that coastlines are generally in agreement, and a value of 1 indicates that the point is influenced by coastlines in all directions. The variance is undefined at the coast, and here the variance is interpolated across the coastline."
            )
        
        angle_ds = angle_ds.assign_attrs(
            description = "Dataset of coastline angles and variance",
            acknowledgmements = "This method was developed with help from Ewan Short and Jarrah Harrison-Lofthouse.",
            R_km = str(R)
            )

    else:

        if path_to_load is not None:
            angle_ds = xr.open_dataset(path_to_load)
            if lat_slice is not None:
                angle_ds = angle_ds.sel(lat=lat_slice)
            if lon_slice is not None:
                angle_ds = angle_ds.sel(lon=lon_slice)
            save = False
        else:
            raise AttributeError("If not computing the angles, path_to_load needs to be specified")

    if save:
        angle_ds.to_netcdf(path_to_save)

    if smooth:
        angle_ds["angle_interp"] = smooth_angles(angle_ds["angle_interp"],sigma)

    return angle_ds