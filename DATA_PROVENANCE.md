# Data provenance

**Status: downloaded.** The authors approved the terms and the download list on 2026-11-11 (licence [GATE], README section 5.1). Sizes and SHA-256 hashes were written by `src/data/download.py` into `configs/raw_files.csv`; nothing was typed by hand.

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

`configs/raw_files.csv`: file, label, URL, size in bytes, SHA-256, retrieval date (UTC). `src/data/download.py` re-hashes every file on each run, and `tests/test_data.py` checks them too; a mismatch fails. Per-message SHA-256 hashes are in `results/m1_messages.csv`, so a reviewer can check they hold the same messages.

The files are stored in a Docker volume, not on the host disk, because the host antivirus quarantines real phishing HTML (ENVIRONMENT.md).

## 5. Processing (`src/data/prepare.py`, offline)

Steps run in this order. Each dropped message keeps its reason in `results/m1_messages.csv`; nothing is dropped silently.

1. **Parse** each message (Python `email` package). If parsing fails: `parse_error`.
2. **Text only.** Any part other than text/plain or text/html, such as an attachment, image or forwarded email: `non_text_part`.
3. **Scrub PII** in headers and bodies:
   - The local part of every email address becomes `user`; the domain stays.
   - Phone numbers written with separators become `[PHONE]`.
   - Recipients' display names and mailbox names become `[NAME]` everywhere.
   - Sender display names become `[NAME]` in headers only, because in phishing they are forged brand names that belong to the content under study.
   - Other personal names in bodies are not detected.
4. **Pre-LLM cutoff**, `phishing-2022` only: a missing or unparseable Date gives `date_unknown`; a Date on or after 2022-11-30 gives `after_cutoff`.
5. **Empty body:** `empty`.
6. **English only.** `langdetect` (seeded) on the body without URLs must return `en`, otherwise `not_english`. A function-word rule tried first dropped many short or link-heavy messages that `langdetect` labels English, so it was replaced before any split or detector existed.
7. **Near-duplicates.** Within each class, messages whose sets of 5-word phrases have Jaccard similarity of at least 0.8 (URLs and digits masked) form one group. The first message in corpus order is kept; the others become `near_duplicate`.
8. **Template clusters.** Kept messages with Jaccard of at least 0.5 are joined into one cluster, transitively.
9. **Splits by cluster.** Clusters are shuffled with seed 2026, then fill pilot (until 25 messages per class), test (25%), dev (15%) and train (the rest). No cluster spans two splits (`tests/test_data.py`).

Outputs: `data/messages.jsonl` holds the content (private, in the volume). `results/m1_sources.csv` holds counts per source and reason. `results/m1_splits.csv` holds counts, clusters, median words, HTML share and median URLs per class and split.

## Open questions

1. **Era match.** SpamAssassin ham is from 2002-2003; Nazario phishing spans 2005-2022. A classifier could learn "era" instead of "phishing". Option: keep only phishing from the 2005-2007 files. Kept counts per file are in `results/m1_sources.csv`, so the authors can decide whether the 2005-2007 subset still gives at least 300 test messages.
2. **HTML imbalance.** Most kept phishing is HTML and most ham is plain text (`results/m1_splits.csv`). This does not bias the paired original-vs-rewrite comparison, but it inflates baseline detection and belongs in the limitations.
3. Should we ask the corpus owner about `private-phishing4.mbox`? Default: no, keep it excluded.
4. Exact CC BY attribution wording for the paper.

## Not verified

- Thresholds (Jaccard 0.8 and 0.5) are conventional choices, not tuned; nobody has looked at example clusters. Authors could inspect a few clusters locally (never through a cloud model).
- The scrub was checked with unit tests only, not by reading scrubbed messages: corpus text must not be sent to Claude.
- `langdetect` accuracy on these corpora (language labels were seen only as counts). The comparison with the function-word rule was a one-off diagnostic script, not kept in the repo.
- That the `20030228` ham sets contain every `20021010` ham message (the readme says "generally").
- Licence of the Toth et al. dataset.
