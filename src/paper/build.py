"""Fill paper/manuscript.md's {{placeholders}} from result and config files: no number is typed by hand.

python -m src.paper.build   ->  paper/manuscript_filled.md, plus the word count and the list of
placeholders that have no value yet (they appear in the output as [MISSING name]).
"""
import csv
import json
import pathlib
import re

from src.data.prepare import REASONS

SOURCE = pathlib.Path("paper/manuscript.md")
OUTPUT = pathlib.Path("paper/manuscript_filled.md")


def _csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def values():
    v = {}
    sources = _csv("results/m1_sources.csv")
    for label in ("phishing", "ham"):
        rows = [r for r in sources if r["label"] == label]
        for column in ["read", "kept", *REASONS]:
            v[f"{label}_{column}"] = sum(int(r[column]) for r in rows)
    for r in _csv("results/m1_splits.csv"):
        v[f"{r['label']}_{r['split']}"] = int(r["messages"])
    l2 = json.loads(pathlib.Path("configs/tfidf_lr.json").read_text())
    v["l2_C"], v["l2_dev_auc"] = l2["C"], l2["dev_auc_by_C"][str(l2["C"])]
    thresholds = pathlib.Path("configs/thresholds.json")
    if thresholds.exists():
        for layer, t in json.loads(thresholds.read_text())["layers"].items():
            v[f"{layer}_threshold"] = round(t["threshold"], 2)
            v[f"{layer}_version"] = t["version"]
    pilot = json.loads(pathlib.Path("results/m3_pilot.json").read_text())
    v["lex_dose"] = f"{100 * pilot['change_fraction_passed']['median']:.1f}%"
    v["pilot_passed"] = pilot["gate_passed"]
    # Main results, once they exist: e.g. {{spamassassin_phishing_calibrated_llm_vs_null_a_net_pp}}
    primary = pathlib.Path("results/primary_test.csv")
    if primary.exists():
        for r in _csv(primary):
            if r["set"] == "gate_passed":
                key = f"{r['layer']}_{r['class']}_{r['point']}_{r['contrast'].replace(' ', '_')}"
                v |= {f"{key}_{k}": r[k] for k in r if k not in ("layer", "set", "class", "point", "contrast")}
    gates = pathlib.Path("results/gates_test.csv")
    if gates.exists():
        for r in _csv(gates):
            v |= {f"gates_{r['label']}_{k}": int(r[k]) for k in r if k != "label"}
    judge = pathlib.Path("results/judge.json")
    if judge.exists():
        out = json.loads(judge.read_text())
        v["judge_equivalent_rate"] = f"{100 * out['equivalent_rate']:.0f}%"
        v["judge_changed"] = sum(q["model_answers_changed_by_author"] for q in out["questions"].values())
    ratings = pathlib.Path("results/ratings.json")
    if ratings.exists():
        out = json.loads(ratings.read_text())
        v["ratings_equivalent_both"] = f"{100 * out['equivalent_both']:.0f}%"
        for q, s in out["questions"].items():
            v[f"kappa_{q}"], v[f"agreement_{q}"] = s["cohen_kappa"], f"{100 * s['agreement']:.0f}%"
    return v


def fmt(value):
    return f"{value:,}" if isinstance(value, int) else str(value)


def main():
    text = re.sub(r"<!--.*?-->\s*", "", SOURCE.read_text(encoding="utf-8"), flags=re.S)  # drop notes to authors
    v = values()
    missing = sorted(set(re.findall(r"\{\{(\w+)\}\}", text)) - set(v))
    filled = re.sub(r"\{\{(\w+)\}\}", lambda m: fmt(v[m[1]]) if m[1] in v else f"[MISSING {m[1]}]", text)
    OUTPUT.write_text(filled, encoding="utf-8")
    print(f"{OUTPUT}: {len(filled.split())} words; missing: {', '.join(missing) or 'none'}")


if __name__ == "__main__":
    main()
