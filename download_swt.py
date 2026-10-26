import requests
from pathlib import Path

BASE_URL = "https://github.com/21centuryweather/Australian-synoptic-weather-types/raw/refs/heads/latest/"

FILES = [
    "example_data/20250204120000-24h-enfo-ef_u_850_0.grib2",
    "example_data/20250204120000-24h-enfo-ef_v_850_0.grib2",
    "SWT_climatology/SWT_climatology.csv",
    "SWT_climatology/SWT_climatology.nc",
    "SWT_fields/SWT_data.nc",
    "example_data/msl_era5_oper_sfc_20250901-20250930.nc",
    "example_data/tcwv_era5_oper_sfc_20250901-20250930.nc",
    "example_data/u_era5_oper_pl_20250901-20250930.nc",
    "example_data/v_era5_oper_pl_20250901-20250930.nc",
]

DATA_DIR = Path("data")

if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True)

for path in FILES:
    target = DATA_DIR / Path(path).name

    if target.exists():
        print(f"Already downloaded: {target}")
        continue

    print(f"Downloading {target.name} ...")
    partial = target.with_name(target.name + ".part")  # so an interrupted download isn't mistaken for a finished one
    with requests.get(BASE_URL + path, stream=True) as response:
        response.raise_for_status()
        with open(partial, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
    partial.replace(target)

print(f"Data saved in {DATA_DIR}")