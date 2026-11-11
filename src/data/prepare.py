"""Data stage: raw corpus files -> scrubbed, filtered, deduplicated, clustered and split messages.

Run offline (ENVIRONMENT.md):  python -m src.data.prepare
Reads data/raw/ (pinned by configs/raw_files.csv) and writes:
  data/messages.jsonl      kept messages with content (private, never committed)
  results/m1_messages.csv  every message read: id, hash, status, cluster, split (no content)
  results/m1_sources.csv   per source file: messages read, dropped by reason, kept
  results/m1_splits.csv    per class and split: messages, clusters, words, HTML share, URLs
It prints counts only, never message text: corpus text must not reach a cloud model (README section 4).
"""
import collections
import csv
import datetime
import email.utils
import hashlib
import json
import mailbox
import pathlib
import random
import re
import statistics
import tarfile

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import CountVectorizer

from src.data.download import RAW, read_config
from src.data.emails import URL_RE, Rejected, body_text, is_english, normalise

SEED = 2026
CUTOFF = datetime.datetime(2022, 11, 30, tzinfo=datetime.timezone.utc)  # ChatGPT release (DATA_PROVENANCE.md)
CUTOFF_FILE = "phishing-2022"  # the only approved file collected across the cutoff
NEAR_DUPLICATE = 0.8  # Jaccard of 5-word shingles: the same message with small edits
TEMPLATE = 0.5  # half the 5-word phrases shared: the same campaign template
PILOT_PER_CLASS, TEST_FRAC, DEV_FRAC = 25, 0.25, 0.15
REASONS = ["parse_error", "non_text_part", "date_unknown", "after_cutoff", "empty", "not_english", "near_duplicate"]
SPLITS = ["pilot", "test", "dev", "train"]


def read_raw(row):
    """Yield (message id, raw bytes) for every message in one source file, in file order."""
    path = RAW / row["file"]
    if path.name.endswith(".tar.bz2"):
        with tarfile.open(path) as tar:  # members are read in memory; nothing is extracted to disk
            for member in tar.getmembers():
                name = member.name.rsplit("/", 1)[-1]
                # Messages are named number.md5 (corpus readme); this skips the 'cmds' script file.
                if member.isfile() and re.fullmatch(r"\d{5}\.[0-9a-f]{32}", name):
                    yield f"{row['file']}/{name}", tar.extractfile(member).read()
    else:
        box = mailbox.mbox(path, create=False)
        for i, key in enumerate(box.iterkeys()):
            yield f"{row['file']}#{i:05d}", box.get_bytes(key)


def message_date(headers):
    value = next((v for k, v in headers if k.lower() == "date"), None)
    try:
        date = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    return date if date.tzinfo else date.replace(tzinfo=datetime.timezone.utc)


def check_scope(msg, source):
    """Raise Rejected if a parsed message is outside the study's scope."""
    if source == CUTOFF_FILE:
        date = message_date(msg["headers"])
        if date is None:
            raise Rejected("date_unknown")
        if date >= CUTOFF:
            raise Rejected("after_cutoff")
    words = body_text(msg)
    if not words.strip():
        raise Rejected("empty")
    if not is_english(words):
        raise Rejected("not_english")


def shingles(msg, k=5):
    """Set of 5-word phrases, with URLs and digits masked so only the wording counts."""
    text = URL_RE.sub(" url ", (msg["subject"] + " " + body_text(msg)).lower())
    tokens = [re.sub(r"\d", "0", t) for t in re.findall(r"[a-z0-9']+", text)]
    k = min(k, len(tokens))
    return {" ".join(tokens[i : i + k]) for i in range(len(tokens) - k + 1)}


def jaccard_components(sets, threshold):
    """Component label per set: sets are joined if their Jaccard similarity >= threshold (chains allowed)."""
    X = CountVectorizer(analyzer=list, binary=True).fit_transform(sets).tocsr()
    sizes = np.asarray(X.sum(axis=1)).ravel()
    rows, cols = [], []
    for start in range(0, X.shape[0], 1000):  # blocks of rows keep memory bounded
        block = (X[start : start + 1000] @ X.T).tocoo()
        r = block.row + start
        jaccard = block.data / (sizes[r] + sizes[block.col] - block.data)
        keep = (jaccard >= threshold) & (r < block.col)
        rows.append(r[keep])
        cols.append(block.col[keep])
    r, c = np.concatenate(rows), np.concatenate(cols)
    graph = coo_matrix((np.ones(len(r)), (r, c)), shape=(X.shape[0], X.shape[0]))
    return connected_components(graph, directed=False)[1]


