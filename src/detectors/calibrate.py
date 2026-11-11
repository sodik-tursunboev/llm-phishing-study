"""Fix each layer's dev-calibrated operating point and write configs/thresholds.json.

python -m src.detectors.calibrate [layer ...]   (default: all; after python -m src.detectors.run <layer> dev)
Naming layers updates only their entries, so one layer can be re-calibrated after a re-pin.

Rule (README section 5.4): flag a message when its score is above t, where t is the lowest dev ham
score with at most 1% of dev ham above it. Only dev originals are used: never test, never rewrites.
The file also records each layer's native operating point on dev, for the floor/ceiling check.
"""
import json
import pathlib
import sys

LAYERS = ["spamassassin", "tfidf_lr", "lynceus"]
TARGET_FPR = 0.01
OUT = pathlib.Path("configs/thresholds.json")


def threshold_at_fpr(ham_scores, target=TARGET_FPR):
    """Lowest observed ham score t such that at most `target` of the ham scores are above t."""
    n = len(ham_scores)
    return min(t for t in set(ham_scores) if sum(s > t for s in ham_scores) / n <= target)


def rate(flags):
    return round(sum(flags) / len(flags), 4)


def main(layers):
    with open("data/messages.jsonl", encoding="utf-8") as f:
        label = {m["id"]: m["label"] for m in map(json.loads, f) if m["split"] == "dev"}
    out = json.loads(OUT.read_text()) if OUT.exists() else {"layers": {}}
    out.update({"rule": "flag when score > threshold", "target_dev_fpr": TARGET_FPR})
    for layer in layers:
        with open(f"data/scores/{layer}_dev.jsonl", encoding="utf-8") as f:
            rows = [json.loads(line) for line in f]
        ok = [r for r in rows if r["error"] is None]
        ham = [r for r in ok if label[r["id"]] == "ham"]
        phish = [r for r in ok if label[r["id"]] == "phishing"]
        t = threshold_at_fpr([r["score"] for r in ham])
        out["layers"][layer] = {
            "threshold": t,
            "dev_fpr": rate([r["score"] > t for r in ham]),
            "dev_tpr": rate([r["score"] > t for r in phish]),
            "native_dev_fpr": rate([r["flagged"] for r in ham]),
            "native_dev_tpr": rate([r["flagged"] for r in phish]),
            "n_ham": len(ham), "n_phishing": len(phish), "errors": len(rows) - len(ok),
            "version": rows[0]["version"], "config_hash": rows[0]["config_hash"],
        }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({layer: out["layers"][layer] for layer in layers}, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:] or LAYERS)
