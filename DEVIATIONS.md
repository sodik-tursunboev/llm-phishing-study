# Deviations from the brief (README v1, 2026-11-11)

Every change to the plan in `README.md`: what changed, why, when, and what it costs the claims. The protocol is not frozen yet (M4); after the freeze, any change that affects scoring triggers a full re-run of all conditions.

## Scope update v3 (authors, 2026-11-11)

The research question is unchanged. Reason for every row below: the authors' scope decision v3. **Authors: add a one-sentence reason per row before M4**, because the defence will ask.

| # | Area (README section) | Was | Now | Cost to the claims |
|---|---|---|---|---|
| 1 | Layers (5.4) | L1 SpamAssassin, L2 TF-IDF+LR, L3 URL layer, L4 Lynceus (go/no-go 14 Nov) | L1, L2 and L4 Lynceus. **Lynceus is required (authors, 2026-11-11, overriding v3's "only if within 45 min").** Its adapter is built first in M2, before any rewriting. It is frozen (tag `lynceus-eval-v1`) before rewritten data is scored and never tuned on rewritten data. If it is still blocked after about 1 hour, work stops and the blocker goes to the authors; it is never dropped silently. | H5 (URL layer unaffected) is dropped; links are still checked by the URL-multiset gate. |
| 2 | Conditions (5.2) | orig, null-A, null-B, lex, llm-G1..G3 | orig, null-A, lex, llm-G1; G2 only if G1 finishes fast | Without null-B, LLM copy artefacts are not separated from paraphrase effects. With one generator, H4 is dropped and single-generator quirks (6.2) cannot be ruled out. Both go in the limitations. |
| 3 | Test size (5.1) | at least 300 per class, never below 200 | at least 200 per class | Wider confidence intervals. |
| 4 | Comparability (5.3) | gates, embedding plus NLI, human audit of 60-100 stratified pairs | gates, embedding similarity, and the same 30 pairs blind-rated by both authors (Cohen's kappa) | A kappa from 30 pairs is imprecise; report it with a confidence interval or say so. NLI is dropped. |
| 5 | Statistics (6.1) | McNemar exact, cluster-bootstrap CI, Wilcoxon, AUC, Holm, equivalence test for null conditions | McNemar exact and the paired cluster-bootstrap CI | See open questions 2 and 3. |
| 6 | Cause (6.2) | accounting, 2-3 interventions (sufficiency and necessity), dose-response, unique-catch | rule/token accounting plus one intervention on the main suspect | Causal wording only for that one property; everything else is "consistent with". H6 and unique-catch are dropped. |
| 7 | Paper (11) | research letter of at most 3,000 words | about 2,000 words including the abstract (advice) | None. |
| 8 | Roles (13) | not set | Sodiq runs the research. Kavish blind-rates the same 30 pairs and, after the draft, verifies every reference and checks each number against the result files. Claude Code prepares the rating sheet and `references/evidence_trail.csv` and never rates or verifies. | None. |

## Authors' decisions recorded before the freeze

| # | Date | Decision | Reason given | What the paper must say |
|---|---|---|---|---|
| 10 | 2026-11-11 | Generator G1 is `gemma3:4b` (Ollama, manifest SHA-256 `68ceab7e468a31c988b44d5a4984a0e21f58c4f7158c6ce29c1804babac38df7`), not the MIT-licensed `phi4-mini` that Claude Code proposed | Authors: stronger model; offline research use only | Gemma's Prohibited Use Policy (last modified 21 Feb 2024, https://ai.google.dev/gemma/prohibited_use_policy) bars "Generating content for deceptive or fraudulent activities, scams, phishing, or malware", with no research exception. Declare this and state the safeguards: existing emails only, offline, nothing sent, rewrites never published. |
| 11 | 2026-11-11 | The rewrite stage runs in a container **with** network access, calling the authors' local Ollama 0.34.4 on the host (`host.docker.internal:11434`), instead of a model server on an isolated Docker network | Authors: avoid another 3.5 GB download | The code sends text only to the local Ollama URL and checks the model digest first. Scoring and analysis still run with `--network none`. State that the generation step was local but not network-isolated. |
| 12 | 2026-11-11 | **Plain-text conditions.** A 4B model cannot rewrite HTML reliably, so it rewrites the visible text, links kept as `<URL>`. Every derived condition (null-A, lex, llm) carries a plain-text body with the original headers. The **primary contrast is llm vs null-A**, where only the wording differs. orig vs null-A is reported as the effect of the plain-text format. | Proposed by Claude Code; authors said start | H2 now reads: null-A measures the format change. It is reported, not required to be zero. Every main result compares with null-A. |
| 14 | 2026-11-12 | **Gates fixed on the pilot (plan A).** Links, numbers and entities are compared as sets after normalising format (`2,500` = `2500`, a trailing `/`), not as counts. A leading "Here is ...:" line is removed from model output. Rewriting continues until 200 per class pass, about 940 rewrites. Embedding similarity is dropped. | The pilot passed only 19 of 53 under count-based gates (no refusals; the model drops numbers and links). Gates are calibrated on the pilot before the freeze (README 5.3). The gates plus the 30-pair rating cover comparability. | Report the pass rate per class and the kept-vs-discarded comparison. The analysed set is a selection of rewrites that kept every link and number. |
| 15 | 2026-11-12 | **Statistics family and lex baseline fixed.** Holm correction covers the confirmatory family only (phishing, calibrated threshold, llm vs null-A, gate-passed: one test per layer). Everything else is descriptive. The lex baseline uses WordNet 3.0 (`wordnet.zip` SHA-256 `cbda5ea6eef7f36a97a43d4a75f85e07fccbb4f23657d27b4ccbc93e2646ab59`) at the pilot dose 0.364. | Scope v3 named McNemar and the bootstrap but no family; a small pre-declared family keeps the confirmatory claim clear | State the family and the dose in Methods. |

## Implementation deviations

| # | Date | What | Why | Cost to the claims |
|---|---|---|---|---|
| 9 | 2026-11-11 | Corpora are stored in a Docker volume, not in `data/` on the host disk (README section 12) | The host antivirus quarantined `phishing3.mbox`; a volume keeps phishing off the host without changing any security setting | None; hashes are verified in the volume (ENVIRONMENT.md). |
| 13 | 2026-11-11 | **Bug fix in the PII scrub (pre-freeze).** (a) The placeholder `[NAME]` in address headers is now quoted, because unquoted it is invalid address syntax and Lynceus dropped the whole sender: a made-up test scored 82 without the sender rule, 95 with it. (b) Address headers are matched case-insensitively, so `CC:` and `Reply-to:` are scrubbed too. | Found while testing null-A at M3 | Everything downstream was re-run: data stage, L2 fit, dev scoring and L1/L2 calibration. The Lynceus test-split stability figures in `LYNCEUS_NOTES.md` predate the fix and are re-run at the re-pin. No rewritten data had been scored. |

## Open questions for the authors

1. v3 does not mention covariate balance, the length-matched subset or the three-way sensitivity analysis (README 5.3, items 4 and 5). Are they dropped? Until you answer: UNKNOWN.
2. Null-A check without a formal equivalence test. Proposal: null-A passes if its paired cluster-bootstrap CI lies inside +-2 pp. This uses the same method, adds no new test, and needs the margin fixed at the freeze.
3. Floor effect without AUC or score shift. If SpamAssassin rarely flags the originals, McNemar has little to test. Proposal: also report the bootstrap CI of the paired score difference, which again uses the same method.