def assign_splits(cluster_sizes, seed=SEED):
    """Assign whole clusters, in seeded random order, to pilot, then test, dev, and train."""
    order = sorted(cluster_sizes)
    random.Random(seed).shuffle(order)
    total, filled, split_of = sum(cluster_sizes.values()), collections.Counter(), {}
    for cluster in order:
        if filled["pilot"] < PILOT_PER_CLASS:
            split = "pilot"
        elif filled["test"] < TEST_FRAC * total:
            split = "test"
        elif filled["dev"] < DEV_FRAC * total:
            split = "dev"
        else:
            split = "train"
        split_of[cluster] = split
        filled[split] += cluster_sizes[cluster]
    return split_of


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    config = read_config()
    records, contents = [], {}
    for row in config:
        for msg_id, raw in read_raw(row):
            record = {"id": msg_id, "label": row["label"], "source": row["file"],
                      "sha256": hashlib.sha256(raw).hexdigest(), "year": "", "status": "ok",
                      "cluster": "", "split": ""}
            try:
                msg = normalise(raw)
                date = message_date(msg["headers"])
                record["year"] = date.year if date else ""
                check_scope(msg, row["file"])
                contents[msg_id] = msg
            except Rejected as reason:
                record["status"] = str(reason)
            records.append(record)

    for label in ("phishing", "ham"):
        ok = [r for r in records if r["label"] == label and r["status"] == "ok"]
        # Near-duplicates: keep the first copy in corpus order (config order, then file order).
        seen = set()
        for record, comp in zip(ok, jaccard_components([shingles(contents[r["id"]]) for r in ok], NEAR_DUPLICATE)):
            if comp in seen:
                record["status"] = "near_duplicate"
            seen.add(comp)
        kept = [r for r in ok if r["status"] == "ok"]
        for record, comp in zip(kept, jaccard_components([shingles(contents[r["id"]]) for r in kept], TEMPLATE)):
            record["cluster"] = f"{label}-{comp:05d}"
        split_of = assign_splits(collections.Counter(r["cluster"] for r in kept))
        for record in kept:
            record["split"] = split_of[record["cluster"]]

    pathlib.Path("results").mkdir(exist_ok=True)
    kept = [r for r in records if r["status"] == "ok"]
    with open("data/messages.jsonl", "w", encoding="utf-8") as f:
        for r in kept:
            f.write(json.dumps({k: r[k] for k in ("id", "label", "source", "year", "cluster", "split")}
                               | contents[r["id"]], ensure_ascii=False) + "\n")
    write_csv("results/m1_messages.csv", records)

    sources = []
    for row in config:
        mine = [r for r in records if r["source"] == row["file"]]
        status = collections.Counter(r["status"] for r in mine)
        sources.append({"source": row["file"], "label": row["label"], "read": len(mine)}
                       | {reason: status[reason] for reason in REASONS} | {"kept": status["ok"]})
    write_csv("results/m1_sources.csv", sources)

    splits = []
    for label in ("phishing", "ham"):
        for split in SPLITS:
            mine = [r for r in kept if r["label"] == label and r["split"] == split]
            msgs = [contents[r["id"]] for r in mine]
            splits.append({
                "label": label, "split": split, "messages": len(mine),
                "clusters": len({r["cluster"] for r in mine}),
                "median_words": statistics.median(len(body_text(m).split()) for m in msgs),
                "pct_html": round(100 * sum(bool(m["html"].strip()) for m in msgs) / len(msgs), 1),
                "median_urls": statistics.median(len(m["urls"]) for m in msgs),
            })
    write_csv("results/m1_splits.csv", splits)
    for row in sources + splits:
        print(row)


if __name__ == "__main__":
    main()
