"""The raw measurements behind the main results, one row per email, version and layer, without email text.

python -m src.analysis.measurements export <split>  ->  results/measurements_<split>.csv (needs the data volume)
python -m src.analysis.measurements check <split>   (needs only the repository)

`check` recomputes every row of results/primary_<split>.csv from the measurements, bootstrap intervals
included, and fails on any difference, so a reader can verify the main results without the private corpora.
Scores and flags only: the layers' evidence is left out, because the TF-IDF evidence holds words from emails.
"""
import csv
import json
import pathlib
import statistics
import sys

from src.analysis.primary import CONTRASTS, LAYERS, gate_table, reading, write_csv
from src.analysis.score import CONDITIONS, rewritten
from src.analysis.stats import cluster_bootstrap_ci, holm, mcnemar_exact


def export(split):
    pairs = rewritten(split)
    passed, _, _ = gate_table(pairs)
    thresholds = json.loads(pathlib.Path("configs/thresholds.json").read_text())["layers"]
    rows = []
    for layer in LAYERS:
        with open(f"data/scores/{layer}_conditions_{split}.jsonl", encoding="utf-8") as f:
            scores = {(s["id"], s["condition"]): s for s in map(json.loads, f)}
        for msg, _ in pairs:
            for condition in CONDITIONS:
                s = scores[(msg["id"], condition)]
                ok = s["error"] is None
                rows.append({
                    "id": msg["id"], "class": msg["label"], "cluster": msg["cluster"],
                    "gate_passed": int(msg["id"] in passed), "layer": layer, "condition": condition,
                    "score": repr(s["score"]) if ok else "",
                    "flagged_native": int(s["flagged"]) if ok else "",
                    "flagged_calibrated": int(s["score"] > thresholds[layer]["threshold"]) if ok else "",
                    "error": int(not ok)})  # whether it failed; the message itself is not published
    write_csv(f"results/measurements_{split}.csv", rows)
    print(f"{len(rows)} rows: {len(pairs)} emails x {len(CONDITIONS)} versions x {len(LAYERS)} layers")


def recompute(measurements):
    """The rows of results/primary_<split>.csv, from the measurements alone."""
    rows = []
    for layer in LAYERS:
        mine = [m for m in measurements if m["layer"] == layer]
        at = {(m["id"], m["condition"]): m for m in mine}
        info = {m["id"]: m for m in mine if m["condition"] == "orig"}  # keeps the file's email order
        for analysis_set in ("gate_passed", "all_rewrites"):
            for cls in ("phishing", "ham"):
                for b, a in CONTRASTS:
                    in_set = [i for i, m in info.items()
                              if m["class"] == cls and (analysis_set == "all_rewrites" or m["gate_passed"] == "1")]
                    ids = [i for i in in_set if at[(i, a)]["error"] == at[(i, b)]["error"] == "0"]
                    clusters = [info[i]["cluster"] for i in ids]
                    shift = [float(at[(i, b)]["score"]) - float(at[(i, a)]["score"]) for i in ids]
                    for point in ("native", "calibrated"):
                        fa, fb = ([int(at[(i, c)][f"flagged_{point}"]) for i in ids] for c in (a, b))
                        diffs = [y - x for x, y in zip(fa, fb)]
                        lost, gained = diffs.count(-1), diffs.count(1)
                        ci, sci = cluster_bootstrap_ci(diffs, clusters), cluster_bootstrap_ci(shift, clusters)
                        rows.append({
                            "layer": layer, "set": analysis_set, "class": cls, "contrast": f"{b} vs {a}",
                            "point": point, "n": len(ids), "excluded_errors": len(in_set) - len(ids),
                            "rate_a": round(sum(fa) / len(ids), 4), "rate_b": round(sum(fb) / len(ids), 4),
                            "lost": lost, "gained": gained, "net_pp": round(100 * sum(diffs) / len(ids), 2),
                            "ci_low_pp": round(100 * ci[0], 2), "ci_high_pp": round(100 * ci[1], 2),
                            "reading": reading(100 * ci[0], 100 * ci[1]),
                            "mcnemar_p": round(mcnemar_exact(lost, gained), 6),
                            "score_shift": round(statistics.mean(shift), 4),
                            "shift_ci_low": round(sci[0], 4), "shift_ci_high": round(sci[1], 4), "holm_p": ""})
    family = [r for r in rows if (r["set"], r["class"], r["contrast"], r["point"])
              == ("gate_passed", "phishing", "llm vs null_a", "calibrated")]
    for r, p in zip(family, holm([r["mcnemar_p"] for r in family])):
        r["holm_p"] = round(p, 6)
    return rows


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def number(x):
    """Numbers as numbers, so "0" and "0.0" are the same value; other text unchanged."""
    try:
        return float(x)
    except ValueError:
        return x


def check(split):
    want = [{k: number(v) for k, v in r.items()} for r in read_csv(f"results/primary_{split}.csv")]
    got = [{k: number(v) for k, v in r.items()} for r in recompute(read_csv(f"results/measurements_{split}.csv"))]
    wrong = [(w, g) for w, g in zip(want, got) if w != g]
    if len(want) != len(got) or wrong:
        sys.exit(f"MISMATCH: {len(want)} rows expected, {len(got)} recomputed, {len(wrong)} differ; first: {wrong[:1]}")
    print(f"all {len(want)} rows of results/primary_{split}.csv recomputed exactly from the measurements")


if __name__ == "__main__":
    {"export": export, "check": check}[sys.argv[1]](sys.argv[2])
