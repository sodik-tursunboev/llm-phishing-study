"""Pre-commit scan: refuse to commit secrets, personal data or corpus files.

The patterns are deliberately simple and err towards false alarms: a hit blocks
the commit and an author decides. Run by hooks/pre-commit (see ENVIRONMENT.md).
"""
import re
import subprocess
import sys

# Raw corpora and rewrites live in data/ and must never be committed (README section 4).
BLOCKED_PATH = re.compile(r"^data/|\.(eml|mbox)$")  # top-level data/ only; src/data/ is code

PATTERNS = {
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "access token": re.compile(r"\b(ghp_|github_pat_|hf_|sk-|AKIA|xox[abp]-)[A-Za-z0-9_-]{16,}"),
    "email address": re.compile(r"[\w.+-]+@([\w-]+\.)+[A-Za-z]{2,}"),
    "phone number": re.compile(r"\+\d{1,3}[ -]?\(?\d{2,4}\)?[ -]?\d{3}[ -]?\d{3,4}\b"),
}

# RFC 2606 reserves these domains for examples, so test fixtures may use them.
EXAMPLE_EMAIL = re.compile(r"@([\w-]+\.)*example\.(com|org|net)$", re.IGNORECASE)


def find_problems(path, text):
    """Return one message per problem found in a file's path or content."""
    if BLOCKED_PATH.search(path):
        return [f"{path}: data or raw-mail file"]
    problems = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(line):
                if name == "email address" and EXAMPLE_EMAIL.search(match.group()):
                    continue
                problems.append(f"{path}:{lineno}: possible {name}")
    return problems


def staged_files():
    """Yield (path, content) for every file added or modified in the commit."""
    names = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    for name in names:
        blob = subprocess.run(["git", "show", f":{name}"], capture_output=True, check=True).stdout
        yield name, blob.decode("utf-8", errors="ignore")


if __name__ == "__main__":
    found = [p for path, text in staged_files() for p in find_problems(path, text)]
    for problem in found:
        print(problem, file=sys.stderr)
    if found:
        print("Commit blocked by hooks/scan.py. Remove the item, or ask your co-author.", file=sys.stderr)
    sys.exit(1 if found else 0)
