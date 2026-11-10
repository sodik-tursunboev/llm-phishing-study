# AI use log

Every substantive AI use (README section 9). The paper's AI-use declaration is built from this file.

| Date | Tool | Purpose | How verified |
|---|---|---|---|
| 2026-11-11 | Claude Code (Claude Opus 5.5) | M0: wrote `Dockerfile`, `requirements.txt`, `.gitignore`, `hooks/`, `tests/`, `ENVIRONMENT.md`; looked up the base-image digest and package versions by running Docker | Check command passed in the no-network container (5 tests); network test fails when the network is enabled; hook blocked a test commit containing an email address and passed the first commit. Authors still to read and be able to explain every file. |
| 2026-11-11 | Claude Code (Claude Opus 5.5) | M1 licence gate: opened the Nazario, SpamAssassin, arXiv:2511.21448 and OpenAI pages and drafted `DATA_PROVENANCE.md` | Every statement cites the page it came from; authors to re-open the pages and approve at the [GATE]. |
