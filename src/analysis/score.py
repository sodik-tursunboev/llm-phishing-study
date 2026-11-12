"""Score all four conditions of every rewritten message of a split with one layer, offline.

python -m src.analysis.score <layer> <split>   ->  data/scores/<layer>_conditions_<split>.jsonl
For test data this runs only after the freeze (PROTOCOL.md). Prints counts, errors and a hash only.
"""
import hashlib
import importlib
import json
import pathlib
import sys
from collections import Counter

from src.data.emails import plain_body
from src.rewrite.conditions import with_body
from src.rewrite.gates import clean
from src.rewrite.lex import dose, lex

CONDITIONS = ["orig", "null_a", "lex", "llm"]


def build(msg, response, fraction):
    """The four versions of one message: original, plain-text copy, synonym swap, LLM rewrite."""
    base = plain_body(msg)
    return {"orig": msg, "null_a": with_body(msg, base), "lex": with_body(msg, lex(base, msg["id"], fraction)),
            "llm": with_body(msg, clean(response))}


def rewritten(split):
    """(message, response) for every message of the split with a model answer, in file order."""
    with open("data/messages.jsonl", encoding="utf-8") as f:
        msgs = {m["id"]: m for m in map(json.loads, f) if m["split"] == split}
    with open(f"data/rewrites/llm_{split}.jsonl", encoding="utf-8") as f:
        return [(msgs[r["id"]], r["response"]) for r in map(json.loads, f) if not r.get("error")]


def main(layer, split):
    detector = importlib.import_module(f"src.detectors.{layer}")
    out = pathlib.Path(f"data/scores/{layer}_conditions_{split}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    fraction, errors, n = dose(), Counter(), 0
    with out.open("w", encoding="utf-8") as f:
        for msg, response in rewritten(split):
            for condition, version in build(msg, response, fraction).items():
                result = detector.score(version)
                errors[(condition, result["error"])] += result["error"] is not None
                f.write(json.dumps({"id": msg["id"], "condition": condition, **result}, sort_keys=True) + "\n")
            n += 1
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"{layer} {split}: {n} messages x {len(CONDITIONS)} conditions, errors "
          f"{ {f'{c}:{e}': k for (c, e), k in errors.items() if k} }, output sha256 {digest}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
