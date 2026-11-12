"""Pilot report (README M3): aggregate numbers only, written to results/m3_pilot.json.

python -m src.rewrite.pilot      (after: python -m src.rewrite.generate pilot)

Reports gate pass rates, refusals, runtime, how much wording the model changes (the dose the
lex baseline must match), the length-ratio spread (to fix the length band), and detection levels
per condition for the floor/ceiling check. Lynceus is left out until its new version is pinned.
"""
import json
import pathlib
import statistics
from collections import Counter

from src.data.emails import plain_body
from src.detectors import spamassassin, tfidf_lr
from src.rewrite.conditions import change_fraction, null_a, with_body
from src.rewrite.gates import GATES, check, clean

LAYERS = {"spamassassin": spamassassin, "tfidf_lr": tfidf_lr}


def quantiles(values):
    values = sorted(values)
    pick = lambda q: round(values[min(len(values) - 1, int(q * len(values)))], 3)  # noqa: E731
    return {"min": pick(0), "p10": pick(0.1), "median": pick(0.5), "p90": pick(0.9), "max": pick(1)}


def main():
    with open("data/messages.jsonl", encoding="utf-8") as f:
        msgs = {m["id"]: m for m in map(json.loads, f) if m["split"] == "pilot"}
    with open("data/rewrites/llm_pilot.jsonl", encoding="utf-8") as f:
        rewrites = {r["id"]: r for r in map(json.loads, f)}
    thresholds = json.loads(pathlib.Path("configs/thresholds.json").read_text())["layers"]

    failures, passed, ratios, doses = Counter(), [], [], []
    for mid, r in rewrites.items():
        if r["error"]:
            failures[r["error"]] += 1
            continue
        base, rewrite = plain_body(msgs[mid]), clean(r["response"])
        failed = check(base, rewrite) + ([] if r["done_reason"] == "stop" else ["truncated"])
        failures.update(failed)
        ratios.append(len(rewrite.split()) / max(1, len(base.split())))
        if not failed:
            passed.append(mid)
            doses.append(change_fraction(base, rewrite))

    detection = {}
    for name, layer in LAYERS.items():
        t = thresholds[name]["threshold"]
        for label in ("phishing", "ham"):
            ids = [i for i in passed if msgs[i]["label"] == label]
            for cond, make in (("orig", lambda m: m), ("null_a", null_a),
                               ("llm", lambda m: with_body(m, clean(rewrites[m["id"]]["response"])))):
                scores = [layer.score(make(msgs[i])) for i in ids]
                detection[f"{name} {label} {cond}"] = {
                    "native": round(sum(s["flagged"] for s in scores) / max(1, len(ids)), 3),
                    "calibrated": round(sum(s["score"] > t for s in scores) / max(1, len(ids)), 3),
                    "n": len(ids)}

    timed = [r for r in rewrites.values() if not r["error"]]
    report = {
        "messages": len(msgs), "rewritten": len(timed), "gate_passed": len(passed),
        "failures_by_gate": {g: failures[g] for g in [*GATES, "truncated", "too_long"]},
        "refusal_rate": round(failures["refusal"] / max(1, len(timed)), 3),
        "seconds_per_rewrite": quantiles([r["seconds"] for r in timed]),
        "output_tokens": quantiles([r["output_tokens"] for r in timed]),
        "length_ratio": quantiles(ratios),
        "change_fraction_passed": quantiles(doses),
        "detection_rate_on_gate_passed": detection,
    }
    pathlib.Path("results/m3_pilot.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
