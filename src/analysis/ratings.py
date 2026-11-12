"""The blind human rating (scope v3): both authors rate the same 30 pairs; Claude Code never rates.

python -m src.analysis.ratings make    ->  ratings/sheet_sodiq.csv and ratings/sheet_kavish.csv
python -m src.analysis.ratings kappa   ->  results/ratings.json (agreement and Cohen's kappa)

The 30 pairs are 15 phishing and 15 legitimate test messages whose rewrite passed every gate,
drawn with seed 2026 and shown in shuffled order without labels or detector output. Links and
addresses are defanged (hxxp, [.], [at]) so nothing in the sheet is clickable. The sheets hold email
text, so ratings/ is git-ignored; the key (pair -> message id) stays in the private data volume.
"""
import csv
import json
import pathlib
import random
import sys

from sklearn.metrics import cohen_kappa_score

from src.analysis.score import rewritten
from src.data.emails import EMAIL_RE, URL_RE, plain_body
from src.rewrite.gates import check, clean

QUESTIONS = {
    "same_action": "Does the rewrite ask the reader to do the same thing? (yes/no)",
    "same_target": "Same sender, target, links, names and numbers? (yes/no)",
    "same_urgency": "Same level of urgency or pressure? (yes/no)",
    "same_label": "Would you still call it phishing / legitimate, as the original? (yes/no)",
}
RATERS = ["sodiq", "kavish"]
KEY = pathlib.Path("data/ratings_key.json")


def defang(text):
    text = URL_RE.sub(lambda m: m.group().replace("http", "hxxp", 1).replace(".", "[.]"), text)
    return EMAIL_RE.sub(lambda m: m.group().replace("@", "[at]").replace(".", "[.]"), text)


def make():
    passed = [(m, r) for m, r in rewritten("test") if not check(plain_body(m), clean(r))]
    rng = random.Random(2026)
    chosen = []
    for label in ("phishing", "ham"):
        chosen += rng.sample([p for p in passed if p[0]["label"] == label], 15)
    rng.shuffle(chosen)
    KEY.write_text(json.dumps({f"P{i:02d}": m["id"] for i, (m, _) in enumerate(chosen, 1)}, indent=2))
    pathlib.Path("ratings").mkdir(exist_ok=True)
    for rater in RATERS:
        with open(f"ratings/sheet_{rater}.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["pair", "original", "rewrite", *QUESTIONS, "notes"])
            w.writerow(["(question)", "", "", *QUESTIONS.values(), "optional"])
            for i, (m, response) in enumerate(chosen, 1):
                w.writerow([f"P{i:02d}", defang(plain_body(m)), defang(clean(response)), "", "", "", "", ""])
    print(f"wrote ratings/sheet_sodiq.csv and ratings/sheet_kavish.csv ({len(chosen)} pairs each)")


def kappa():
    sheets = {}
    for rater in RATERS:
        with open(f"ratings/sheet_{rater}.csv", newline="", encoding="utf-8-sig") as f:
            sheets[rater] = {r["pair"]: r for r in csv.DictReader(f) if r["pair"].startswith("P")}
    pairs = sorted(sheets[RATERS[0]])
    answer = lambda rater, p, q: sheets[rater][p][q].strip().lower()  # noqa: E731
    out = {"pairs": len(pairs), "questions": {}}
    for q in QUESTIONS:
        a, b = ([answer(r, p, q) for p in pairs] for r in RATERS)
        out["questions"][q] = {
            "agreement": round(sum(x == y for x, y in zip(a, b)) / len(pairs), 3),
            "cohen_kappa": round(float(cohen_kappa_score(a, b)), 3),
            "yes_rate": {r: round([answer(r, p, q) for p in pairs].count("yes") / len(pairs), 3) for r in RATERS},
            "disagreements": [p for p, x, y in zip(pairs, a, b) if x != y],
        }
    equivalent = {r: [all(answer(r, p, q) == "yes" for q in QUESTIONS) for p in pairs] for r in RATERS}
    out["equivalent_rate"] = {r: round(sum(v) / len(pairs), 3) for r, v in equivalent.items()}
    out["equivalent_both"] = round(sum(x and y for x, y in zip(*equivalent.values())) / len(pairs), 3)
    pathlib.Path("results/ratings.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    {"make": make, "kappa": kappa}[sys.argv[1]]()
