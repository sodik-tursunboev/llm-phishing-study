"""L4 Lynceus, the authors' own detector, behind the common detector interface (LYNCEUS_NOTES.md).

Lynceus parses each message in a separate worker process. On Windows its launcher starts that
worker inside an AppContainer sandbox; on Linux the launcher refuses. We replace only the launcher:
the same worker code runs as a plain subprocess inside our offline container, which takes the
sandbox's place. Lynceus's parser, rules and scoring run unchanged.
"""
import hashlib
import pathlib
import resource
import subprocess
import sys
import time

from src.data.emails import render

ROOT = pathlib.Path("/opt/lynceus")  # snapshot of Lynceus core/ and rules/ (ENVIRONMENT.md)
sys.path.insert(0, str(ROOT))

from core import sandbox  # noqa: E402  (Lynceus modules from here on)
from core.contracts import VerdictState  # noqa: E402
from core.email.engine import ENGINE_VERSION, analyze_message  # noqa: E402
from rules.email.data import ruleset_version  # noqa: E402

PINNED = "d9c3ba88f9b995d9079434d39ad8d977dbb49b05"  # the evaluated version (LYNCEUS_NOTES.md)
COMMIT = (ROOT / "COMMIT").read_text().strip()
if COMMIT != PINNED:  # refuse to score with any other version of Lynceus
    raise RuntimeError(f"Lynceus snapshot is {COMMIT}, expected {PINNED}")
# Lynceus warns the user on these two states; UNKNOWN means "not enough to call it" and raises no warning.
FLAGGED = {VerdictState.MALICIOUS, VerdictState.SUSPICIOUS}


def _rules_hash():
    """SHA-256 over every file of Lynceus's rules/ folder (path and content), in sorted order."""
    h = hashlib.sha256()
    for path in sorted((ROOT / "rules").rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            h.update(str(path.relative_to(ROOT)).encode() + b"\0" + path.read_bytes())
    return h.hexdigest()


CONFIG_HASH = _rules_hash()


def _run_worker(script, stdin=b"", limits=sandbox.Limits()):
    """Stand-in for core.sandbox.run: same worker, same CPU, memory, time and output caps."""

    def cap():
        resource.setrlimit(resource.RLIMIT_CPU, (limits.cpu_seconds, limits.cpu_seconds))
        resource.setrlimit(resource.RLIMIT_AS, (limits.memory_mb * 2**20, limits.memory_mb * 2**20))

    start = time.monotonic()
    worker = ROOT / "core" / "sandbox" / "guest" / script
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-B", str(worker)], input=stdin, capture_output=True,
            timeout=limits.wall_seconds, preexec_fn=cap,
        )
    except subprocess.TimeoutExpired:
        return sandbox.Result(False, b"", "timeout", None, 0.0, 0.0, limits.wall_seconds, 0)
    too_big = len(proc.stdout) > limits.max_output_bytes
    ok = proc.returncode == 0 and not too_big
    reason = "ok" if ok else ("output_limit" if too_big else "crashed")
    return sandbox.Result(ok, proc.stdout if ok else b"", reason, proc.returncode, 0.0, 0.0,
                          time.monotonic() - start, 0)


sandbox.run = _run_worker  # the engine looks sandbox.run up at call time


def score(msg):
    """Common interface: one normalised message in, Lynceus's verdict out. Never raises.

    An ERROR or an unscored verdict (the engine gives a reason) is reported as an error with
    flagged=None: it is never counted as benign or as flagged (README section 5.4).
    """
    report = analyze_message(render(msg)).report
    verdict = report.verdict
    error = report.reason or ("error" if verdict.state is VerdictState.ERROR else None)
    return {
        "score": verdict.risk_score,
        "flagged": None if error else verdict.state in FLAGGED,
        "state": verdict.state.value,
        "evidence": sorted(s.rule_id for s in verdict.signals),
        "error": error,
        "version": f"lynceus {COMMIT[:12]} {ENGINE_VERSION} rules {ruleset_version()}",
        "config_hash": CONFIG_HASH,
    }
