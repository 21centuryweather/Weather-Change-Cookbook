"""Download every file of a Zenodo record into ./data.

This script lists the record's files via the API and downloads
each one individually, with resume, retries, and MD5 verification.
Files already downloaded are skipped, so the script can safely be re-run.
"""
import hashlib
import time
from pathlib import Path
from urllib.parse import quote

import requests

RECORD_ID = "23199746"
API = f"https://zenodo.org/api/records/{RECORD_ID}"
DATA_DIR = Path("data")

MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds
HEADERS = {"User-Agent": "tobac-training-download/1.0 (python-requests)"}
CHUNK = 1024 * 1024


def md5sum(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def with_retries(func, label):
    """Call func(), retrying on transient errors. 401/403/404 fail immediately."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return func()
        except (requests.RequestException, OSError, ValueError) as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status in (401, 403, 404):
                raise
            print(f"  {label}: attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"{label}: failed after {MAX_RETRIES} attempts."
                ) from e
            time.sleep(RETRY_DELAY)


def list_files(session):
    """Return a list of file entries ({'key', 'size', 'checksum', ...})."""
    r = session.get(API, timeout=60)
    r.raise_for_status()
    files = r.json().get("files", [])
    if isinstance(files, dict):  # InvenioRDM-style serialisation
        files = files.get("entries", [])
    if isinstance(files, dict):
        files = list(files.values())
    if not files:  # fall back to the dedicated files endpoint
        r = session.get(f"{API}/files", timeout=60)
        r.raise_for_status()
        files = r.json().get("entries", [])
    return files


def download_file(session, entry):
    key = entry["key"]
    size = entry.get("size")
    checksum = entry.get("checksum") or ""
    expected_md5 = checksum.split(":", 1)[1] if checksum.startswith("md5:") else None

    dest = (DATA_DIR / key).resolve()
    if DATA_DIR.resolve() not in dest.parents:
        raise ValueError(f"Refusing to write outside {DATA_DIR}/: {key}")
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Skip files that are already complete.
    if dest.exists() and (size is None or dest.stat().st_size == size):
        if expected_md5 is None or md5sum(dest) == expected_md5:
            print(f"  Already downloaded, skipping: {key}")
            return

    url = f"{API}/files/{quote(key)}/content"
    part = dest.with_name(dest.name + ".part")

    resume = part.stat().st_size if part.exists() else 0
    if size is not None and resume > size:
        part.unlink()
        resume = 0

    if size is None or resume < size:
        headers = {"Range": f"bytes={resume}-"} if resume else {}
        with session.get(url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            # 206 = server honoured the Range request; 200 = start from scratch.
            mode = "ab" if r.status_code == 206 else "wb"
            with open(part, mode) as f:
                for chunk in r.iter_content(chunk_size=CHUNK):
                    if chunk:
                        f.write(chunk)

    # Verify before moving into place; a bad .part is discarded so the retry is clean.
    if size is not None and part.stat().st_size != size:
        got = part.stat().st_size
        part.unlink()
        raise ValueError(f"size mismatch for {key}: got {got}, expected {size}")
    if expected_md5 is not None and md5sum(part) != expected_md5:
        part.unlink()
        raise ValueError(f"MD5 mismatch for {key}")

    part.replace(dest)


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with requests.Session() as session:
        session.headers.update(HEADERS)

        print("Fetching file list from Zenodo...")
        try:
            files = with_retries(lambda: list_files(session), "file list")
        except requests.HTTPError as e:
            raise SystemExit(
                f"Could not read record {RECORD_ID}: {e}\n"
                "Check that the record is public and the ID is correct."
            )

        total = sum(f.get("size", 0) for f in files)
        print(f"Found {len(files)} files ({total / 1e6:,.1f} MB).")

        for i, entry in enumerate(files, 1):
            key = entry["key"]
            print(f"[{i}/{len(files)}] {key} ({entry.get('size', 0) / 1e6:,.1f} MB)")
            try:
                with_retries(lambda e=entry: download_file(session, e), key)
            except requests.HTTPError as e:
                raise SystemExit(f"Download of {key} was refused: {e}")

    print(f"\nAll files downloaded to {DATA_DIR}/")


if __name__ == "__main__":
    main()