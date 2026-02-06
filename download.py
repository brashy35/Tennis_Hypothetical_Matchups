from __future__ import annotations
import datetime as _dt
from pathlib import Path
import requests
from .config import CACHE_DATA_DIR
from .cache import connect, get_file_meta, upsert_file_meta

class DownloadError(RuntimeError):
    pass

def _http_get(url: str, headers: dict | None = None) -> requests.Response:
    try:
        r = requests.get(url, headers=headers or {}, timeout=30)
        return r
    except requests.RequestException as e:
        raise DownloadError(f"Network error downloading {url}: {e}") from e

def fetch_to_cache(key: str, url: str, filename: str) -> Path:
    """Downloads a file and caches it. Uses ETag/Last-Modified when possible."""
    con = connect()
    meta = get_file_meta(con, key)
    headers = {}
    if meta:
        _, etag, last_modified = meta
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

    r = _http_get(url, headers=headers)
    if r.status_code == 304 and meta:
        return Path(meta[0])

    if r.status_code != 200:
        raise DownloadError(f"Failed to download {url} (status {r.status_code})")

    out_path = CACHE_DATA_DIR / filename
    out_path.write_bytes(r.content)

    etag = r.headers.get("ETag")
    last_modified = r.headers.get("Last-Modified")
    fetched_at = _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    upsert_file_meta(con, key, str(out_path), etag, last_modified, fetched_at)
    return out_path
