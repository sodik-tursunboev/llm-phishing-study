"""L4 adapter checks: Lynceus scores a message end to end offline, deterministically, and a worker
failure becomes an error, never a verdict. Needs the Lynceus snapshot volume (ENVIRONMENT.md)."""
import pathlib

import pytest

if not (pathlib.Path("/opt/lynceus") / "COMMIT").exists():
    pytest.skip("Lynceus snapshot not mounted at /opt/lynceus", allow_module_level=True)

from src.detectors import lynceus  # noqa: E402  (puts Lynceus on sys.path)

from core import sandbox  # noqa: E402  (Lynceus)


def message(html, sender="PayPal <service@paypal-secure.example.com>"):
    return {
        "headers": [("From", sender), ("To", "user@example.com"), ("Subject", "Account notice")],
        "subject": "Account notice", "text": "", "html": html, "urls": [],
    }


PHISH = message("<p>Your account is suspended. "
                "<a href='http://paypal.com.verify-login.example.net/signin'>Verify now</a></p>")


def test_scores_phish_end_to_end_and_deterministically():
    first, second = lynceus.score(PHISH), lynceus.score(PHISH)
    assert first == second
    assert first["error"] is None and first["flagged"] is True and first["evidence"]


def test_plain_message_is_scored_not_flagged():
    result = lynceus.score(message("<p>Minutes of Tuesday's meeting are attached below.</p>",
                                   sender="Alice <alice@example.org>"))
    assert result["error"] is None and result["flagged"] is False


def test_worker_failure_is_an_error_not_a_verdict(monkeypatch):
    def timed_out(script, stdin=b"", limits=sandbox.Limits()):
        return sandbox.Result(False, b"", "timeout", None, 0.0, 0.0, 0.0, 0)

    monkeypatch.setattr(sandbox, "run", timed_out)
    result = lynceus.score(PHISH)
    assert result["error"] == "parser_timeout" and result["flagged"] is None
