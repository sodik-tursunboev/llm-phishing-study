"""Accounting (README 6.2, level 2): what moved between null-A and the LLM rewrite, per layer.

python -m src.analysis.accounting <split>   ->  results/accounting_<split>.csv

This shows WHAT changed, not WHY; a cause is claimed only after the intervention (PROTOCOL 5).
- SpamAssassin: its score is a sum of rule points, so each rule's share of the change is exact.
- TF-IDF: the logit is a sum of token contributions (TF-IDF weight x coefficient), also exact.
- Lynceus: which rules stop or start firing.
Rows are means over gate-passed phishing messages. Words are listed only if they occur in at least
5 messages, so no rare, identifying word reaches the results.
"""
import csv
import json
import sys
from collections import Counter, defaultdict

from src.analysis.score import build, rewritten
from src.data.emails import plain_body
from src.rewrite.gates import check, clean
from src.rewrite.lex import dose

MIN_MESSAGES = 5
TOP = 15


def scores(layer, split):
    with open(f"data/scores/{layer}_conditions_{split}.jsonl", encoding="utf-8") as f:
        return {(s["id"], s["condition"]): s for s in map(json.loads, f)}


def token_changes(pairs):
    """Mean change per token of its logit contribution, from null-A to llm (exact decomposition)."""
    from src.detectors import tfidf_lr

    tfidf_lr._load()
    vectorizer, classifier = tfidf_lr._model.named_steps.values()
    names, coef = tfidf_lr._names, classifier.coef_[0]
    total, seen = defaultdict(float), Counter()
    fraction = dose()
    for msg, response in pairs:
        versions = build(msg, response, fraction)
        x = vectorizer.transform([tfidf_lr.text(versions["null_a"]), tfidf_lr.text(versions["llm"])])
        diff = (x[1] - x[0]).tocoo()
        for j, value in zip(diff.col, diff.data):
            total[names[j]] += value * coef[j]
        logits = classifier.decision_function(x)
        assert abs(sum(v * coef[j] for j, v in zip(diff.col, diff.data)) - (logits[1] - logits[0])) < 1e-9, \
            "token contributions must add up to the logit change"
        seen.update({names[j] for j in set(x[0].indices) | set(x[1].indices)})
    n = len(pairs)
    return {t: total[t] / n for t in total if seen[t] >= MIN_MESSAGES}


def main(split):
    pairs = [(m, r) for m, r in rewritten(split)
             if m["label"] == "phishing" and not check(plain_body(m), clean(r))]
    ids = [m["id"] for m, _ in pairs]
    rows = []
    sa = scores("spamassassin", split)
    change = defaultdict(float)
    for i in ids:
        a, b = sa[(i, "null_a")]["evidence"], sa[(i, "llm")]["evidence"]
        for rule in set(a) | set(b):
            change[rule] += (b.get(rule, 0) - a.get(rule, 0)) / len(ids)
    rows += [{"layer": "spamassassin", "item": k, "mean_change": round(v, 4)}
             for k, v in sorted(change.items(), key=lambda kv: kv[1])[:TOP] if v]
    rows += [{"layer": "tfidf_lr", "item": k, "mean_change": round(v, 4)}
             for k, v in sorted(token_changes(pairs).items(), key=lambda kv: kv[1])[:TOP]]
    try:
        ly = scores("lynceus", split)
        fired = Counter()
        for i in ids:
            a, b = set(ly[(i, "null_a")]["evidence"]), set(ly[(i, "llm")]["evidence"])
            fired.update({f"{r} stops": 1 for r in a - b})
            fired.update({f"{r} starts": 1 for r in b - a})
        rows += [{"layer": "lynceus", "item": k, "mean_change": round(v / len(ids), 4)}
                 for k, v in fired.most_common(TOP)]
    except FileNotFoundError:
        pass
    with open(f"results/accounting_{split}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["layer", "item", "mean_change"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(ids)} gate-passed phishing messages; {len(rows)} rows -> results/accounting_{split}.csv")


if __name__ == "__main__":
    main(sys.argv[1])
