import requests
from pathlib import Path
 
#Download BARRA-C2 data from the NCI THREDDS server using the NetCDF Subset Service (NCSS)
#https://opus.nci.org.au/spaces/NDP/pages/112263187/NetCDF+Subset+Service+NCSS

lon_range = (113,119)  # Longitude range for the subset
lat_range = (-36,-30)  # Latitude range for the subset
time_range = ("2026-01-01T00:00:00Z", "2026-01-31T23:00:00Z")  # Time range for the subset

#Setup each URL for the subset (one day of 2026 data)
UAS_URL = f"https://thredds.nci.org.au/thredds/ncss/grid/ob53/output/reanalysis/AUST-04/BOM/ERA5/historical/hres/BARRA-C2/v1/1hr/uas/latest/uas_AUST-04_ERA5_historical_hres_BOM_BARRA-C2_v1_1hr_202601-202601.nc?var=uas&north={lat_range[1]}&west={lon_range[0]}&east={lon_range[1]}&south={lat_range[0]}&horizStride=1&time_start={time_range[0]}&time_end={time_range[1]}&&&accept=netcdf4ext"
VAS_URL = f"https://thredds.nci.org.au/thredds/ncss/grid/ob53/output/reanalysis/AUST-04/BOM/ERA5/historical/hres/BARRA-C2/v1/1hr/vas/latest/vas_AUST-04_ERA5_historical_hres_BOM_BARRA-C2_v1_1hr_202601-202601.nc?var=vas&north={lat_range[1]}&west={lon_range[0]}&east={lon_range[1]}&south={lat_range[0]}&horizStride=1&time_start={time_range[0]}&time_end={time_range[1]}&&&accept=netcdf4ext"
HUSS_URL = f"https://thredds.nci.org.au/thredds/ncss/grid/ob53/output/reanalysis/AUST-04/BOM/ERA5/historical/hres/BARRA-C2/v1/1hr/huss/latest/huss_AUST-04_ERA5_historical_hres_BOM_BARRA-C2_v1_1hr_202601-202601.nc?var=huss&north={lat_range[1]}&west={lon_range[0]}&east={lon_range[1]}&south={lat_range[0]}&horizStride=1&time_start={time_range[0]}&time_end={time_range[1]}&&&accept=netcdf4ext"
LSM_URL = f"https://thredds.nci.org.au/thredds/ncss/grid/ob53/output/reanalysis/AUST-04/BOM/ERA5/historical/hres/BARRA-C2/v1/fx/sftlf/latest/sftlf_AUST-04_ERA5_historical_hres_BOM_BARRA-C2_v1.nc?var=sftlf&north={lat_range[1]}&west={lon_range[0]}&east={lon_range[1]}&south={lat_range[0]}&horizStride=1&&&&&accept=netcdf4ext"

#Setup the data directory
DATA_DIR = Path("data")
if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True)
 
#Download the url
for URL,var in zip([UAS_URL,VAS_URL,HUSS_URL,LSM_URL],[ "barra_uas.nc", "barra_vas.nc", "barra_hus.nc", "barra_lsm.nc"]):
    print(f"Downloading {var} from NCI THREDDS server...")
    response = requests.get(URL)
    response.raise_for_status()

    # Save the content to a NetCDF file
    with open(DATA_DIR / var, "wb") as f:
        f.write(response.content)
        f.close()
