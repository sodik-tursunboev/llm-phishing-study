"""M3 checks: the plain-text version keeps every link, null-A changes nothing but the format,
and each comparability gate catches what it is meant to catch."""
from src.data.emails import html_to_plain, normalise, render
from src.rewrite.conditions import change_fraction, null_a, with_body
from src.rewrite.gates import check, clean

HTML = ('<html><body><p>Dear customer,</p><p>Please <a href="http://example.com/login">sign in</a> '
        'or visit <a href="http://example.org/help">http://example.org/help</a>.</p>'
        '<script>var x = 1;</script></body></html>')


def test_html_to_plain_keeps_paragraphs_and_every_link_once():
    assert html_to_plain(HTML) == ("Dear customer,\n\nPlease sign in <http://example.com/login> "
                                   "or visit http://example.org/help.")


def test_null_a_keeps_headers_and_survives_render():
    sender = ("From", '"[NAME]" <user@example.com>')  # stored messages are already scrubbed
    msg = {"headers": [sender, ("Subject", "Notice")], "subject": "Notice", "text": "", "html": HTML, "urls": []}
    plain = null_a(msg)
    again = normalise(render(plain))
    assert again["text"].strip() == plain["text"] and again["html"] == ""
    assert sender in again["headers"]
    assert sorted(plain["urls"]) == ["http://example.com/login", "http://example.org/help"]


BASE = "Your invoice 4521 for 30 EUR is due on 12/05. Pay at http://example.com/pay or call [PHONE]."


def test_gates_pass_a_faithful_rewrite():
    rewrite = "Invoice 4521 of 30 EUR must be paid by 12/05. Use http://example.com/pay or ring [PHONE]."
    assert check(BASE, rewrite) == []


def test_gates_catch_each_failure():
    assert "urls" in check(BASE, BASE.replace("example.com/pay", "example.com/payment"))
    assert "numbers" in check(BASE, BASE.replace("4521", "4512"))
    assert "entities" in check(BASE, BASE.replace("[PHONE]", "us"))
    assert "length" in check(BASE, BASE + (" filler" * 40))
    assert "refusal" in check(BASE, "I cannot help with rewriting this email.")
    assert "meta_text" in check(BASE, "Here is the rewritten email: " + BASE)


def test_formatting_only_differences_pass_and_meta_line_is_removed():
    base = "Transfer 2,500 EUR via http://example.com/pay/ today."
    assert check(base, "Today, send 2500 EUR through http://example.com/pay.") == []
    assert clean("Here's a rewritten version of the email:\n\nHello there.") == "Hello there."
    assert clean("Hello there.\nHere is more.") == "Hello there.\nHere is more."  # only leading lines go


def test_refusal_wording_already_in_the_original_is_not_a_refusal():
    base = "Sorry, I can't make it on Friday. Can we meet on Monday instead at 10?"
    assert "refusal" not in check(base, "Apologies, I can't attend on Friday. Could we meet Monday at 10?")


def test_lex_is_deterministic_hits_its_dose_and_never_touches_links_or_placeholders():
    from src.rewrite.lex import lex

    text = ("Dear [NAME], your account has been suspended because unusual activity was detected. "
            "Please confirm your details at http://example.com/account/verify within seven days "
            "or the account will be closed permanently. Regards, Customer Service")
    once, twice = lex(text, "msg-1", 0.3), lex(text, "msg-1", 0.3)
    assert once == twice and once != text
    assert "http://example.com/account/verify" in once and "[NAME]" in once
    assert abs(change_fraction(text, once) - 0.3) <= 0.06
    assert lex(text, "msg-1", 0.0) == text


def test_change_fraction():
    assert change_fraction("a b c d", "a b c d") == 0
    assert change_fraction("a b c d", "a x c y") == 0.5
    assert with_body({"headers": [], "subject": "", "text": "", "html": "<p>x</p>", "urls": []}, "hi")["html"] == ""
