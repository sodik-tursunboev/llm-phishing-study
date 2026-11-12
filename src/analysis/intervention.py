"""The one causal test (PROTOCOL 5): a rule-based edit of a single property, applied to null-A.

python -m src.analysis.intervention <split>   (reads configs/intervention.json, declared beforehand)
-> results/intervention_<split>.json

configs/intervention.json names a layer, the property in words, and the word list that carries it,
taken from the accounting. Each listed word in the null-A text is replaced by its WordNet synonym
(the same rule as the lex baseline, so no LLM is involved), and nothing else changes. If the layer
loses detections on these edited messages, the property is sufficient for (part of) the LLM effect;
"share_of_llm_effect" says how much of the llm-vs-null-A change it reproduces.
"""
import json
import pathlib
import re
import sys

from src.analysis.primary import reading
from src.analysis.score import build, rewritten
from src.analysis.stats import cluster_bootstrap_ci, mcnemar_exact
from src.data.emails import plain_body
from src.rewrite.conditions import with_body
from src.rewrite.gates import check, clean
from src.rewrite.lex import _match_case, dose, synonym


def edit(text, words):
    """Replace each listed word (whole word, any case) with its WordNet synonym; links stay untouched."""
    for word in words:
        new = synonym(word.lower())
        if new:
            text = re.sub(rf"(?<![\w/.@-]){re.escape(word)}(?![\w/@-])",
                          lambda m: _match_case(new, m.group()), text, flags=re.IGNORECASE)
    return text


def main(split):
    config = json.loads(pathlib.Path("configs/intervention.json").read_text())
    layer = __import__(f"src.detectors.{config['layer']}", fromlist=["score"])
    threshold = json.loads(pathlib.Path("configs/thresholds.json").read_text())["layers"][config["layer"]]["threshold"]
    pairs = [(m, r) for m, r in rewritten(split) if m["label"] == "phishing" and not check(plain_body(m), clean(r))]
    fraction, flags, clusters = dose(), {"null_a": [], "edited": [], "llm": []}, []
    for msg, response in pairs:
        versions = build(msg, response, fraction)
        versions["edited"] = with_body(msg, edit(versions["null_a"]["text"], config["words"]))
        results = {k: layer.score(versions[k]) for k in flags}
        if any(r["error"] for r in results.values()):
            continue
        for k, r in results.items():
            flags[k].append(r["score"] > threshold)
        clusters.append(msg["cluster"])

    def contrast(b):
        diffs = [int(y) - int(x) for x, y in zip(flags["null_a"], flags[b])]
        lost = sum(x and not y for x, y in zip(flags["null_a"], flags[b]))
        gained = sum(y and not x for x, y in zip(flags["null_a"], flags[b]))
        low, high = cluster_bootstrap_ci(diffs, clusters)
        return {"net_pp": round(100 * sum(diffs) / len(diffs), 2), "ci_pp": [round(100 * low, 2), round(100 * high, 2)],
                "reading": reading(100 * low, 100 * high), "lost": lost, "gained": gained,
                "mcnemar_p": round(mcnemar_exact(lost, gained), 6)}

    out = {"config": config, "n": len(clusters), "point": "calibrated",
           "edited_vs_null_a": contrast("edited"), "llm_vs_null_a": contrast("llm")}
    llm = out["llm_vs_null_a"]["net_pp"]
    out["share_of_llm_effect"] = round(out["edited_vs_null_a"]["net_pp"] / llm, 3) if llm else None
    pathlib.Path(f"results/intervention_{split}.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
