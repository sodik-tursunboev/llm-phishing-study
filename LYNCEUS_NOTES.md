# Lynceus (L4): what it is and how it fits the evaluation

Everything below comes from the Lynceus repository at the pinned commit (code, `README.md`, `CLAUDE.md`, git history), read on 2026-11-11. Where the code does not answer a question, it says UNKNOWN. Lynceus is one pluggable layer, **never the contribution** (README section 7).

## 1. Identity

| | |
|---|---|
| Repository | local, `C:\mirage` (folder name from its earlier name MIRAGE; renamed Lynceus on 2026-11-06 per its README) |
| Version evaluated | branch `main`, commit `d9c3ba88f9b995d9079434d39ad8d977dbb49b05` (2026-11-10 23:40 +01:00). The other branch, `rename-lynceus` (worktree `C:\lynceus-work`), has no commit that `main` lacks. |
| Engine versions | `lynceus d9c3ba88f9b9 email-1.2.0 rules 1.3.0+70796a1de43c`, as reported by the adapter; `rules/` SHA-256 `a08ecc81cd929a55aee936acc8800d8d190c3b28a3ec5ab7372ad3ffc5601fe1`. The adapter refuses to run on any other commit. |
| Licence | **UNKNOWN**: the repository has no LICENSE, COPYING or NOTICE file |
| History | 83 commits, 2026-11-04 to 2026-11-10, all authored by `sodik-t`; all 83 carry a `Co-Authored-By` trailer for Claude (67 Claude Sonnet 5.5, 16 Claude Opus 5.5). The repository contains `CLAUDE.md`, a Claude Code instruction file. |

## 2. What it does (its own README)

A local-first phishing detector for Windows with these parts:
- a URL engine (readable rules);
- message and file engines that parse in a sandboxed worker;
- optional threat-intelligence lists and providers;
- a Windows agent, a browser extension and a console;
- read-only Gmail and Outlook connectors.

Verdicts are `MALICIOUS | SUSPICIOUS | BENIGN | UNKNOWN | ERROR`, each with a risk score, the rules that fired and evidence. Its README reports that its URL rules catch 2.5% of real phishing URLs on its own E1 evaluation (`docs/eval/url-real.md` in that repository, not checked here).

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
- attachment parsers (pikepdf, Pillow, OpenCV): not installed, because every study message is text-only, so attachment inspection is never triggered.

**Static and offline?** Yes, on this path. Fixed rules and weights, no training, no network (the container has none), deterministic. `tests/test_lynceus.py` checks one message gives an identical result twice, and the test-split run below checks the same at scale.

## 4. The one adaptation

Lynceus starts its parser worker through `core.sandbox.run`, which uses a Windows AppContainer and refuses on Linux. `src/detectors/lynceus.py` replaces that one function: the **same worker code** runs as a subprocess with the same CPU, memory, wall-time and output caps, inside our offline container. Parsing, rules and scoring are unchanged.

Consequence: the Windows sandbox itself is not part of what we evaluate. It is a security boundary, not a detection component, so it does not change verdicts.

## 5. Adapter output (common interface)

`score(msg) -> {score, flagged, state, evidence, error, version, config_hash}`

- `score` is Lynceus's risk score, 0-100, or None when it gave none.
- `flagged` is True for MALICIOUS or SUSPICIOUS, the states where Lynceus warns the user. UNKNOWN ("not enough to call it") is not flagged. *Authors: confirm this mapping.*
- An ERROR, or a verdict without a score (the engine gives a reason, such as a parser timeout), becomes `error` with `flagged=None`. It is never counted as benign or flagged.
- `evidence` lists the rule ids that fired. `config_hash` is the SHA-256 of Lynceus's `rules/` folder.
- A second, dev-calibrated threshold on `score` (1% false positives on dev originals) will be fixed before the freeze, as for the other layers (README section 5.4).

## 6. How a rewrite can reach Lynceus (from its rule code)

A rewrite changes only the body. Lynceus's message rules that can see body wording or body structure:
- **Wording:** `email.social_engineering` (phrases from the urgency and credential-request lists, in the subject plus a body excerpt).
- **Link text and HTML structure:** `email.link_text_brand_mismatch`, `email.link_text_mismatch`, `email.hidden_link`, `email.image_only_link`, `email.password_form`, `email.script_content`, `email.meta_refresh`, `email.link_flood`, `email.malformed_mime`.

The URL rules see the links, and the gates keep links identical. The sender rules see headers, which are never rewritten. Most of Lynceus's signal therefore sits where a rewrite cannot reach. This is a prediction from the code, not a result.

## 7. Stability on the original test split (go/no-go criteria, README section 7.4)

`python -m src.detectors.run lynceus test`, run twice offline on 2026-11-11:
- 1,662 of 1,662 messages scored, 0 errors, 131 s and 136 s;
- the two output files are identical (SHA-256 `e485ec66a95d70a512bf455416f82466ab071d5eb3803fe46d232799a2c84bf7`);
- the adapter tests pass.

That meets all three go criteria. Detection rates were deliberately not looked at: thresholds are set on dev, never on test.

**Freeze:** tag `lynceus-eval-v1` once the authors confirm section 5's mapping and the dev threshold is fixed, before any rewritten data is scored.

**Version change pending (2026-11-11):** the first author is improving Lynceus. The rule is that no data from this study (corpora, dev, test, rewrites) may be used for that work. When the new commit is ready, the adapter is re-pinned, sections 1 and 7 are re-run, and only then is Lynceus calibrated on dev; its dev results are not reported before that. The change goes in `DEVIATIONS.md`.

## 8. Known limits

- Lynceus's README says it was built and checked on one Windows 11 machine, and that its CI has never run.
- Its rules were written by the same authors who run this study (conflict of interest, README section 7.5): results are reported whatever they are, with the same controls as every layer.
- The frozen version must never be tuned on rewritten data. A bug found after the freeze goes to `DEVIATIONS.md` and triggers a full re-run.

## 9. [GATE] Authorship split: authors to fill in

The coordinator asked what we built ourselves. Git history alone does not establish contributions (README section 7.1). It shows one human author and Claude co-authorship on every commit.

| Part | Written by us | AI-assisted (how) | Third-party |
|---|---|---|---|
| Rule design (which signs of phishing, weights) | UNKNOWN | UNKNOWN | UNKNOWN |
| Rule and engine code | UNKNOWN | UNKNOWN | UNKNOWN |
| Rule data (brand lists, phrase lists) | UNKNOWN | UNKNOWN | UNKNOWN (origin of `rules/*/lists.toml` not stated in the code read) |
| Parser libraries | | | ada-url, lxml, pydantic, and the Python `email` package |
| Kavish's part in Lynceus | UNKNOWN (no commits under another name) | | |

## Open questions

1. Confirm `flagged` = MALICIOUS or SUSPICIOUS (section 5).
2. Licence for Lynceus, and whether it may be released with the study or only described.
3. The authorship split (section 9).

## Not verified

- Lynceus's own evaluation figures (its README's 2.5%) were not re-run.
- The origin of its brand and phrase lists.
- Behaviour on attachments (out of scope here; the parsers are not installed).
