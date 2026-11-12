"""Main results (README 6.1, scope v3): paired change per layer, class, contrast and operating point.

python -m src.analysis.primary <split> [layer ...]  ->  results/primary_<split>.csv,
results/gates_<split>.csv, results/selection_<split>.csv

Each row compares condition B with condition A on the same messages:
- lost: flagged under A, not under B; gained: the reverse; net_pp: change in flag rate
  (percentage points), with a 95% cluster-bootstrap CI and an exact McNemar p;
- score_shift: mean paired score change, with its CI.
Primary contrast: llm vs null_a (same plain-text format, only the wording differs; DEVIATIONS #12).
Analysis set "gate_passed" (primary) and "all_rewrites" (sensitivity). The confirmatory family
(phishing, calibrated threshold, llm vs null_a, gate_passed, one test per layer) is Holm-adjusted.
"""
import csv
import json
import pathlib
import statistics
import sys
from collections import Counter

from src.analysis.score import rewritten
from src.analysis.stats import cluster_bootstrap_ci, holm, mcnemar_exact
from src.data.emails import plain_body
from src.rewrite.gates import GATES, check, clean

LAYERS = ["spamassassin", "tfidf_lr", "lynceus"]
MARGIN_PP = 2.0  # PROTOCOL.md section 5


def reading(low_pp, high_pp):
    """The pre-declared reading of a 95% CI for a net change (PROTOCOL.md section 5)."""
    if low_pp > 0 or high_pp < 0:
        return "change"
    if -MARGIN_PP <= low_pp and high_pp <= MARGIN_PP:
        return f"no change larger than {MARGIN_PP:g} pp"
    return "inconclusive"
CONTRASTS = [("llm", "null_a"), ("lex", "null_a"), ("llm", "lex"), ("null_a", "orig")]  # (B, A)


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def gate_table(pairs):
    """Gate outcomes per class, and kept-vs-discarded means for the selection-bias check."""
    passed, gates, selection = set(), [], []
    for label in ("phishing", "ham"):
        mine = [(m, r) for m, r in pairs if m["label"] == label]
        fails = {m["id"]: check(plain_body(m), clean(r)) for m, r in mine}
        passed |= {i for i, f in fails.items() if not f}
        count = Counter(g for f in fails.values() for g in f)
        gates.append({"label": label, "rewritten": len(mine), "passed": sum(not f for f in fails.values())}
                     | {g: count[g] for g in GATES})
        for kept in (True, False):
            group = [m for m, _ in mine if (not fails[m["id"]]) == kept]
            selection.append({
                "label": label, "group": "kept" if kept else "discarded", "n": len(group),
                "median_words": statistics.median(len(plain_body(m).split()) for m in group) if group else "",
                "median_urls": statistics.median(len(set(m["urls"])) for m in group) if group else "",
                "pct_html": round(100 * sum(bool(m["html"].strip()) for m in group) / len(group), 1) if group else ""})
    return passed, gates, selection


def main(split, layers):
    pairs = rewritten(split)
    label = {m["id"]: m["label"] for m, _ in pairs}
    cluster = {m["id"]: m["cluster"] for m, _ in pairs}
    passed, gates, selection = gate_table(pairs)
    thresholds = json.loads(pathlib.Path("configs/thresholds.json").read_text())["layers"]
    rows = []
    for layer in layers:
        scores = {}
        with open(f"data/scores/{layer}_conditions_{split}.jsonl", encoding="utf-8") as f:
            for s in map(json.loads, f):
                scores[(s["id"], s["condition"])] = s
        t = thresholds[layer]["threshold"]
        for analysis_set in ("gate_passed", "all_rewrites"):
            for cls in ("phishing", "ham"):
                for b, a in CONTRASTS:
                    in_set = [i for i in label if label[i] == cls and (analysis_set == "all_rewrites" or i in passed)]
                    ids = [i for i in in_set if scores[(i, a)]["error"] is None and scores[(i, b)]["error"] is None]
                    excluded = len(in_set) - len(ids)  # scoring errors only (PROTOCOL.md section 5)
                    for point in ("native", "calibrated"):
                        flag = (lambda s: s["flagged"]) if point == "native" else (lambda s: s["score"] > t)  # noqa: E731
                        fa = [flag(scores[(i, a)]) for i in ids]
                        fb = [flag(scores[(i, b)]) for i in ids]
                        diffs = [int(y) - int(x) for x, y in zip(fa, fb)]
                        shift = [scores[(i, b)]["score"] - scores[(i, a)]["score"] for i in ids]
                        lost = sum(x and not y for x, y in zip(fa, fb))
                        gained = sum(y and not x for x, y in zip(fa, fb))
                        ci = cluster_bootstrap_ci(diffs, [cluster[i] for i in ids]) if ids else ("", "")
                        sci = cluster_bootstrap_ci(shift, [cluster[i] for i in ids]) if ids else ("", "")
                        rows.append({
                            "layer": layer, "set": analysis_set, "class": cls, "contrast": f"{b} vs {a}",
                            "point": point, "n": len(ids), "excluded_errors": excluded,
                            "rate_a": round(sum(fa) / len(ids), 4) if ids else "",
                            "rate_b": round(sum(fb) / len(ids), 4) if ids else "",
                            "lost": lost, "gained": gained,
                            "net_pp": round(100 * sum(diffs) / len(ids), 2) if ids else "",
                            "ci_low_pp": round(100 * ci[0], 2) if ids else "", "ci_high_pp": round(100 * ci[1], 2) if ids else "",
                            "reading": reading(100 * ci[0], 100 * ci[1]) if ids else "",
                            "mcnemar_p": round(mcnemar_exact(lost, gained), 6),
                            "score_shift": round(statistics.mean(shift), 4) if ids else "",
                            "shift_ci_low": round(sci[0], 4) if ids else "", "shift_ci_high": round(sci[1], 4) if ids else "",
                        })
    family = [r for r in rows if (r["set"], r["class"], r["contrast"], r["point"])
              == ("gate_passed", "phishing", "llm vs null_a", "calibrated")]
    for r, p in zip(family, holm([r["mcnemar_p"] for r in family])):
        r["holm_p"] = round(p, 6)
    for r in rows:
        r.setdefault("holm_p", "")
    write_csv(f"results/primary_{split}.csv", rows)
    write_csv(f"results/gates_{split}.csv", gates)
    write_csv(f"results/selection_{split}.csv", selection)
    print(f"{len(rows)} rows; gate-passed {len(passed)} of {len(pairs)}; confirmatory family:")
    for r in family:
        print({k: r[k] for k in ("layer", "n", "rate_a", "rate_b", "net_pp", "ci_low_pp", "ci_high_pp", "mcnemar_p", "holm_p")})


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:] or LAYERS)
