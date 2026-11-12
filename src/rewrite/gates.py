"""Pre-declared comparability gates: a rewrite enters the analysis only if it keeps the original's
links, numbers and entities, has a similar length, is English, and adds no refusal or meta-text
(README section 5.3). Failures are counted per gate, never silently dropped.
"""
import re
from collections import Counter

from src.data.emails import EMAIL_RE, URL_RE, extract_urls, is_english

LENGTH_BAND = (0.5, 2.0)  # rewrite words / original words; proposal, to be fixed at the freeze
NUMBER_RE = re.compile(r"\d+(?:[.,:/-]\d+)*")
PLACEHOLDER_RE = re.compile(r"\[(?:NAME|PHONE)\]")
REFUSAL_RE = re.compile(
    r"\b(?:I can(?:no|')t|I am unable|I'm unable|I won't|as an AI|I must decline|"
    r"(?:cannot|can't|unable to) (?:help|assist|comply|fulfil|fulfill))", re.IGNORECASE)
META_RE = re.compile(r"^\s*(?:sure|certainly|okay|ok|here(?:'s| is| are))\b|rewritten (?:email|version|text)",
                     re.IGNORECASE)
GATES = ["refusal", "meta_text", "urls", "numbers", "entities", "length", "language"]


def numbers(text):
    return NUMBER_RE.findall(EMAIL_RE.sub(" ", URL_RE.sub(" ", text)))


def entities(text):
    return [m.group() for m in EMAIL_RE.finditer(text)] + PLACEHOLDER_RE.findall(text)


def check(base, rewrite):
    """Names of the gates a rewrite fails against its plain-text original; empty means it passes.

    Refusal and meta-text count only when the rewrite has more of them than the original, so an
    original that says "I can't make it" is not mistaken for a refusal.
    """
    failed = []
    if len(REFUSAL_RE.findall(rewrite)) > len(REFUSAL_RE.findall(base)):
        failed.append("refusal")
    if len(META_RE.findall(rewrite)) > len(META_RE.findall(base)):
        failed.append("meta_text")
    if Counter(extract_urls(rewrite, "")) != Counter(extract_urls(base, "")):
        failed.append("urls")
    if Counter(numbers(rewrite)) != Counter(numbers(base)):
        failed.append("numbers")
    if Counter(entities(rewrite)) != Counter(entities(base)):
        failed.append("entities")
    ratio = len(rewrite.split()) / max(1, len(base.split()))
    if not LENGTH_BAND[0] <= ratio <= LENGTH_BAND[1]:
        failed.append("length")
    if not is_english(rewrite):
        failed.append("language")
    return failed
