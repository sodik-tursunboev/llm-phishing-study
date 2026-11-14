"""How many rewrites carry a "Subject:" line in their body (why the TF-IDF word "subject" moved
under the LLM rewrite, results/accounting_test.csv). TF-IDF reads the subject's content, not the word "Subject",
so the word can only come from the body. Prints counts only, never email text (README section 4).

python -m src.analysis.subject_lines <split>
"""
import sys

from src.analysis.score import rewritten
from src.data.emails import plain_body
from src.rewrite.gates import check, clean


def has_subject_line(text):
    """True if any line of the text starts with "Subject:" (any case, leading spaces allowed)."""
    return any(line.strip().lower().startswith("subject:") for line in text.splitlines())


def main(split):
    pairs = rewritten(split)
    passed = [(m, r) for m, r in pairs if not check(plain_body(m), clean(r))]
    for name, chosen in (("all rewrites", pairs), ("gate-passed", passed)):
        for label in ("phishing", "ham"):
            mine = [(m, r) for m, r in chosen if m["label"] == label]
            in_rewrite = sum(has_subject_line(clean(r)) for _, r in mine)
            in_null_a = sum(has_subject_line(plain_body(m)) for m, _ in mine)
            print(f"{name}, {label}: {in_rewrite} of {len(mine)} rewrites have a 'Subject:' line in the body "
                  f"({in_null_a} of their null-A texts do)")


if __name__ == "__main__":
    main(sys.argv[1])
