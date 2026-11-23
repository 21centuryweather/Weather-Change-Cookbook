import os
import sys

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import metpy.calc as mpcalc
import xarray as xr
from cartopy.feature import LAND
from cartopy.mpl.gridliner import LATITUDE_FORMATTER, LONGITUDE_FORMATTER
from metpy.units import units

#sys.path.append(os.environ["WXSYSLIBDIR"])

#from utils.general.nci_utils import get_GADI_ERA5_filename

SWTcolors = [
    (134 / 255, 0 / 255, 34 / 255),
    (241 / 255, 0 / 255, 241 / 255),
    (255 / 255, 134 / 255, 255 / 255),
    (255 / 255, 241 / 255, 255 / 255),  # Pink WH
    (255 / 255, 204 / 255, 51 / 255),
    (255 / 255, 245 / 255, 204 / 255),  # Yellow CH
    (153 / 255, 15 / 255, 15 / 255),
    (178 / 255, 44 / 255, 44 / 255),
    (204 / 255, 81 / 255, 81 / 255),
    (229 / 255, 126 / 255, 126 / 255),
    (255 / 255, 178 / 255, 178 / 255),  # Red EH
    (153 / 255, 84 / 255, 15 / 255),
    (204 / 255, 142 / 255, 81 / 255),
    (255 / 255, 216 / 255, 178 / 255),  # Brown TH
    (107 / 255, 153 / 255, 15 / 255),
    (163 / 255, 204 / 255, 81 / 255),
    (195 / 255, 229 / 255, 126 / 255),  # Green FH (133/255,178/255,44/255),
    (66 / 255, 44 / 255, 178 / 255),
    (143 / 255, 126 / 255, 229 / 255),  # Purple WCT
    (5 / 255, 67 / 255, 113 / 255),
    (15 / 255, 107 / 255, 153 / 255),
    (44 / 255, 133 / 255, 178 / 255),
    (81 / 255, 163 / 255, 204 / 255),
    (126 / 255, 195 / 255, 229 / 255),
    (178 / 255, 229 / 255, 255 / 255),  # Blue COL
    (0 / 255, 60 / 255, 48 / 255),
    (1 / 255, 102 / 255, 95 / 255),
    (53 / 255, 151 / 255, 143 / 255),
    (128 / 255, 205 / 255, 193 / 255),
    (199 / 255, 234 / 255, 229 / 255),
]


def plot_synoptic_PVless_ERA5(code, indt):
    plot_extent = [80, 180, -60, -5]
    figsize = (11, 8)
    fig, ax = plt.subplots(
        1, 1, figsize=figsize, subplot_kw=dict(projection=ccrs.PlateCarree())
    )

    mls_file = "data/msl_era5_oper_sfc_20250901-20250930.nc"
    u_file = "data/u_era5_oper_pl_20250901-20250930.nc"
    v_file = "data/v_era5_oper_pl_20250901-20250930.nc"
    tcwv_file = "data/tcwv_era5_oper_sfc_20250901-20250930.nc"

    dsMSL = (
        xr.open_dataset(mls_file)
        .sel(time=indt, latitude=slice(-5, -60), longitude=slice(80, 180))
        .msl
    )
  
    dsU850 = (
        xr.open_dataset(u_file)
        .sel(time=indt, level=850, latitude=slice(-5, -60), longitude=slice(80, 180))
        .u
    )
  
    dsV850 = (
        xr.open_dataset(v_file)
        .sel(time=indt, level=850, latitude=slice(-5, -60), longitude=slice(80, 180))
        .v
    )

    dsU = (
        xr.open_dataset(u_file)
        .sel(time=indt, level=300, latitude=slice(-5, -60), longitude=slice(80, 180))
        .u
    )

    dsV = (
        xr.open_dataset(v_file)
        .sel(time=indt, level=300, latitude=slice(-5, -60), longitude=slice(80, 180))
        .v
    )

    dsTCWV = (
        xr.open_dataset(tcwv_file)
        .sel(time=indt, latitude=slice(-5, -60), longitude=slice(80, 180))
        .tcwv
    )

    spd300 = mpcalc.wind_speed(
        dsU * units("m/s"), dsV * units("m/s")
    ).metpy.dequantify()
    ujet300 = dsU.where(spd300 > 50 * 0.514444)
    vjet300 = dsV.where(spd300 > 50 * 0.514444)
    jet300 = spd300.where(spd300 > 50 * 0.514444)

    uW850 = dsU850.where(dsU850 >= 2).sel(latitude=slice(0, -20))
    vW850 = dsV850.where(dsU850 >= 2).sel(latitude=slice(0, -20))

    ax.set_extent(plot_extent, crs=ccrs.PlateCarree())

    ax.add_feature(LAND, facecolor="lightgrey")
    ax.coastlines(linewidths=0.4)

    plot_levels = list(range(900, 1060, 2))
    c = ax.contour(
        dsMSL.longitude,
        dsMSL.latitude,
        dsMSL / 100,
        levels=plot_levels,
        colors="black",
        linewidths=0.75,
        linestyles="-",
        transform=ccrs.PlateCarree(),
    )

    fmt = "%i"
    ax.clabel(c, c.levels, inline=True, fmt=fmt, fontsize=8)

    plot_levels = range(50, 120, 5)
    cf = ax.contourf(
        jet300.longitude,
        jet300.latitude,
        jet300 * 1.94384,
        levels=plot_levels,
        cmap="Blues",
        extend="max",
        transform=ccrs.PlateCarree(),
        alpha=0.5,
    )

    plot_levels = range(48, 1000, 500)
    cf = ax.contourf(
        dsTCWV.longitude,
        dsTCWV.latitude,
        dsTCWV,
        levels=plot_levels,
        cmap="Greens",
        extend="max",
        transform=ccrs.PlateCarree(),
        alpha=0.4,
    )

    c = ax.contour(
        dsTCWV.longitude,
        dsTCWV.latitude,
        dsTCWV,
        levels=[48],
        colors="limegreen",
        linewidths=0.8,
        linestyles="-",
        transform=ccrs.PlateCarree(),
    )

    nvec = 10
    q = ax.barbs(
        uW850.longitude[::nvec],
        uW850.latitude[::nvec],
        uW850[::nvec, ::nvec],
        vW850[::nvec, ::nvec],
        color="darkgreen",
        length=6,
        # scale=10,width=0.0008,color='darkgreen',#pivot='tail',
        transform=ccrs.PlateCarree(),
    )
    nvec = 10
    q = ax.quiver(
        jet300.longitude[::nvec],
        jet300.latitude[::nvec],
        ujet300[::nvec, ::nvec],
        vjet300[::nvec, ::nvec],
        scale=800,
        width=0.004,
        transform=ccrs.PlateCarree(),
        alpha=0.5,
    )

    label = ax.text(
        82,
        -9.5,
        f"{indt.strftime('%Y-%m-%d')} | {code}",
        ha="left",
        va="center",
        fontsize=20,
        bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="black"),
        zorder=10,
    )

    gl = ax.gridlines(
        transform=ccrs.PlateCarree(),
        draw_labels=True,
        linewidth=0.4,
        color="lightgrey",
        alpha=0.5,
        linestyle="--",
    )
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.top_labels = False
    gl.right_labels = False
    gl.bottom_labels = False
    gl.left_labels = False

    plt.show()

