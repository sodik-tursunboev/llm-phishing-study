# Protocol (frozen at tag `protocol-freeze-v1`)

**Status: DRAFT, awaiting the authors' approval ([GATE], README M4).** Nothing below may change after the tag without an entry in `DEVIATIONS.md`, and any change that affects scoring triggers a full re-run of all conditions. All code is frozen by the tag's commit. This file lists the parameters a reader needs.

## Research question

When the same emails are rewritten once by a local open-weight model (neutral prompt, no detector feedback), how much does detection by static layers change, and which layer accounts for it? The answer is reported as a paired comparison with controls; see section 6 for which claims are allowed.

## 1. Data (M1, `DATA_PROVENANCE.md`)

| Item | Value |
|---|---|
| Corpora | Nazario phishing (13 files, 2005–2022, before 2022-11-30) and SpamAssassin ham (3 files); SHA-256 in `configs/raw_files.csv` |
| Splits | by template cluster (Jaccard ≥ 0.5 on 5-word shingles), seed 2026; pilot 25 per class, test 25%, dev 15%, train the rest |
| Near-duplicates | Jaccard ≥ 0.8, first in corpus order kept |
| Test set | messages rewritten in seeded order (seed 2026, alternating classes) until **200 per class pass every gate**; the stopping rule looks only at the gates |

## 2. Conditions (all keep the original headers)

| Condition | Body |
|---|---|
| `orig` | the original message, unchanged |
| `null_a` | the original body as plain text (`plain_body`: the plain part, or the HTML's visible text with each link written as `<URL>`) |
| `lex` | `null_a` text with WordNet 3.0 synonyms (first different single-word lemma of the first synset; words of four or more letters; links, addresses and placeholders untouched) swapped in until a fraction **0.364** of words has changed. That fraction is the median change of gate-passing pilot rewrites (`results/m3_pilot.json`). Seed from each message id. |
| `llm` | one paraphrase of the `null_a` text by **`gemma3:4b`** (Ollama manifest SHA-256 `68ceab7e468a31c988b44d5a4984a0e21f58c4f7158c6ce29c1804babac38df7`), Ollama 0.34.4, prompt `prompts/paraphrase.txt` (SHA-256 `8035b83e699983f7747ebf162c60fdb9315f18f46f8439a2ab8774c29f54c783`), temperature 0, seed 42, context 4,096 tokens, one discarded warm-up request per run; bodies over 1,200 words are not rewritten (counted). A leading "Here is ...:" line is removed before gating. |

## 3. Comparability gates (`src/rewrite/gates.py`)

A rewrite is analysed only if, compared with its `null_a` text:
- the set of links is identical, ignoring a trailing `/` or `.`;
- the set of numbers is identical, ignoring `,` and `.` separators;
- the set of addresses and `[NAME]`/`[PHONE]` placeholders is identical;
- the length ratio is between 0.5 and 2.0;
- `langdetect` returns English;
- it adds no refusal or meta-text.

Failures are counted per gate. Kept and discarded messages are compared on length, links and HTML share (selection bias).

**Human check:** both authors independently rate the same 30 gate-passing test pairs (15 per class, seed 2026), blind to class and detector output. We report agreement and Cohen's kappa per question, and the share judged equivalent. Embedding similarity was dropped (`DEVIATIONS.md`).

## 4. Detectors (static, offline)

| Layer | Version and configuration | Dev-calibrated threshold (flag if score > t) |
|---|---|---|
| L1 SpamAssassin | 4.0.1, shipped rules, scoreset 0, local tests only, Bayes and auto-learn off; native threshold 5.0 | `configs/thresholds.json` (9.393) |
| L2 TF-IDF + logistic regression | train split only, C = 100 chosen on dev, model SHA-256 in `configs/tfidf_lr.json`; native threshold logit 0 | `configs/thresholds.json` (−1.594) |
| L4 Lynceus | **TO BE CONFIRMED at the re-pin**: expected commit `ac2a5af9b4f209a76c881a5337c5291b25b54c63`, `rules/` hash `176402d19e7d02d741770bd858c74a4071b5ff2bc3539fd7f515242b21af485e`, tag `lynceus-eval-v1`; native = MALICIOUS or SUSPICIOUS. **Score:** Lynceus's risk (0-100) for every message, from its own scoring function on the rules that fired; Lynceus reports it only at 45 and above (UNKNOWN carries none), so the adapter re-runs that function with the SUSPICIOUS line at 0; 0 when no rule fired; errors have no score (`src/detectors/lynceus.py`, DEVIATIONS.md #16) | **to be calibrated on dev after the re-pin** |

Thresholds leave at most 1% of dev legitimate originals flagged. They are never changed after rewritten data is scored.

## 5. Analysis (`src/analysis/primary.py`, `src/analysis/stats.py`)

- **Contrasts (B vs A), paired per message:**
  - `llm vs null_a` (primary: only the wording differs);
  - `lex vs null_a`;
  - `llm vs lex` (does the LLM exceed any rewording, H3);
  - `null_a vs orig` (effect of the plain-text format).
- **Per layer, class and operating point (native, calibrated):**
  - lost and gained detections;
  - net change in percentage points, with a 95% cluster-bootstrap CI (template clusters, 10,000 resamples, seed 2026);
  - exact McNemar p;
  - mean paired score shift, with its CI.
- **Confirmatory family:** phishing, calibrated threshold, `llm vs null_a`, gate-passed set, one test per layer, Holm-adjusted. Everything else is descriptive.
- **Sensitivity:** every result is also given on all rewrites, not only gate-passed ones.
- **Cause:** rule and token accounting (which SpamAssassin rules, L2 tokens and Lynceus rules moved). Then **one** rule-based intervention on the main suspect, chosen from the accounting and declared in `DEVIATIONS.md` before it is run. Anything else is phrased "consistent with".

## 6. Claims policy

As README 6.3: no claims about commercial filters, real mail flow, adaptive attackers or human susceptibility. No causal wording without the intervention. Never "evades" as a general conclusion.
