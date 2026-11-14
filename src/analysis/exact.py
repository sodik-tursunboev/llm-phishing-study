"""Two descriptive additions made after the freeze (DEVIATIONS.md #24), computed from the main table only.

python -m src.analysis.exact <split>   ->  results/exact_<split>.csv, results/decomposition_<split>.csv

Both read results/primary_<split>.csv and nothing else, so they need no data volume and change no
score, threshold or pre-declared reading.

1. Paired score intervals. With zero or one discordant pair, the pre-declared cluster bootstrap
   returns [0, 0] or an interval that stops at 0, which overstates certainty. For every row of the
   main table, this adds Newcombe's paired score interval (src/analysis/stats.py) and the reading it
   would give under the same 2-point rule. It ignores template clusters, so it is a check on the
   bootstrap, not a replacement; with few discordant pairs it is slightly conservative.
2. End-to-end decomposition. llm vs orig is what an attacker who sends the model's plain-text output
   would get. The same messages are in every condition, so its net change is exactly the
   canonicalization step (null_a vs orig) plus the wording step (llm vs null_a).
"""
import csv
import sys

from src.analysis.primary import reading
from src.analysis.stats import paired_score_ci


def read(split):
    with open(f"results/primary_{split}.csv", newline="") as f:
        return list(csv.DictReader(f))


def table(row):
    """The paired 2x2 table behind one row: (both, lost, gained, neither)."""
    n, lost, gained = int(row["n"]), int(row["lost"]), int(row["gained"])
    flagged_a, flagged_b = round(float(row["rate_a"]) * n), round(float(row["rate_b"]) * n)
    both = flagged_a - lost
    assert both + gained == flagged_b, f"rates and counts disagree: {row}"
    return both, lost, gained, n - both - lost - gained


def exact_rows(rows):
    out = []
    for r in rows:
        low, high = (100 * x for x in paired_score_ci(*table(r)))
        out.append({k: r[k] for k in ("layer", "set", "class", "contrast", "point", "n", "lost", "gained",
                                      "net_pp", "ci_low_pp", "ci_high_pp", "reading")}
                   | {"exact_low_pp": round(low, 2), "exact_high_pp": round(high, 2),
                      "exact_reading": reading(low, high)})
    return out


def decomposition_rows(rows):
    get = {(r["layer"], r["set"], r["class"], r["point"], r["contrast"]): r for r in rows}
    out = []
    for (layer, aset, cls, point, contrast), wording in get.items():
        if contrast != "llm vs null_a":
            continue
        canon = get[(layer, aset, cls, point, "null_a vs orig")]
        # The identity holds only when both steps use the same messages.
        assert wording["n"] == canon["n"] and wording["excluded_errors"] == canon["excluded_errors"] == "0"
        n = int(wording["n"])
        step = {name: int(r["gained"]) - int(r["lost"]) for name, r in (("canon", canon), ("wording", wording))}
        out.append({"layer": layer, "set": aset, "class": cls, "point": point, "n": n,
                    "orig_pct": round(100 * float(canon["rate_a"]), 2),
                    "null_a_pct": round(100 * float(canon["rate_b"]), 2),
                    "llm_pct": round(100 * float(wording["rate_b"]), 2),
                    # From the counts, so the two steps add up exactly to the end-to-end change.
                    "canonicalization_pp": round(100 * step["canon"] / n, 2),
                    "wording_pp": round(100 * step["wording"] / n, 2),
                    "end_to_end_pp": round(100 * (step["canon"] + step["wording"]) / n, 2)})
    return out


def write(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main(split):
    rows = read(split)
    write(f"results/exact_{split}.csv", exact_rows(rows))
    write(f"results/decomposition_{split}.csv", decomposition_rows(rows))
    print(f"results/exact_{split}.csv, results/decomposition_{split}.csv from {len(rows)} rows")


if __name__ == "__main__":
    main(sys.argv[1])
