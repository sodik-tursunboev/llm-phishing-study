# AI use log

Every substantive AI use (README section 9). The paper's AI-use declaration is built from this file.

| Date | Tool | Purpose | How verified |
|---|---|---|---|
| 2026-11-11 | Claude Code (Claude Opus 5.5) | M0: wrote `Dockerfile`, `requirements.txt`, `.gitignore`, `hooks/`, `tests/`, `ENVIRONMENT.md`; looked up the base-image digest and package versions by running Docker | Check command passed in the no-network container (5 tests); network test fails when the network is enabled; hook blocked a test commit containing an email address and passed the first commit. Authors still to read and be able to explain every file. |
| 2026-11-11 | Claude Code (Claude Opus 5.5) | M1 licence gate: opened the Nazario, SpamAssassin, arXiv:2511.21448 and OpenAI pages and drafted `DATA_PROVENANCE.md` | Every statement cites the page it came from; authors to re-open the pages and approve at the [GATE]. |
| 2026-11-11 | Claude Code (Claude Opus 5.5) | M1 data stage: wrote `src/data/` (download, parse, PII scrub, filters, deduplication, clustering, splits), `tests/test_data.py`; chose `langdetect` after a count-only comparison; moved corpora into a Docker volume after the host antivirus quarantined a file | Claude Code saw only counts and hashes, never message text (README section 4). Unit tests and split/accounting tests pass; the pipeline ran twice with identical output hashes. Authors to inspect a sample of scrubbed messages locally. |
