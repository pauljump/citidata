#!/usr/bin/env python3
"""Download and verify monthly Citi Bike trip data from the official bucket.

    python3 fetch.py --dest DIR              newest 6 months
    python3 fetch.py --dest DIR --months 12  newest 12 months
    python3 fetch.py --dest DIR --list       show what would be fetched

Each zip goes in its own folder (nyc-202610/, jc-202610/). Files already
present at the published size are kept. Anything listed in manifest.json is
also checked against its SHA-256.
"""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

BUCKET = "https://s3.amazonaws.com/tripdata"
KEY = re.compile(r"^(JC-)?(20\d{4})-citibike-tripdata(\.csv)?\.zip$")
MANIFEST = pathlib.Path(__file__).resolve().parent / "manifest.json"


def published():
    """Return [(month, region, key, size)] for every monthly zip."""
    with urllib.request.urlopen(f"{BUCKET}?list-type=2&max-keys=1000", timeout=60) as r:
        root = ET.fromstring(r.read())
    if root.findtext("{*}IsTruncated") == "true":
        sys.exit("bucket listing has more than one page; add paging before trusting it")
    out = []
    for c in root.iterfind("{*}Contents"):
        key = c.findtext("{*}Key")
        m = KEY.match(key)
        if m:
            out.append((m[2], "jc" if m[1] else "nyc", key, int(c.findtext("{*}Size"))))
    return out


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(1 << 20):
            h.update(block)
    return h.hexdigest()


def check(path, size, known):
    """Return a problem description, or None if the file is good."""
    if path.stat().st_size != size:
        return f"size {path.stat().st_size}, expected {size}"
    if known and known["bytes"] == size:
        return None if sha256(path) == known["sha256"] else "SHA-256 differs from manifest.json"
    try:
        with zipfile.ZipFile(path) as z:
            bad = z.testzip()
    except zipfile.BadZipFile as e:
        return str(e)
    return f"corrupt member {bad}" if bad else None


def main():
    ap = argparse.ArgumentParser(description="Download and verify Citi Bike trip data.")
    ap.add_argument("--dest", type=pathlib.Path, required=True)
    ap.add_argument("--months", type=int, default=6)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.months < 1:
        ap.error("--months must be at least 1")

    files = published()
    months = sorted({m for m, region, _, _ in files if region == "nyc"})[-a.months:]
    files = sorted(f for f in files if f[0] in months)
    known = {e["file"]: e for e in json.loads(MANIFEST.read_text())}

    failed = 0
    for month, region, key, size in files:
        if a.list:
            print(f"{size:>13,}  {key}")
            continue
        path = a.dest / f"{region}-{month}" / key
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            part = path.with_name(key + ".part")
            r = subprocess.run(["curl", "-fsS", "--retry", "5", "-C", "-", "-R",
                                "-o", str(part), f"{BUCKET}/{key}"])
            if r.returncode:
                print(f"FAIL {key}: curl exit {r.returncode}")
                failed += 1
                continue
            part.rename(path)
        problem = check(path, size, known.get(key))
        print(f"FAIL {key}: {problem}" if problem else f"OK   {key}", flush=True)
        failed += bool(problem)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
