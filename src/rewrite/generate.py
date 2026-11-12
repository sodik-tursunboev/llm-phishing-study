"""Condition llm-G1: one neutral paraphrase per message by a local model, single pass, no feedback.

python -m src.rewrite.generate <split> [target_passing_per_class]
Writes data/rewrites/llm_<split>.jsonl (private). Resumable: messages already written are skipped.
Prints counts and timing only, never text. Talks only to the local Ollama server (OLLAMA_URL).

With a target, messages are taken in a fixed seeded order, alternating classes, and a class stops
once that many of its rewrites pass the comparability gates (README 5.1: at least 200 per class).
The stopping rule looks only at the gates, never at any detector.
"""
import hashlib
import itertools
import json
import os
import pathlib
import random
import sys
import time
import urllib.request
from collections import Counter

from src.data.emails import plain_body
from src.rewrite.gates import check, clean

MODEL = "gemma3:4b"
DIGEST = "68ceab7e468a31c988b44d5a4984a0e21f58c4f7158c6ce29c1804babac38df7"  # Ollama manifest SHA-256
PROMPT_FILE = pathlib.Path("prompts/paraphrase.txt")
PROMPT = PROMPT_FILE.read_text(encoding="utf-8").strip()
PROMPT_SHA256 = hashlib.sha256(PROMPT_FILE.read_bytes()).hexdigest()
OPTIONS = {"temperature": 0, "seed": 42, "num_ctx": 4096}  # greedy decoding, fixed seed and context
MAX_WORDS = 1200  # a longer body plus its rewrite would not fit the context; counted, not rewritten
URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434")


def ollama(path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(URL + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=600) as response:
        return json.loads(response.read())


def check_model():
    """Refuse to run unless the server holds exactly the pinned model."""
    digests = {m["name"]: m["digest"] for m in ollama("/api/tags")["models"]}
    if digests.get(MODEL) != DIGEST:
        raise RuntimeError(f"{MODEL} on the server is {digests.get(MODEL)}, expected {DIGEST}")


def paraphrase(text):
    return ollama("/api/generate", {"model": MODEL, "prompt": f"{PROMPT}\n\n{text}", "stream": False,
                                    "options": OPTIONS})


def ordered(split):
    """The split's messages: each class shuffled with seed 2026, then interleaved phishing, ham, ..."""
    with open("data/messages.jsonl", encoding="utf-8") as f:
        rows = [m for m in map(json.loads, f) if m["split"] == split]
    by_class = []
    for label in ("phishing", "ham"):
        mine = [m for m in rows if m["label"] == label]
        random.Random(2026).shuffle(mine)
        by_class.append(mine)
    return [m for pair in itertools.zip_longest(*by_class) for m in pair if m is not None]


def passes(msg, record):
    return not record.get("error") and record.get("done_reason") == "stop" and not check(
        plain_body(msg), clean(record["response"]))


def main(split, target=None):
    check_model()
    paraphrase("Hello, see you tomorrow.")  # warm-up: the first answer after loading can differ
    out = pathlib.Path(f"data/rewrites/llm_{split}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    records = [json.loads(line) for line in out.open(encoding="utf-8")] if out.exists() else []
    msgs = ordered(split)
    by_id = {m["id"]: m for m in msgs}
    done = {r["id"] for r in records}
    passing = Counter(by_id[r["id"]]["label"] for r in records if passes(by_id[r["id"]], r))
    todo = [m for m in msgs if m["id"] not in done]
    start, tokens, i = time.monotonic(), 0, 0
    with out.open("a", encoding="utf-8") as f:
        for msg in todo:
            if target is not None and passing[msg["label"]] >= target:
                if all(passing[c] >= target for c in ("phishing", "ham")):
                    break
                continue
            i += 1
            base = plain_body(msg)
            record = {"id": msg["id"], "model": MODEL, "digest": DIGEST, "prompt_sha256": PROMPT_SHA256,
                      "options": OPTIONS}
            if len(base.split()) > MAX_WORDS:
                record["error"] = "too_long"
            else:
                t = time.monotonic()
                r = paraphrase(base)
                tokens += r.get("eval_count", 0)
                record |= {"error": None, "response": r["response"], "done_reason": r.get("done_reason"),
                           "prompt_tokens": r.get("prompt_eval_count"), "output_tokens": r.get("eval_count"),
                           "seconds": round(time.monotonic() - t, 2)}
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
            passing[msg["label"]] += passes(msg, record)
            if i % 20 == 0:
                print(f"{i} new, passing {dict(passing)}, {time.monotonic() - start:.0f} s", flush=True)
    elapsed = time.monotonic() - start
    print(f"llm {split}: {i} new, {len(done)} already done, passing {dict(passing)}, {elapsed:.0f} s, "
          f"{tokens / max(elapsed, 1):.1f} output tokens/s")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
