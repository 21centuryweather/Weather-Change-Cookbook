"""Download the data files needed by this recipe into ./data.

Files that already exist are skipped, so it is safe to run more than once.
Run it from the recipe folder:  python download_recipe_data.py
"""
from pathlib import Path

import requests

DATA_DIR = Path("data")

FILES = [
    # Zenodo record 24393605
    "https://zenodo.org/records/24393605/files/2GMEL_ideal-actual_timeseries.nc?download=1",
    "https://zenodo.org/records/24393605/files/4GADE_ideal-actual_timeseries.nc?download=1",
    "https://zenodo.org/records/24393605/files/IDE00326.202412311900.nc?download=1",
    "https://zenodo.org/records/24393605/files/IDE00326.202412311920.nc?download=1",
    "https://zenodo.org/records/24393605/files/IDE00326.202412311940.nc?download=1",
    # Synoptic weather type climatology (GitHub)
    "https://raw.githubusercontent.com/21centuryweather/Australian-synoptic-weather-types/"
    "refs/heads/latest/SWT_climatology/SWT_climatology.csv",
]


def download(url: str, dest: Path) -> None:
    """Stream a file to disk, using a .part file so a failed download isn't left behind."""
    part = dest.with_name(dest.name + ".part")
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with open(part, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
    part.replace(dest)


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)  # only creates the folder if it's missing

    for url in FILES:
        name = url.split("?")[0].rsplit("/", 1)[-1]
        dest = DATA_DIR / name
        if dest.exists():
            print(f"[skip] {name} already exists")
            continue
        print(f"[download] {name}")
        download(url, dest)

    print(f"Done. Files are in {DATA_DIR.resolve()}")


if __name__ == "__main__":
    main()