"""M0 environment checks. They must run inside the study container (see ENVIRONMENT.md)."""
import os
import subprocess

# GTUBE: SpamAssassin's built-in test string; any working install flags it.
GTUBE = (
    "Subject: test\n\n"
    "XJS*C4JDBQADN1.NSBN3*2IDNEN*GTUBE-STANDARD-ANTI-UBE-TEST-EMAIL*C.34X\n"
)


def test_container_has_no_network():
    # With `docker run --network none`, Docker creates only the loopback interface,
    # so no packet can leave the container. Outside the container this test fails.
    assert sorted(os.listdir("/sys/class/net")) == ["lo"]


def test_spamassassin_scores_offline():
    # -L runs local tests only (no DNS or network rules); -t adds the rule report.
    out = subprocess.run(
        ["spamassassin", "-L", "-t"], input=GTUBE,
        capture_output=True, text=True, check=True, timeout=120,
    ).stdout
    assert "GTUBE" in out
