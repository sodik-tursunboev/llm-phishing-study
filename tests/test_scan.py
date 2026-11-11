"""The pre-commit scan must block secrets, PII and data files, and pass clean text.

Fake secrets are built by concatenation so this file does not trip the scan itself.
"""
from hooks.scan import find_problems


def test_blocks_data_and_raw_mail_paths():
    assert find_problems("data/raw/nazario.mbox", "")
    assert find_problems("notes/sample.eml", "")


def test_blocks_secrets_and_pii():
    for text in [
        "-----BEGIN RSA " + "PRIVATE KEY-----",
        "token = " + "ghp_" + "a" * 36,
        "contact " + "jane.doe" + "@" + "corp.org",
        "call " + "+48 22 " + "123 4567",
    ]:
        assert find_problems("notes.md", text), text


def test_code_under_src_data_is_allowed():
    assert find_problems("src/data/prepare.py", "import csv") == []


def test_passes_clean_text_and_reserved_example_domain():
    assert find_problems("notes.md", "Score with SpamAssassin, DOI 10.1109/CARS67163.2025.11337548") == []
    assert find_problems("tests/fixture.py", "sender = 'alice" + "@" + "example.com'") == []
