"""Download the approved corpus files into data/raw/ and pin their SHA-256.

configs/raw_files.csv works like a lock file: on the first download the size, hash and
date are written into it; on every later run each file is re-hashed and must match.
This is the only stage that needs the network (ENVIRONMENT.md).
"""
import csv
import datetime
import hashlib
import pathlib
import sys
import urllib.request

CONFIG = pathlib.Path("configs/raw_files.csv")
RAW = pathlib.Path("data/raw")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_config():
    with open(CONFIG, newline="") as f:
        return list(csv.DictReader(f))


def main():
    rows = read_config()
    RAW.mkdir(parents=True, exist_ok=True)
    mismatches = []
    for row in rows:
        path = RAW / row["file"]
        if not path.exists():
            print(f"downloading {row['file']}")
            part = path.with_name(path.name + ".part")  # an interrupted download never looks complete
            urllib.request.urlretrieve(row["url"], part)
            part.rename(path)
        digest = sha256(path)
        if not row["sha256"]:  # first acquisition: pin what we received
            today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
            row.update(bytes=path.stat().st_size, sha256=digest, retrieved_utc=today)
        elif row["sha256"] != digest:
            mismatches.append(row["file"])
    with open(CONFIG, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    if mismatches:
        sys.exit(f"SHA-256 mismatch: {', '.join(mismatches)}")
    print(f"{len(rows)} files present and hashes match configs/raw_files.csv")


if __name__ == "__main__":
    main()
