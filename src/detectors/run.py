"""Score every message of one split with one layer, offline.

python -m src.detectors.run <layer> <split>      e.g.  python -m src.detectors.run lynceus test

Writes data/scores/<layer>_<split>.jsonl (private: per-message scores) and prints only counts,
errors, runtime and the output's SHA-256, so a re-run can be compared without looking at results.
"""
import collections
import hashlib
import importlib
import json
import pathlib
import sys
import time


def main(layer, split):
    detector = importlib.import_module(f"src.detectors.{layer}")
    out = pathlib.Path(f"data/scores/{layer}_{split}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    start, scored, errors = time.monotonic(), 0, collections.Counter()
    with open("data/messages.jsonl", encoding="utf-8") as src, open(out, "w", encoding="utf-8") as dst:
        for line in src:
            msg = json.loads(line)
            if msg["split"] != split:
                continue
            result = detector.score(msg)
            scored += 1
            if result["error"]:
                errors[result["error"]] += 1
            dst.write(json.dumps({"id": msg["id"], **result}, sort_keys=True) + "\n")
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"{layer} {split}: {scored} scored, errors {dict(errors)}, "
          f"{time.monotonic() - start:.0f} s, output sha256 {digest}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
