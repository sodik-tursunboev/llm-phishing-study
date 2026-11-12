"""Pre-declared comparability gates: a rewrite enters the analysis only if it keeps every link, number
and entity of the original, has a similar length, is English, and adds no refusal or meta-text
(README section 5.3). Failures are counted per gate, never silently dropped.

Fixed after the pilot (DEVIATIONS.md #14): links, numbers and entities are compared as sets, after
removing formatting that does not change meaning ("2,500" = "2500"; a trailing "/" or "." on a
link). A leading "Here is the rewritten email:" line is removed from model output before gating.
"""
import re

from src.data.emails import EMAIL_RE, URL_RE, extract_urls, is_english

LENGTH_BAND = (0.5, 2.0)  # rewrite words / original words
NUMBER_RE = re.compile(r"\d+(?:[.,:/-]\d+)*")
PLACEHOLDER_RE = re.compile(r"\[(?:NAME|PHONE)\]")
REFUSAL_RE = re.compile(
    r"\b(?:I can(?:no|')t|I am unable|I'm unable|I won't|as an AI|I must decline|"
    r"(?:cannot|can't|unable to) (?:help|assist|comply|fulfil|fulfill))", re.IGNORECASE)
META_RE = re.compile(r"^\s*(?:sure|certainly|okay|ok|here(?:'s| is| are))\b|rewritten (?:email|version|text)",
                     re.IGNORECASE)
GATES = ["refusal", "meta_text", "urls", "numbers", "entities", "length", "language"]


def clean(response):
    """Deterministic clean-up of model output: drop leading blank lines and leading lines such as
    "Here's a rewritten version of the email:" (a meta line that ends with a colon)."""
    lines = response.strip().splitlines()
    while lines and (not lines[0].strip() or (META_RE.search(lines[0]) and lines[0].rstrip().endswith(":"))):
        lines.pop(0)
    return "\n".join(lines).strip()


def numbers(text):
    """Numbers outside links and addresses, without thousands or decimal separators."""
    return {re.sub(r"[.,]", "", n) for n in NUMBER_RE.findall(EMAIL_RE.sub(" ", URL_RE.sub(" ", text)))}


def links(text):
    return {u.rstrip("/.") for u in extract_urls(text, "")}


def entities(text):
    return {m.group() for m in EMAIL_RE.finditer(text)} | set(PLACEHOLDER_RE.findall(text))


def check(base, rewrite):
    """Names of the gates a (cleaned) rewrite fails against its plain-text original; empty = passes.

    Refusal and meta-text count only when the rewrite has more of them than the original, so an
    original that says "I can't make it" is not mistaken for a refusal.
    """
    failed = []
    if len(REFUSAL_RE.findall(rewrite)) > len(REFUSAL_RE.findall(base)):
        failed.append("refusal")
    if len(META_RE.findall(rewrite)) > len(META_RE.findall(base)):
        failed.append("meta_text")
    if links(rewrite) != links(base):
        failed.append("urls")
    if numbers(rewrite) != numbers(base):
        failed.append("numbers")
    if entities(rewrite) != entities(base):
        failed.append("entities")
    ratio = len(rewrite.split()) / max(1, len(base.split()))
    if not LENGTH_BAND[0] <= ratio <= LENGTH_BAND[1]:
        failed.append("length")
    if not is_english(rewrite):
        failed.append("language")
    return failed
