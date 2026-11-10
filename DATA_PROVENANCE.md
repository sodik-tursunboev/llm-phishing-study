# Data provenance

**Status: pre-download.** Nothing has been downloaded. **[GATE]** The authors approve the terms and the download list below before acquisition (README section 5.1). Checksums are added by script after download, never by hand.

All pages below were opened on 2026-11-11 by Claude Code; the authors have not yet re-checked them.

## 1. Nazario phishing corpus (phishing class)

- **Source:** https://monkey.org/~jose/phishing/ (directory listing, `README.txt`, `LICENSE.txt`).
- **Terms:** `README.txt` states the files are licensed CC-BY-4.0; `LICENSE.txt` (dated 2026-02-20) holds the CC BY 4.0 legal text. Derivative works are allowed; **attribution is required** in the paper.
- **Owner's notes (`README.txt`, paraphrased):** collected from one personal inbox and hand-classified, so it is representative rather than exhaustive and may contain labelling errors; earlier mailboxes were anonymised (destination IPs and domains), later ones were not; it should not contain malware.
- **PII risk:** high for the later, non-anonymised files (recipient addresses, names). Everything is scrubbed before any derived file is written.
- **Pre-LLM cutoff:** ChatGPT was released on 30 Nov 2022 (https://openai.com/index/chatgpt/). We keep files collected up to 2022 and, inside `phishing-2022`, only messages dated before 2022-11-30. Messages with a missing or unparseable `Date` in that file are counted and excluded.

Proposed download (sizes from the directory listing):

| File | Listed date | Size |
|---|---|---|
| `phishing0.mbox` | 2005-06-13 | 3.0 MB |
| `phishing1.mbox` | 2005-11-15 | 4.0 MB |
| `20051114.mbox` | 2014-02-10 | 3.9 MB |
| `phishing2.mbox` | 2006-08-07 | 9.9 MB |
| `phishing3.mbox` | 2007-08-07 | 19 MB |
| `phishing-2015` ... `phishing-2022` (8 files) | 2018-05-15 to 2023-01-31 | 57.6 MB |
| **Total (13 files)** | | **about 97 MB** |

Excluded: `phishing-2023`, `-2024`, `-2025` (collected after the cutoff, may contain LLM-written phishing); `private-phishing4.mbox` (the name suggests it is not meant for public use and `README.txt` does not mention it).

## 2. SpamAssassin public corpus, ham only (legitimate class)

- **Source:** https://spamassassin.apache.org/old/publiccorpus/ (directory listing and `readme.html`, last revised 2006-01-31).
- **Terms:** no formal licence. The readme (paraphrased) offers the corpus as a service to spam-filter developers; says the messages were posted to public fora, sent knowing they might be made public, or came from public newsletters; says copyright in the message text stays with the original senders; and asks that the mails never be sent into a live mail system.
- **Consequence for us:** offline research use only, which matches README section 4; we never redistribute message text, only manifests, hashes and aggregates.
- **PII risk:** medium. Some addresses were obfuscated by the corpus owner; headers are otherwise as received.

Proposed download:

| File | Listed size | Messages (per readme) |
|---|---|---|
| `20030228_easy_ham.tar.bz2` | 1.5 MB | 2,500 |
| `20030228_easy_ham_2.tar.bz2` | 1.0 MB | 1,400 |
| `20030228_hard_ham.tar.bz2` | 1.0 MB | 250 |
| **Total** | **3.5 MB** | **4,150** |

Excluded: the `20021010_*` files (older versions; the readme says the newer sets generally include them), all `spam` files (spam is not phishing and not part of the RQ), and `obsolete/`.

## 3. Not needed now

- **Enron:** not downloaded. 4,150 ham messages should cover train, dev and at least 300 test messages; we add Enron only if counts after deduplication fall short.
- **Toth et al. (2025), arXiv:2511.21448** (fallback and optional external check): the abstract page (v5, 20 Mar 2026; v3 and v4 withdrawn) says the dataset is on GitHub. Its licence is not shown on the abstract page and the repository was not opened. Its emails are LLM-generated variants, so it could only serve as an external check, not as pre-LLM data. First item on the cut list.

## 4. Checksums

Filled in by the download script: file, URL, download date, size in bytes, SHA-256. A test re-hashes the files and must match.

## Open questions

1. **Era match.** SpamAssassin ham is from 2002-2003; Nazario phishing spans 2005-2022. A classifier could learn "era" instead of "phishing". Option: restrict phishing to the 2005-2007 files. Decide after per-year counts following deduplication.
2. Should we ask the corpus owner about `private-phishing4.mbox`? Default: no, keep it excluded.
3. Exact CC BY attribution wording for the paper.

## Not verified

- Message counts (only the readme's numbers and listing sizes so far).
- Whether Nazario files contain attachments. Out of scope (text only); the parser will drop them and count drops.
- That the `20030228` ham sets contain every `20021010` ham message (the readme says "generally").
- Licence of the Toth et al. dataset.
