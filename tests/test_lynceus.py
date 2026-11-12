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


def test_reported_scores_are_passed_through_unchanged():
    result = lynceus.score(PHISH)
    assert result["reported_score"] is not None and result["score"] == result["reported_score"]


def test_an_unknown_verdict_gets_its_score_below_the_line():
    """Lynceus reports no score for UNKNOWN; the adapter gives the risk it computed (PROTOCOL 4)."""
    weak = message("<p>Please see the schedule for next week.</p>", sender="Alice <alice@example.org>")
    weak["headers"].append(("Reply-To", "billing@other-company.example.net"))
    result = lynceus.score(weak)
    assert result["state"] == "UNKNOWN" and result["reported_score"] is None
    assert result["evidence"] and 0 < result["score"] < 45 and result["flagged"] is False


def test_nothing_fired_scores_zero():
    result = lynceus.score(message("<p>Lunch at noon?</p>", sender="Alice <alice@example.org>"))
    assert result["evidence"] == [] and result["score"] == 0 and result["reported_score"] is None


def test_full_range_score_is_lynceus_own_arithmetic():
    """Over many random sets of Lynceus's own rules: whenever Lynceus reports a score, the full-range
    score is that same number; whenever it reports none, the full-range score is below its line."""
    import random
    from types import SimpleNamespace

    from core.contracts import Signal
    from rules.email import RULES

    cfg = lynceus.scoring()
    weights = cfg["weights"]
    rules = [(r.id, r.category) for r in RULES if r.id in weights]
    rng = random.Random(2026)
    reported = unreported = 0
    for _ in range(3000):
        picked = rng.sample(rules, rng.randint(1, 6))
        signals = [Signal(rule_id=i, category=c, weight=weights[i], description=i) for i, c in picked]
        own = lynceus.lynceus_scoring(signals, False, cfg).risk_score
        full = lynceus.full_range_score(SimpleNamespace(risk_score=None, signals=signals))
        if own is None:
            unreported += 1
            assert 0 <= full < cfg["thresholds"]["suspicious"]
        else:
            reported += 1
            assert full == own
    assert reported > 100 and unreported > 100  # both branches were exercised


def test_worker_failure_is_an_error_not_a_verdict(monkeypatch):
    def timed_out(script, stdin=b"", limits=sandbox.Limits()):
        return sandbox.Result(False, b"", "timeout", None, 0.0, 0.0, 0.0, 0)

    monkeypatch.setattr(sandbox, "run", timed_out)
    result = lynceus.score(PHISH)
    assert result["error"] == "parser_timeout" and result["flagged"] is None
    assert result["score"] is None  # an error never gets a score
