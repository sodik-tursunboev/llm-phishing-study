"""Comparability judgment of the 30 rating pairs by a LOCAL model, checked by the first author.

This replaces the two-author blind rating (authors' decision, DEVIATIONS.md #20). The judge is
llama3.2:3b, a different model family from the generator, so the rewriter does not grade its own
work. It runs on the host's Ollama, so no email text leaves the machine. Claude Code sees only
counts. No inter-rater kappa is claimed: there is one model and one checking author.

python -m src.analysis.judge run      -> ratings/sheet_model.csv: the 30 pairs (same pairs as
    data/ratings_key.json), the model's four answers already filled in, and an EMPTY `checked` column
python -m src.analysis.judge summary  -> results/judge.json, once a human has read every pair,
    corrected any answer they disagree with, and typed their own name in `checked`

`checked` is never filled by code. The summary refuses to run while any pair is unchecked or any
answer is blank, and records per named person how many pairs they checked and answers they changed,
so the paper states exactly who checked what.

Needs network to reach the host's Ollama (like generate.py, DEVIATIONS.md #11).
"""
import csv
import hashlib
import json
import pathlib
import sys

from src.analysis.ratings import KEY, QUESTIONS, defang
from src.data.emails import plain_body
from src.rewrite.gates import clean
from src.rewrite.generate import ollama

MODEL = "llama3.2:3b"
DIGEST = "a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72"
PROMPT_FILE = pathlib.Path("prompts/judge.txt")
OPTIONS = {"temperature": 0, "seed": 42, "num_ctx": 8192}
SHEET = pathlib.Path("ratings/sheet_model.csv")
ANSWERS = pathlib.Path("data/judge_model_answers.json")  # the model's own answers, kept to count corrections


def judge(original, rewrite):
    prompt = f"{PROMPT_FILE.read_text(encoding='utf-8').strip()}\n\nORIGINAL:\n{original}\n\nREWRITE:\n{rewrite}"
    reply = ollama("/api/generate", {"model": MODEL, "prompt": prompt, "stream": False, "format": "json",
                                     "options": OPTIONS})
    return parse(reply["response"])


def parse(text):
    """The model's four answers. Anything but a clear yes/no is left blank for the author; never guessed."""
    try:
        answer = json.loads(text)
    except json.JSONDecodeError:
        answer = {}
    if not isinstance(answer, dict):
        answer = {}
    clear = lambda v: str(v).strip().lower() if str(v).strip().lower() in ("yes", "no") else ""  # noqa: E731
    return {q: clear(answer.get(q, "")) for q in QUESTIONS}


def run():
    digests = {m["name"]: m["digest"] for m in ollama("/api/tags")["models"]}
    if digests.get(MODEL) != DIGEST:
        raise SystemExit(f"{MODEL} on the server is {digests.get(MODEL)}, expected {DIGEST}")
    key = json.loads(KEY.read_text())
    with open("data/messages.jsonl", encoding="utf-8") as f:
        msgs = {m["id"]: m for m in map(json.loads, f) if m["id"] in key.values()}
    with open("data/rewrites/llm_test.jsonl", encoding="utf-8") as f:
        responses = {r["id"]: r["response"] for r in map(json.loads, f) if r["id"] in key.values()}
    answers, rows = {}, []
    for pair, mid in key.items():
        original, rewrite = plain_body(msgs[mid]), clean(responses[mid])
        answers[pair] = judge(original, rewrite)
        rows.append([pair, defang(original), defang(rewrite), *answers[pair].values(), "", ""])
    ANSWERS.write_text(json.dumps({"model": MODEL, "digest": DIGEST, "options": OPTIONS,
                                   "prompt_sha256": hashlib.sha256(PROMPT_FILE.read_bytes()).hexdigest(),
                                   "answers": answers}, indent=2))
    with open(SHEET, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["pair", "original", "rewrite", *QUESTIONS, "checked", "notes"])
        w.writerow(["(question)", "", "", *QUESTIONS.values(),
                    "type YOUR NAME (Sodik or Kavish) once you have read this pair", "optional"])
        w.writerows(rows)
    blanks = sum(v == "" for a in answers.values() for v in a.values())
    print(f"wrote {SHEET}: {len(rows)} pairs, {blanks} answers left blank by the model")


AUTHORS = {"sodik": "Sodik Tursunboev", "kavish": "Kavish"}  # what a checker types -> name in the paper


def checker(text):
    """The author who checked a pair, from what they typed in `checked`; None if no author name."""
    typed = text.strip().lower()
    return next((name for key, name in AUTHORS.items() if typed.startswith(key)), None)


def summary():
    model = json.loads(ANSWERS.read_text())["answers"]
    with open(SHEET, newline="", encoding="utf-8-sig") as f:
        final = {r["pair"]: r for r in csv.DictReader(f) if r["pair"].startswith("P")}
    who = {p: checker(r["checked"]) for p, r in final.items()}
    unchecked = [p for p, name in who.items() if name is None]
    if unchecked:
        raise SystemExit(f"not checked yet (no author name in `checked`): {', '.join(unchecked)}")
    blank = [p for p in final if any(final[p][q].strip().lower() not in ("yes", "no") for q in QUESTIONS)]
    if blank:
        raise SystemExit(f"answers still blank or not yes/no: {', '.join(blank)}")
    out = {"pairs": len(final), "judge": MODEL, "checked_by": {}, "questions": {}}
    for name in sorted(set(who.values())):
        mine = [p for p in final if who[p] == name]
        out["checked_by"][name] = {
            "pairs_checked": len(mine), "answers": 4 * len(mine),
            "answers_changed": sum(final[p][q].strip().lower() != model[p][q] for p in mine for q in QUESTIONS)}
    for q in QUESTIONS:
        changed = [p for p in final if final[p][q].strip().lower() != model[p][q]]
        yes = sum(final[p][q].strip().lower() == "yes" for p in final)
        out["questions"][q] = {"final_yes_rate": round(yes / len(final), 3),
                               "model_answers_changed": len(changed), "changed_pairs": changed}
    out["equivalent_rate"] = round(sum(all(final[p][q].strip().lower() == "yes" for q in QUESTIONS)
                                       for p in final) / len(final), 3)
    pathlib.Path("results/judge.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    {"run": run, "summary": summary}[sys.argv[1]]()
