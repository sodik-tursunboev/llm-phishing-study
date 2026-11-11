"""L1 and L2 adapter checks: offline, deterministic, and their evidence explains their score."""
import pathlib

import pytest

from src.detectors import spamassassin
from src.detectors.calibrate import threshold_at_fpr

GTUBE = "XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-EMAIL*C.34X"


def message(text, subject="Meeting notes"):
    return {"headers": [("From", "Alice <alice@example.org>"), ("To", "bob@example.org"), ("Subject", subject)],
            "subject": subject, "text": text, "html": "", "urls": []}


def test_spamassassin_flags_gtube_and_its_score_is_the_sum_of_rule_points():
    result = spamassassin.score(message(GTUBE + "\n"))
    assert result["flagged"] is True and "GTUBE" in result["evidence"]
    assert result["score"] == pytest.approx(sum(result["evidence"].values()), abs=0.01)


def test_spamassassin_is_deterministic_and_leaves_plain_mail_unflagged():
    msg = message("Hi Bob, the notes from Tuesday are below. See you next week.\n")
    first, second = spamassassin.score(msg), spamassassin.score(msg)
    assert first == second and first["flagged"] is False and first["error"] is None


def test_threshold_keeps_at_most_one_percent_of_ham_above_it():
    ham = list(range(200))  # scores 0..199: exactly 2 of 200 (1%) lie above 197
    assert threshold_at_fpr(ham) == 197
    # Ties: 2 of 152 above 0 is 1.3% (too many); 1 of 152 above 5 is 0.7%, so the threshold is 5.
    assert threshold_at_fpr([0] * 150 + [5, 6]) == 5


@pytest.mark.skipif(not pathlib.Path("data/models/tfidf_lr.pkl").exists(), reason="L2 model not fitted")
def test_tfidf_lr_is_deterministic_and_reports_token_evidence():
    from src.detectors import tfidf_lr

    msg = message("Your account is suspended. Verify your password now to avoid closure.\n", "Urgent")
    first, second = tfidf_lr.score(msg), tfidf_lr.score(msg)
    assert first == second and first["error"] is None and first["evidence"]
    assert first["flagged"] == (first["score"] >= 0)
