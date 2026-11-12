"""Condition lex: a deterministic synonym swap with no LLM, changing about as many words as the LLM.

If detection drops under llm but also under lex, the drop is "any rewording", not something the
LLM adds (README H3). The dose is the median change fraction of gate-passing pilot rewrites
(results/m3_pilot.json). Each chosen word becomes the first different single-word lemma of its
first WordNet 3.0 synset. Links, addresses, placeholders and words under four letters are never
touched (short words are mostly function words). The words to swap are drawn with a seed derived
from the message id, so every run gives the same text.
"""
import hashlib
import json
import pathlib
import random
import re
from functools import cache

from nltk.corpus import wordnet as wn

from src.data.emails import EMAIL_RE, URL_RE
from src.rewrite.conditions import words
from src.rewrite.gates import PLACEHOLDER_RE

WORD_RE = re.compile(r"[A-Za-z]{4,}")


def dose():
    return json.loads(pathlib.Path("results/m3_pilot.json").read_text())["change_fraction_passed"]["median"]


@cache
def synonym(word):
    """First single-word WordNet lemma that differs from the word and from its base form, or None
    (so "accounts" never becomes just "account")."""
    base = wn.morphy(word) or word
    for synset in wn.synsets(word):
        for lemma in synset.lemma_names():
            if lemma.isalpha() and lemma.lower() not in (word, base):
                return lemma.lower()
    return None


def _match_case(new, old):
    return new.upper() if old.isupper() and len(old) > 1 else new.capitalize() if old[0].isupper() else new


def lex(text, msg_id, fraction):
    """Swap words for synonyms until `fraction` of all words have changed, or no candidate is left."""
    protected = [m.span() for r in (URL_RE, EMAIL_RE, PLACEHOLDER_RE) for m in r.finditer(text)]
    candidates = [m for m in WORD_RE.finditer(text)
                  if synonym(m.group().lower()) and not any(a <= m.start() < b for a, b in protected)]
    wanted = min(len(candidates), round(fraction * len(words(text))))
    seed = int(hashlib.sha256(msg_id.encode()).hexdigest(), 16)
    chosen = sorted(random.Random(seed).sample(candidates, wanted), key=lambda m: m.start())
    out, last = [], 0
    for m in chosen:
        out += [text[last:m.start()], _match_case(synonym(m.group().lower()), m.group())]
        last = m.end()
    return "".join(out + [text[last:]])
