# Lynceus (L4): what it is and how it fits the evaluation

Everything below comes from the Lynceus repository at the pinned commit (code, `README.md`, project notes, git history), read on 2026-11-11. Where the code does not answer a question, it says UNKNOWN. Lynceus is one pluggable layer, **never the contribution** (README section 7).

## 1. Identity

| | |
|---|---|
| Repository | local, `C:\mirage` (folder name from its earlier name MIRAGE; renamed Lynceus on 2026-11-06 per its README) |
| Version evaluated | branch `main`, commit **`ac2a5af9b4f209a76c881a5337c5291b25b54c63`** ("D1: page detonation ...", re-pinned 2026-11-12; DEVIATIONS.md #17). It was first pinned at `d9c3ba88f9b995d9079434d39ad8d977dbb49b05`. The other branch, `rename-lynceus` (worktree `C:\lynceus-work`), has no commit that `main` lacks. |
| Engine versions | `lynceus ac2a5af9b4f2 email-1.2.0 rules 1.3.0+70796a1de43c`, as reported by the adapter; `rules/` SHA-256 `176402d19e7d02d741770bd858c74a4071b5ff2bc3539fd7f515242b21af485e`. The adapter refuses to run on any other commit. |
| Licence | **UNKNOWN**: the repository has no LICENSE, COPYING or NOTICE file |
| History | 84 commits at `ac2a5af`, 2026-11-04 to 2026-11-12 (83 at the first pin), all authored by `sodik-t`; each with an AI co-author trailer. |

## 2. What Lynceus is

Sources: Lynceus's own `FEATURES.md`, `DETECTION_ENGINE.md` and `KNOWN_LIMITATIONS.md` (version of 2026-11-11, provided by the author on 2026-11-14), and its README. Lynceus is still being improved; this study evaluates commit `ac2a5af` only.

Lynceus is a local-first phishing-defence system for Windows. It is more than a static detector:
- **URL engine:** 20 readable rules (lookalike and typosquat domains, encoded targets, credential bait and more) over a browser-grade URL parser.
- **Message and file engines:** MIME, header, HTML and link analysis, sender and authentication checks, and attachment inspection (scripts, shortcuts, programs, PDFs, archives, images with QR codes, Office documents), each parsed in a sandboxed worker.
- **Macro analysis:** a bounded evaluator runs a macro's own string-building code, and call-graph analysis follows auto-run code to dangerous calls.
- **Page detonation (D1):** on request, opens a page in a throwaway, locked-down browser container and judges what it shows, with 10 page rules.
- **Threat intelligence:** OpenPhish and PhishTank lists matched locally; optional VirusTotal, urlscan, URLhaus, MalwareBazaar and domain age.
- **Local AI reviewer:** `llama3.2:3b` through Ollama gives advice on macros. It is off by default, and can add at most one weak signal, never decide.
- **Scoring:** a published risk model (noisy-OR per category, capped, then across categories, 0 to 100). MALICIOUS needs a high score and strong evidence of two independent kinds.
- **Around the engine:** a Windows agent, a browser extension with warning pages, a console, reversible quarantine, and read-only Gmail and Outlook connectors (tested against fakes only).

Verdicts are `MALICIOUS | SUSPICIOUS | BENIGN | UNKNOWN | ERROR`, each with a risk score, the rules that fired and evidence. Lynceus's own measurements (not re-run here): its URL rules alone catch 2.5% of real phishing URLs (E1), and URL rules plus the opened page catch 37.3% of live phishing pages (D1 test half). Learned scoring is planned, not built.

## 3. What we use, and what we do not

**Used:** only the message engine (`core/email/engine.py`, `analyze_message`): raw RFC 822 bytes in, verdict out. That path covers:
- its sandbox worker's MIME and HTML parsing (`core/sandbox/guest/`);
- every link through the URL engine (`core/detection`, `rules/url`);
- the message rule pack (`rules/email`);
- scoring (`core/risk`, `rules/email/scoring.toml`).

Only `core/` and `rules/` are copied, by `git archive`, into the Docker volume `lynceus-src`. That leaves out `.env`, test samples and the Windows parts.

**Not used:**
- the agent, extension, console and mail connectors;
- threat intelligence: needs the network, and stays off because no `LYNCEUS_INTEL_PROVIDERS` is set;
- known-bad hash lists: none are configured, so `intel.hash_known_bad` cannot fire;
- the local-model reviewer: `analyze_message` does not call it;
- attachment parsers (pikepdf, Pillow, OpenCV) and macro analysis: not installed, because every study message is text-only, so attachment inspection is never triggered;
- page detonation (D1): it needs Docker and the network, opens live pages, and is never called on the message path.

**Static and offline?** Lynceus as a whole is not purely static (page detonation, intelligence feeds, the local reviewer). The path this study uses is. Fixed rules and weights, no training, no network (the container has none), deterministic. `tests/test_lynceus.py` checks one message gives an identical result twice, and the test-split run below checks the same at scale.

## 4. The one adaptation

Lynceus starts its parser worker through `core.sandbox.run`, which uses a Windows AppContainer and refuses on Linux. `src/detectors/lynceus.py` replaces that one function: the **same worker code** runs as a subprocess with the same CPU, memory, wall-time and output caps, inside our offline container. Parsing, rules and scoring are unchanged.

Consequence: the Windows sandbox itself is not part of what we evaluate. It is a security boundary, not a detection component, so it does not change verdicts.

## 5. Adapter output (common interface)

`score(msg) -> {score, flagged, state, evidence, error, version, config_hash}`

- `score` is Lynceus's risk, 0-100, for every message that did not error. Lynceus computes it from the rules that fired but reports it only for SUSPICIOUS and MALICIOUS (45 and above); an UNKNOWN verdict carries None. The adapter therefore re-runs Lynceus's own scoring function on the same signals with its SUSPICIOUS line set to 0, which returns the risk Lynceus discarded (0 when no rule fired). No rule, weight or cap changes. `reported_score` keeps what Lynceus itself reported. A test over 3,000 random sets of Lynceus's rules checks that the two agree whenever Lynceus reports a score and that the full-range score stays below 45 when it does not (DEVIATIONS.md #16).
- `flagged` is True for MALICIOUS or SUSPICIOUS, the states where Lynceus warns the user. UNKNOWN ("not enough to call it") is not flagged.
- An ERROR, or a verdict without a score (the engine gives a reason, such as a parser timeout), becomes `error` with `flagged=None`. It is never counted as benign or flagged.
- `evidence` lists the rule ids that fired. `config_hash` is the SHA-256 of Lynceus's `rules/` folder.
- A second, dev-calibrated threshold on `score` (at most 1% false positives on dev originals) was fixed before the freeze, as for the other layers: flag when score > 87 (section 7).

## 6. How a rewrite can reach Lynceus (from its rule code)

A rewrite changes only the body. Lynceus's message rules that can see body wording or body structure:
- **Wording:** `email.social_engineering` (phrases from the urgency and credential-request lists, in the subject plus a body excerpt).
- **Link text and HTML structure:** `email.link_text_brand_mismatch`, `email.link_text_mismatch`, `email.hidden_link`, `email.image_only_link`, `email.password_form`, `email.script_content`, `email.meta_refresh`, `email.link_flood`, `email.malformed_mime`.

The URL rules see the links, and the gates keep links identical. The sender rules see headers, which are never rewritten. Most of Lynceus's signal therefore sits where a rewrite cannot reach. This is a prediction from the code, not a result.

## 7. Stability on the original test split (go/no-go criteria, README section 7.4)

`python -m src.detectors.run lynceus test`, run twice offline on 2026-11-12, at `ac2a5af` and after the PII-scrub fix (DEVIATIONS.md #13):
- 1,662 of 1,662 messages scored, 0 errors, 225 s and 216 s;
- the two output files are identical (SHA-256 `9d9ae765f6741de1a536474af71b6a2e02e6e067d5b7a49fa1fa892c16c2012c`);
- all 41 study tests pass.

That meets all three go criteria. Test detection rates were not looked at: thresholds are set on dev, never on test.

**Re-pin check (2026-11-12):** dev was scored at `d9c3ba8` and at `ac2a5af` with the same adapter. All 997 dev messages give the same score, flag, state, rules fired and error at both commits. On the message path, only two files changed between the commits:
- `core/detection/engine.py`: parameters added with defaults;
- the worker: a new `reencode_jpeg` operation for detonator screenshots, never called for email.

The new detonation code is not on the path this study uses.

**Dev calibration (2026-11-12, `configs/thresholds.json`):** flag when score > 87. That flags 0.7% of dev legitimate mail and catches 12.0% of dev phishing. The native point (MALICIOUS or SUSPICIOUS) flags 6.0% and catches 61.0%.

**Freeze:** tag `lynceus-eval-v1` on the study commit that pins `ac2a5af`, before any rewritten data is scored.

## 8. Known limits

- Lynceus's README says it was built and checked on one Windows 11 machine, and that its CI has never run.
- Its rules were written by the same authors who run this study (conflict of interest, README section 7.5): results are reported whatever they are, with the same controls as every layer.
- The frozen version must never be tuned on rewritten data. A bug found after the freeze goes to `DEVIATIONS.md` and triggers a full re-run.

## 9. Authorship

**Authors' statement:** Lynceus is Sodik Tursunboev's tool. Sodik, a SOC and cybersecurity analyst, designed its full architecture and built it with an AI assistant before this study. Kavish Chaudhari is Sodik's partner in this study and did not write Lynceus.

Dates from the two git histories:
- Lynceus's first commit is 2026-11-04.
- The version first pinned, `d9c3ba8`, is from 2026-11-10 23:40.
- This study's first commit is 2026-11-11 00:23.
- The evaluated version, `ac2a5af` (2026-11-12 14:00), adds Sodik's later improvements, made without study data. They change no verdict on this study's data (DEVIATIONS.md #17).

The coordinator asked what we built ourselves. Git history alone does not establish contributions (README section 7.1); it shows one human author, Sodik, with an AI co-author on every commit. The table records who did what. It was compiled on 2026-11-12 from the Lynceus git history at `ac2a5af` and its provenance files, and updated on 2026-11-14 with the author's statement on the architecture.

| Part | Sodik | AI assistant | Third-party |
|---|---|---|---|
| Architecture, direction and decisions | Designed the full architecture (the parts in section 2); set the goals and the milestone order; chose what to build; approved each plan, every architecture decision record (24 at `d9c3ba8`, 25 at `ac2a5af`) and every new dependency; chose the evaluation datasets; ran the installs and live checks on Sodik's own machine | Drafted plans and decision records from Sodik's design, for Sodik's approval | None |
| Rule design (which signs of phishing, weights) | Chose what Lynceus detects; approved the rules and weights milestone by milestone | Drafted the signs of phishing and set each weight, cap and threshold by hand, from general knowledge of phishing techniques, then checked them on its own synthetic corpus and, for URLs, on real data (E1). Weights were never fitted: a fit on E1 data was tried and not adopted. The message rules used here are unchanged since 2026-11-10 | MITRE ATT&CK technique ids, as labels only |
| Rule and engine code | Built it with the assistant: directed every step, and ran and checked the result | Wrote the code from Sodik's instructions: all 84 commits (2026-11-04 to 2026-11-12) are authored as `sodik-t` and every one carries an AI co-author trailer | The libraries in the next rows |
| Rule data (brand lists, phrase lists) | Approved with each milestone | Drafted from general knowledge and not verified against any source, as their own file headers say: `rules/url/brands.toml` and `rules/url/lists.toml` (2026-11-04), `rules/email/lists.toml` (urgency and credential phrases, English and Polish, 2026-11-05) | `rules/url/data/confusables.txt`: Unicode UTS #39 confusables 18.0.0, unmodified, Unicode License (`rules/url/data/PROVENANCE.md`). `core/urls/data/public_suffix_list.dat`: Public Suffix List snapshot of 2026-11-04, MPL 2.0 (`core/urls/data/PROVENANCE.md`) |
| Parser libraries | | | On this study's path (text-only messages): ada-url (URL parsing) and pydantic (data models) in the engine, and the Python standard library (`email`, `html.parser`) in the parser worker, which imports nothing else. lxml, pikepdf, Pillow and OpenCV are used only for attachments and are not installed here |
| Kavish's part in Lynceus | None: Kavish did not write Lynceus (authors' statement, 2026-11-12); no commits under another name | | |

## Open questions

1. Licence for Lynceus, and whether it may be released with the study or only described.

Answered: `flagged` = MALICIOUS or SUSPICIOUS (approved with PROTOCOL.md); the authorship split (section 9).

## Not verified

- Lynceus's own evaluation figures (its README's 2.5%) were not re-run.
- The origin of its brand and phrase lists.
- Behaviour on attachments (out of scope here; the parsers are not installed).
