"""L1 SpamAssassin behind the common detector interface.

One Perl worker (sa_worker.pl) loads the pinned rules once and scores each message with local
tests only, Bayes off and no learning (ENVIRONMENT.md). The native operating point is
SpamAssassin's own required score (5.0 by default); a dev-calibrated one is in configs/thresholds.json.
"""
import hashlib
import json
import pathlib
import selectors
import subprocess

from src.data.emails import render

WORKER = pathlib.Path(__file__).with_name("sa_worker.pl")
TIMEOUT = 60  # seconds per message; a hung check becomes an error, never a verdict
RULE_DIRS = [pathlib.Path("/usr/share/spamassassin"), pathlib.Path("/etc/spamassassin")]


def _config_hash():
    """SHA-256 over the shipped rules, the site config and our worker (paths and contents, sorted)."""
    h = hashlib.sha256()
    files = [p for d in RULE_DIRS for p in d.rglob("*") if p.is_file()] + [WORKER]
    for path in sorted(files):
        h.update(str(path).encode() + b"\0" + path.read_bytes())
    return h.hexdigest()


CONFIG_HASH = _config_hash()
_proc, _header = None, None


def _start():
    global _proc, _header
    _proc = subprocess.Popen(["perl", str(WORKER)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    _header = json.loads(_proc.stdout.readline())


def _answer(raw):
    """Send one message to the worker; return its JSON answer, or None after TIMEOUT."""
    _proc.stdin.write(f"{len(raw)}\n".encode() + raw)
    _proc.stdin.flush()
    with selectors.DefaultSelector() as sel:
        sel.register(_proc.stdout, selectors.EVENT_READ)
        if not sel.select(TIMEOUT):
            return None
    line = _proc.stdout.readline()
    return json.loads(line) if line else None


def score(msg):
    """Common interface: one normalised message in, SpamAssassin's verdict out. Never raises."""
    if _proc is None or _proc.poll() is not None:
        _start()
    answer = _answer(render(msg))
    version = f"SpamAssassin {_header['version']} scoreset {_header['scoreset']}"
    if answer is None:  # timeout or worker death: restart for the next message, report an error
        _proc.kill()
        _proc.wait()
        return {"score": None, "flagged": None, "evidence": {}, "error": "timeout_or_crash",
                "version": version, "config_hash": CONFIG_HASH}
    return {
        "score": answer["score"],
        "flagged": answer["score"] >= answer["required"],
        "evidence": answer["hits"],  # rule name -> points (score is their sum)
        "error": None,
        "version": version,
        "config_hash": CONFIG_HASH,
    }
