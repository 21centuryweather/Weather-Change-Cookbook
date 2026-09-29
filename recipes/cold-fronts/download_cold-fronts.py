import zipfile
import io
import requests
from pathlib import Path
 
URL = "https://sandbox.zenodo.org/api/records/610702/files-archive"
DATA_DIR = Path("data")
 
if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True)
 
response = requests.get(URL)
response.raise_for_status()
 
with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
    zf.extractall(DATA_DIR)
 
print(f"Extracted to {DATA_DIR}/")
