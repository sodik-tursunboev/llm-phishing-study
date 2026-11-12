"""Turn one raw email into the study's normalised message object, with personal data scrubbed.

The object keeps every header (decoded to text), the text/plain and text/html bodies, and the
URL list. A message with any other part (attachment, image, forwarded mail) is rejected,
because the study is text-only (README section 4).
"""
import email
import email.policy
import email.utils
import html
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html.parser import HTMLParser

from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException

URL_RE = re.compile(r"https?://[^\s\"'<>()]+", re.IGNORECASE)
EMAIL_RE = re.compile(r"[\w.+-]+@([\w-]+(?:\.[\w-]+)+)")
# Phone numbers need separators, so long IDs inside URLs are not mistaken for phones.
PHONE_RE = re.compile(
    r"(?<![\w/=.-])(?:\+\d{1,3}[ .-]\d{2,4}[ .-]\d{3,4}[ .-]?\d{3,4}|\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4})(?![\w/])"
)
ADDRESS_HEADERS = {"from", "to", "cc", "reply-to", "sender", "delivered-to", "x-original-to"}  # lower case
RECIPIENT_HEADERS = {"to", "cc", "delivered-to", "x-original-to"}
# In an address header the placeholder must be quoted: an unquoted "[NAME]" is invalid address
# syntax, and parsers (Lynceus's included) then drop the whole address.
UNQUOTED_NAME = re.compile(r'(?<!")\[NAME\](?!")')

DetectorFactory.seed = 0  # langdetect is randomised; a fixed seed makes it deterministic


class Rejected(Exception):
    """The message is outside the study's scope; the reason is recorded, never silently dropped."""


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self._skip = [], 0

    def handle_starttag(self, tag, attrs):
        self._skip += tag in ("script", "style")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def html_to_text(markup):
    """Visible text of an HTML body (script and style content dropped)."""
    parser = _TextExtractor()
    parser.feed(markup)
    return " ".join(" ".join(parser.parts).split())


BLOCK_TAGS = {"p", "br", "div", "tr", "li", "ul", "ol", "table", "h1", "h2", "h3", "h4", "h5", "h6"}


class _PlainExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self._skip, self._links = [], 0, []  # _links: (href, index where its text starts)

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")
        if tag == "a":
            self._links.append((dict(attrs).get("href") or "", len(self.parts)))

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
        elif tag == "a" and self._links:
            href, start = self._links.pop()
            if URL_RE.fullmatch(href) and href not in "".join(self.parts[start:]):
                self.parts.append(f" <{href}>")  # keep the address a reader would click
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def html_to_plain(markup):
    """Plain-text version of an HTML body for rewriting: paragraph breaks kept, and each link's
    address written after its text as <URL>, so no link is lost when the HTML is dropped."""
    parser = _PlainExtractor()
    parser.feed(markup)
    lines = (" ".join(line.split()) for line in "".join(parser.parts).splitlines())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def plain_body(msg):
    """The body every derived condition starts from: the plain part, or the HTML as plain text."""
    return msg["text"] if msg["text"].strip() else html_to_plain(msg["html"])


def extract_urls(text, markup):
    """All http(s) URLs in the plain body and the HTML body (a multiset, in order)."""
    found = URL_RE.findall(text) + [html.unescape(u) for u in URL_RE.findall(markup)]
    return [u.rstrip(".,;:!?") for u in found]


def body_text(msg):
    """The words a reader sees: the plain body, or the HTML body's text if there is no plain body."""
    return msg["text"] if msg["text"].strip() else html_to_text(msg["html"])


def is_english(text):
    """True if langdetect (character n-gram language identifier) labels the text, minus URLs, English.

    A function-word rule tried first rejected short or link-heavy English mail (DATA_PROVENANCE.md).
    """
    try:
        return detect(URL_RE.sub(" ", text)) == "en"
    except LangDetectException:  # no letters to judge
        return False


def scrub(text, names):
    """Replace email local parts, phone numbers and the given names (whole words, any case)."""
    text = EMAIL_RE.sub(r"user@\1", text)
    text = PHONE_RE.sub("[PHONE]", text)
    for name in sorted(names, key=len, reverse=True):  # longest first: "Jane Doe" before "Jane"
        # Never touch a word joined to "@": addresses were already handled above.
        text = re.sub(rf"(?<![\w@]){re.escape(name)}(?![\w@])", "[NAME]", text, flags=re.IGNORECASE)
    return text


def _decode(part):
    payload = part.get_payload(decode=True) or b""
    try:
        return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
    except LookupError:  # unknown charset name
        return payload.decode("latin-1")


def normalise(raw):
    """Parse raw RFC 822 bytes into {headers, subject, text, html, urls}, scrubbed. Raises Rejected."""
    try:
        msg = email.message_from_bytes(raw, policy=email.policy.default)
        headers = [(k, str(v)) for k, v in msg.items()]
    except Exception as exc:  # malformed beyond what the email package tolerates
        raise Rejected("parse_error") from exc

    text, markup = [], []
    for part in msg.walk():
        if part.get_content_maintype() == "message":
            raise Rejected("non_text_part")  # a forwarded or attached email
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        if ctype not in ("text/plain", "text/html") or part.get_content_disposition() == "attachment":
            raise Rejected("non_text_part")
        (text if ctype == "text/plain" else markup).append(_decode(part))

    # Recipients are real people; their display names and mailbox names are removed everywhere.
    # Sender display names are removed from headers only: in phishing they are forged brand
    # names that belong to the content we study.
    pairs = email.utils.getaddresses([v for k, v in headers if k.lower() in ADDRESS_HEADERS])
    recipients = email.utils.getaddresses([v for k, v in headers if k.lower() in RECIPIENT_HEADERS])
    body_names = {n for n, _ in recipients if len(n) >= 3} | {
        a.split("@")[0] for _, a in recipients if len(a.split("@")[0]) >= 3
    }
    header_names = body_names | {n for n, _ in pairs if len(n) >= 3}

    headers = [(k, scrub(v, header_names)) for k, v in headers]
    headers = [(k, UNQUOTED_NAME.sub('"[NAME]"', v) if k.lower() in ADDRESS_HEADERS else v) for k, v in headers]
    result = {
        "headers": headers,
        "subject": next((v for k, v in headers if k.lower() == "subject"), ""),
        "text": scrub("\n".join(text), body_names),
        "html": scrub("\n".join(markup), body_names),
    }
    result["urls"] = extract_urls(result["text"], result["html"])
    return result


MIME_HEADERS = {"content-type", "content-transfer-encoding", "mime-version"}


def render(msg):
    """RFC 822 bytes for a normalised message: its own headers, then a freshly encoded body.

    Every detector scores these bytes, and every condition (original or rewritten) goes through
    this same function, so encoding differences cannot differ between conditions.
    """
    parts = [MIMEText(body, subtype, "utf-8") for body, subtype in ((msg["text"], "plain"), (msg["html"], "html")) if body]
    if len(parts) == 1:
        out = parts[0]
    else:  # both bodies, or (never after filtering) neither
        out = MIMEMultipart("alternative")
        for part in parts:
            out.attach(part)
    mime = list(out.items())
    for name in {k for k, _ in mime}:
        del out[name]
    for name, value in msg["headers"]:  # original order first, minus the old MIME headers
        if name.lower() not in MIME_HEADERS:
            out[name] = value
    for name, value in mime:
        out[name] = value
    return out.as_bytes(policy=email.policy.default)
