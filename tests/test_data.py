"""M1 checks: raw files match their pinned hashes, no cluster spans two splits, every message is
accounted for, and the parsing and scrubbing helpers behave as documented."""
import collections
import csv
import email.message

import pytest

from src.data.download import RAW, read_config, sha256
from src.data.emails import Rejected, extract_urls, html_to_text, is_english, normalise, scrub
from src.data.prepare import REASONS, jaccard_components


def rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


@pytest.mark.skipif(not RAW.exists() or not any(RAW.iterdir()), reason="corpus not downloaded")
def test_raw_files_match_pinned_hashes():
    for row in read_config():
        assert sha256(RAW / row["file"]) == row["sha256"], row["file"]


def test_no_cluster_in_two_splits():
    splits_of = collections.defaultdict(set)
    for r in rows("results/m1_messages.csv"):
        if r["status"] == "ok":
            splits_of[r["cluster"]].add(r["split"])
    assert splits_of and all(len(s) == 1 for s in splits_of.values())


def test_every_message_accounted_for():
    messages = rows("results/m1_messages.csv")
    assert len({r["id"] for r in messages}) == len(messages)
    assert all(r["status"] in REASONS + ["ok"] for r in messages)
    assert all((r["status"] == "ok") == bool(r["split"]) for r in messages)  # kept <=> has a split
    for source in rows("results/m1_sources.csv"):
        assert int(source["read"]) == int(source["kept"]) + sum(int(source[x]) for x in REASONS)
        assert int(source["read"]) == sum(r["source"] == source["source"] for r in messages)


def test_scrub_removes_addresses_phones_and_names():
    out = scrub("Dear Jane Doe, mail jane.doe@example.com or call (555) 123-4567.", {"Jane Doe"})
    assert out == "Dear [NAME], mail user@example.com or call [PHONE]."


def test_scrub_leaves_url_ids_and_scrubbed_addresses_alone():
    text = "See http://example.com/track?id=5551234567 or write to user@example.com"
    assert scrub(text, {"user"}) == text


def test_normalise_scrubs_recipient_everywhere_and_sender_in_headers_only():
    raw = (b"From: PayPal <service@example.com>\nTo: Jane Doe <jane@example.com>\nSubject: Hello Jane Doe\n\n"
           b"Dear Jane Doe, PayPal asks you to verify at http://example.com/login\n")
    msg = normalise(raw)
    assert ("From", "[NAME] <user@example.com>") in msg["headers"]
    assert ("To", "[NAME] <user@example.com>") in msg["headers"]
    assert msg["subject"] == "Hello [NAME]"
    assert msg["text"] == "Dear [NAME], PayPal asks you to verify at http://example.com/login\n"
    assert msg["urls"] == ["http://example.com/login"]


def test_attachments_are_rejected():
    msg = email.message.EmailMessage()
    msg["Subject"] = "invoice"
    msg.set_content("See the attached invoice.")
    msg.add_attachment(b"%PDF-1.4", maintype="application", subtype="pdf", filename="invoice.pdf")
    with pytest.raises(Rejected, match="non_text_part"):
        normalise(msg.as_bytes())


def test_urls_come_from_text_and_html():
    urls = extract_urls("Go to http://example.com/a.", '<a href="https://example.org/x?a=1&amp;b=2">x</a>')
    assert urls == ["http://example.com/a", "https://example.org/x?a=1&b=2"]


def test_html_to_text_drops_scripts():
    assert html_to_text("<p>Hello <b>you</b></p><script>var x = 1;</script>") == "Hello you"


def test_language_filter():
    assert is_english("Please confirm your account details by clicking the link below before Friday.")
    assert not is_english("Bitte bestätigen Sie Ihre Kontodaten, indem Sie auf den folgenden Link klicken.")


def test_jaccard_components_join_similar_sets_only():
    sets = [{"a b", "b c", "c d"}, {"a b", "b c", "c d", "d e"}, {"x y"}]  # Jaccard(0, 1) = 3/4
    assert list(jaccard_components(sets, 0.5)) == [0, 0, 1]
