"""The derived conditions. Each keeps the original headers and carries a plain-text body.

Rewriting needs plain text, so every derived condition is plain text: null-A (the original body as
plain text, no LLM), lex and llm. Comparing llm with null-A therefore changes only the wording;
orig versus null-A measures the effect of the plain-text format itself (DEVIATIONS.md).
"""
import difflib
import re

from src.data.emails import extract_urls, plain_body


def with_body(msg, text):
    """The same message (same headers) with `text` as its only, plain-text body."""
    return {**msg, "text": text, "html": "", "urls": extract_urls(text, "")}


def null_a(msg):
    return with_body(msg, plain_body(msg))


def words(text):
    return re.findall(r"\w+", text.lower())


def change_fraction(base, rewrite):
    """Share of the original's words that do not survive, in order, into the rewrite (0 = identical)."""
    a, b = words(base), words(rewrite)
    kept = sum(block.size for block in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())
    return 1 - kept / len(a) if a else 0.0
