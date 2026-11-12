"""What exactly the orig -> null-A step changes, measured on the gate-passed pairs of a split.

python -m src.analysis.canonical <split>   ->  results/canonical_<split>.json   (counts only)

null-A is a controlled canonicalization, not a change of "format only". From the code:
- orig is the stored message rendered by render(): its scrubbed headers, plus its text and/or
  HTML part as UTF-8 MIME parts (multipart/alternative when both exist).
- null-A keeps the same headers, but the body becomes ONE text/plain UTF-8 part holding
  plain_body(): the original plain part if there is one (the HTML part is then dropped
  unchanged), otherwise the visible text of the HTML, with each http(s) link written after its
  anchor text as <URL>. Script, style, tags, attributes and every URL that appears only outside
  an anchor (images, CSS, forms) are lost.
- SpamAssassin and Lynceus read the full rendered message; TF-IDF reads subject + visible text,
  which for HTML-only messages now also contains the <URL> strings.
This script measures how often each of those changes happens.
"""
import json
import pathlib
import statistics
import sys

from src.analysis.score import rewritten
from src.data.emails import extract_urls, plain_body
from src.detectors.tfidf_lr import text as tfidf_text
from src.rewrite.conditions import null_a
from src.rewrite.gates import check, clean


def pct(flags):
    return round(100 * sum(flags) / len(flags), 1)


def main(split):
    pairs = [(m, r) for m, r in rewritten(split) if not check(plain_body(m), clean(r))]
    out = {}
    for label in ("phishing", "ham"):
        msgs = [m for m, _ in pairs if m["label"] == label]
        has_text = [bool(m["text"].strip()) for m in msgs]
        has_html = [bool(m["html"].strip()) for m in msgs]
        orig_urls = [set(m["urls"]) for m in msgs]
        null_urls = [set(extract_urls(plain_body(m), "")) for m in msgs]
        out[label] = {
            "n": len(msgs),
            "pct_with_html_part": pct(has_html),
            "pct_html_only_converted_to_text": pct([h and not t for h, t in zip(has_html, has_text)]),
            "pct_html_part_dropped_plain_part_kept": pct([h and t for h, t in zip(has_html, has_text)]),
            "median_distinct_urls_orig": statistics.median(len(u) for u in orig_urls),
            "median_distinct_urls_null_a": statistics.median(len(u) for u in null_urls),
            "pct_losing_at_least_one_url": pct([bool(o - n) for o, n in zip(orig_urls, null_urls)]),
            "pct_gaining_a_url": pct([bool(n - o) for o, n in zip(orig_urls, null_urls)]),
            "pct_tfidf_input_changed": pct([tfidf_text(m) != tfidf_text(null_a(m)) for m in msgs]),
        }
    pathlib.Path(f"results/canonical_{split}.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
