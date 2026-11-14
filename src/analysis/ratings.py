"""The blind rating of the 30 pairs by both authors (planned in scope v3; prepared but not carried out, DEVIATIONS.md #25).

python -m src.analysis.ratings make    ->  ratings/sheet_sodik.csv and ratings/sheet_kavish.csv
python -m src.analysis.ratings kappa   ->  results/ratings.json (agreement, Cohen's kappa with a
                                           bootstrap CI, and how often the model judge agreed)
Rules: each author rates alone, without the model's answers. The AI assistant never rates.

The 30 pairs are the first 15 phishing and first 15 legitimate test rewrites that pass every gate,
in generation order (itself a seeded random order, so this is a random sample, and the same 30 pairs
come out however far generation has run). They are shown in an order shuffled with seed 2026,
without labels or detector output. Links and
addresses are defanged (hxxp, [.], [at]) so nothing in the sheet is clickable. The sheets hold email
text, so ratings/ is git-ignored; the key (pair -> message id) stays in the private data volume.
"""
import csv
import hashlib
import json
import pathlib
import random
import sys

from src.analysis.score import rewritten
from src.data.emails import EMAIL_RE, URL_RE, plain_body
from src.rewrite.gates import check, clean

QUESTIONS = {
    "same_action": "Does the rewrite ask the reader to do the same thing? (yes/no)",
    "same_target": "Same sender, target, links, names and numbers? (yes/no)",
    "same_urgency": "Same level of urgency or pressure? (yes/no)",
    "same_label": "Would you still call it phishing / legitimate, as the original? (yes/no)",
}
RATERS = ["sodik", "kavish"]
KEY = pathlib.Path("data/ratings_key.json")


def defang(text):
    text = URL_RE.sub(lambda m: m.group().replace("http", "hxxp", 1).replace(".", "[.]"), text)
    return EMAIL_RE.sub(lambda m: m.group().replace("@", "[at]").replace(".", "[.]"), text)


def make():
    passed = [(m, r) for m, r in rewritten("test") if not check(plain_body(m), clean(r))]  # generation order
    chosen = []
    for label in ("phishing", "ham"):
        mine = [p for p in passed if p[0]["label"] == label][:15]
        if len(mine) < 15:
            raise SystemExit(f"only {len(mine)} gate-passing {label} rewrites so far; need 15")
        chosen += mine
    random.Random(2026).shuffle(chosen)
    key = {f"P{i:02d}": m["id"] for i, (m, _) in enumerate(chosen, 1)}
    # The same 30 pairs as the model judge (judge.py reads this key), never a new draw.
    if KEY.exists() and json.loads(KEY.read_text()) != key:
        raise SystemExit(f"{KEY} names other pairs than this split gives; nothing written")
    # Never overwrite a sheet someone may already be filling in.
    existing = [str(sheet(r)) for r in RATERS if sheet(r).exists()]
    if existing:
        raise SystemExit(f"{', '.join(existing)} already exist; nothing written")
    KEY.write_text(json.dumps(key, indent=2))
    pathlib.Path("ratings").mkdir(exist_ok=True)
    for rater in RATERS:
        with open(sheet(rater), "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["pair", "original", "rewrite", *QUESTIONS, "notes"])
            w.writerow(["(question)", "", "", *QUESTIONS.values(), "optional"])
            for i, (m, response) in enumerate(chosen, 1):
                w.writerow([f"P{i:02d}", defang(plain_body(m)), defang(clean(response)), "", "", "", "", ""])
    print(f"wrote {sheet('sodik')} and {sheet('kavish')} ({len(chosen)} pairs each)")


def sheet(rater):
    return pathlib.Path(f"ratings/sheet_{rater}.csv")


def cohen_kappa(a, b):
    """Agreement beyond chance: (observed - expected) / (1 - expected), where "expected" is the
    agreement two raters would reach by chance with their own yes-rates. None when it is undefined:
    if both raters give one and the same answer to every pair, expected agreement is 1."""
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    expected = sum((a.count(v) / n) * (b.count(v) / n) for v in set(a) | set(b))
    return None if expected == 1 else (observed - expected) / (1 - expected)


def kappa_ci(a, b, seed=2026, resamples=2000):
    """95% percentile CI of kappa, resampling pairs; None if kappa is undefined in most resamples."""
    rng, n, values = random.Random(seed), len(a), []
    for _ in range(resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        k = cohen_kappa([a[i] for i in idx], [b[i] for i in idx])
        if k is not None:
            values.append(k)
    if len(values) < resamples / 2:
        return None
    values.sort()
    return values[int(0.025 * len(values))], values[int(0.975 * len(values)) - 1]


def read_sheets():
    """Both raters' answers, refusing to go on while any answer is blank or not yes/no."""
    sheets, hashes = {}, {}
    for rater in RATERS:
        raw = sheet(rater).read_bytes()
        hashes[rater] = hashlib.sha256(raw).hexdigest()  # lets a reviewer check the private sheets later
        rows = csv.DictReader(raw.decode("utf-8-sig").splitlines())
        sheets[rater] = {r["pair"]: r for r in rows if r["pair"].startswith("P")}
    pairs = sorted(sheets[RATERS[0]])
    if sorted(sheets[RATERS[1]]) != pairs:
        raise SystemExit("the two sheets do not hold the same pairs")
    answers = {r: {q: [sheets[r][p][q].strip().lower() for p in pairs] for q in QUESTIONS} for r in RATERS}
    bad = [f"{r} {p} {q}" for r in RATERS for q in QUESTIONS for p, v in zip(pairs, answers[r][q])
           if v not in ("yes", "no")]
    if bad:
        raise SystemExit(f"{len(bad)} answers are blank or not yes/no, e.g. {'; '.join(bad[:5])}")
    return pairs, answers, hashes


def kappa():
    pairs, answers, hashes = read_sheets()
    a_name, b_name = RATERS
    model_file = pathlib.Path("data/judge_model_answers.json")  # the llama judge's own answers, if run
    model = json.loads(model_file.read_text())["answers"] if model_file.exists() else None
    out = {"pairs": len(pairs), "sheet_sha256": hashes, "questions": {}}
    for q in QUESTIONS:
        a, b = answers[a_name][q], answers[b_name][q]
        k, ci = cohen_kappa(a, b), kappa_ci(a, b)
        out["questions"][q] = {
            "agreement": round(sum(x == y for x, y in zip(a, b)) / len(pairs), 3),
            "cohen_kappa": None if k is None else round(k, 3),
            "kappa_ci": None if ci is None else [round(ci[0], 3), round(ci[1], 3)],
            "yes_rate": {r: round(answers[r][q].count("yes") / len(pairs), 3) for r in RATERS},
            "disagreements": [p for p, x, y in zip(pairs, a, b) if x != y],
        }
        if model:  # how often the model judge gave the same answer as each author
            out["questions"][q]["model_agrees_with"] = {
                r: round(sum(model[p][q] == v for p, v in zip(pairs, answers[r][q])) / len(pairs), 3)
                for r in RATERS}
    equivalent = {r: [all(answers[r][q][i] == "yes" for q in QUESTIONS) for i in range(len(pairs))]
                  for r in RATERS}
    out["equivalent_rate"] = {r: round(sum(v) / len(pairs), 3) for r, v in equivalent.items()}
    out["equivalent_both"] = round(sum(x and y for x, y in zip(*equivalent.values())) / len(pairs), 3)
    pathlib.Path("results/ratings.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    {"make": make, "kappa": kappa}[sys.argv[1]]()
