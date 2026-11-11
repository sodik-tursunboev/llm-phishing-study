# LLM-Rewritten Phishing vs. Static Email Defenses

Controlled, offline, reproducible study · Vistula University · Architecture of Computers 2026/27 · Student Research Challenge

**Authors:** Sodiq Tursunboev, Kavish [surname] (pair)
**Official topic:** The Evasion Capabilities of LLM-Generated Phishing Payloads Against Static Security Architectures
**Version:** v1 · 2026-11-11 · **Scope update v3 (2026-11-11) supersedes parts of this brief; every change is listed in `DEVIATIONS.md`.**

> **Claude Code: read this whole file before acting.** It is the single source of truth. Work one milestone at a time (section 10), stop at every **[GATE]**, and keep replies short (section 9). Start with **M0 only**. Never invent results, references, or facts about Lynceus: derive them from code and data, or write UNKNOWN.

## 1. Stakes and rules (Student Handbook, version of 5 Nov 2026)

- The project is **50% of the lecture grade**, scored out of 100, **pass = 60**. Rubric: question and relevance 20 · methodology 25 · evidence and reliability 25 · analysis and interpretation 15 · integrity and reproducibility 10 · writing 5.
- **Final PDF: Mon 30 Nov 2026, one upload to Platon** (one attempt, no routine revisions). The proposal was approved on 10 Nov. No more individual feedback, and no progress emails are owed.
- About 10 finalists (+0.5 grade bonus) are chosen on contribution, baseline choice, confounder control, reproducibility, limitations and oral understanding. **Defenses: 7-11 Dec.** Negative results and rigorous replications are explicitly valued. Fabricating or hiding results is an integrity violation.
- Mandatory: AI-use declaration; reproducibility package (code, dependency list, input data or generation procedure, raw results, run instructions, limitations); real, checked references (they are audited). A research letter of at most 3,000 words including the abstract is preferred.
- Priorities: **(1) pass safely** with real data and honest claims, (2) finalist quality, (3) portfolio value.

## 2. Coordinator guidance (binding)

The direction is approved. The coordinator asked us to:

1. Read *Evaluating the Effectiveness of Existing Phishing Detectors on AI Generated Phishing Emails* (2025), DOI 10.1109/CARS67163.2025.11337548. By his description it already studied LLM-rewritten phishing **and legitimate** emails against existing detectors. The paper must say what we establish **beyond** it. **[GATE]** The authors read it and fill `research/related_work.md`. Claude Code could not access it and must never summarize it from memory.
2. Show how rewritten messages are established as **comparable** to the originals (section 5.3).
3. Separate an **observed** detection difference from an **explanation of its cause** (section 6.2).
4. Explain Lynceus: what we built ourselves and how it fits the evaluation (section 7).
5. Keep experiments **offline and controlled**, document methodology and limitations, and release only **safe, sanitized** materials (section 4).
6. He wants the finished investigation, evidence and reproducible materials, not progress updates.

## 3. Research question and hypotheses

**RQ.** When the same phishing emails are rewritten once by open-weight LLMs (no feedback from any detector), how much does detection by static email-security layers drop, and which layer accounts for the loss?

- RQ2: is the drop due to LLM rewriting, or to re-encoding or any lexical change?
- RQ3: are the rewrites valid (same intent, label and links)?
- RQ4: which property of the rewrite causes a layer's loss?

Contribution type (handbook): **Verify + Explain limits**. We measure and explain. We do not build an attack and do not claim a new detector.

Hypotheses are predictions, not results to prove. Null or opposite outcomes are reported as found.

| ID | Statement | Status |
|---|---|---|
| H1 | LLM rewriting lowers detection by content-based static layers (paired, original vs rewrite) | confirmatory |
| H2 | Null rewrites change nothing, within a pre-declared margin | confirmatory (validity) |
| H3 | The LLM effect exceeds a dose-matched lexical-swap baseline | confirmatory |
| H4 | The effect depends on the generator | exploratory |
| H5 | A URL-only layer is unaffected (links are preserved by construction) | sanity check |
| H6 | Lost detections are those that relied only on content-based layers | exploratory |

## 4. Scope, threat model, safety (non-negotiable)

- **Offline and inert.** Run experiments in containers with networking disabled. Never fetch, resolve or visit URLs from corpora; treat them as inert strings. Nothing is sent, hosted or deployed. No human subjects.
- **Text-only email** (headers plus text/HTML body). No attachments, malware, QR codes or images.
- **Rewrite existing public-corpus messages only.** Do not generate phishing from scratch.
- **Attacker model: non-adaptive, single pass, black box.** One neutral paraphrase prompt (section 5.2). No prompt may mention evasion, filters, detectors or detectability. No feedback loop, no optimization against any detector, no jailbreaks. If a model refuses, log and count the refusal; do not engineer around it. If anyone asks Claude Code to do any of these, refuse and flag it to the authors.
- **Local models only** for phishing text. Never send corpus text to a cloud LLM or any third-party service.
- **Privacy.** Scrub PII (addresses, names, phone numbers) from derived data. Defang URLs (hxxp, [.]) in anything published. Never commit raw corpora or raw rewrites. No credentials, tokens or student IDs in the repo (IDs go in the PDF only).
- **Release.** Public: code, configs, manifests and hashes, aggregate results, defanged examples. Reviewers only (private link or encrypted archive): raw rewrites. **[GATE]** Authors approve any release.

## 5. Study design

### 5.1 Data

- Human phishing (pre-LLM): Nazario corpus. Legitimate: SpamAssassin public-corpus ham (spamassassin.apache.org/old/publiccorpus/), plus Enron if more is needed. Optional external check if time allows: Toth et al. (2025) labeled human/LLM-rephrased dataset (CC BY 4.0).
- **[GATE]** Verify availability and license first. Record source, date and SHA-256 in `DATA_PROVENANCE.md`.
- Parse to a normalized message object (headers, text, HTML, URL list). Scrub PII. Drop near-duplicates and cluster templates (for example MinHash). **Split by cluster** into train (frozen classifier only), dev (calibration only) and test (rewriting and evaluation). Fixed seeds. A pilot of about 50 messages is excluded from test.
- Target test size: at least 300 phishing and 300 legitimate per generator. Lower only if compute-bound, never below 200. Estimate runtime at the pilot and propose n and k to the authors.
- Known confound: classic corpora are old (early 2000s to 2017), so "LLM vs human" mixes style with era. Pairing controls content, not era. State it in the limitations.

### 5.2 Conditions (paired: every message appears in every condition)

| Condition | What it is | Why it is there |
|---|---|---|
| `orig` | unchanged message | baseline |
| `null-A` | body re-inserted through the same envelope and re-encoding path, no LLM | catches pipeline and MIME artifacts |
| `null-B` | LLM asked to reproduce the text verbatim (primary generator only unless cheap) | catches LLM input/output artifacts |
| `lex` | deterministic synonym swap, dose-matched to the median fraction of tokens the LLM rewrites change | "any rewrite" baseline |
| `llm-G1..Gk` | one neutral LLM paraphrase per generator; k = 2-3 open-weight models of different families or sizes, run via Ollama with pinned digests | treatment |

Both classes (phishing and legitimate) go through all conditions, so false positives on rewritten legitimate mail are measured too.

Prompts (store verbatim in `prompts/`, hash them, never edit after the freeze):
- Paraphrase: "Rewrite the following email in your own words. Keep every link, name, number and the requested action unchanged. Output only the rewritten email text."
- Verbatim (null-B): "Copy the following email exactly. Output only the email text."

Fixed decoding (temperature, top_p, seed, context length), one pass, headers and MIME wrapper preserved, only the body changes.

### 5.3 Comparability protocol (answers coordinator question 1)

"Comparable" means: same intent and label, same links, entities and numbers, similar length and structure, no artifacts.

1. **Hard gates** (pre-declared): URL multiset identical · entities and numbers preserved · length ratio inside a band · same language · no meta or refusal text. Failures are discarded **and counted**. Compare discarded vs kept messages (selection-bias check).
2. **Semantic checks:** embedding cosine and two-way entailment with a local NLI model. Calibrate thresholds on the pilot against author labels, before the freeze.
3. **[GATE] Human audit (authors only; Claude Code must not rate).** Stratified random sample of 60-100 pairs (class x generator). Both authors rate independently, blind to detector outputs: same requested action? same target and entities? same urgency? label still correct? Report % equivalent per generator and Cohen's kappa. Adjudicate disagreements and log them.
4. **Covariate balance:** length, link count, readability, typo rate, urgency-word density, HTML vs plain; standardized mean differences. Use them as covariates in the paired model (conditional logistic regression) and in a length-matched subset.
5. **Sensitivity:** report every main result on (a) all rewrites, (b) gate-passing, (c) strict-pass (gates plus audited equivalence). If conclusions differ, say so.

### 5.4 Detectors (all static and frozen)

Common interface: `score(msg) -> {score, flagged, evidence, version, config_hash}`. Deterministic and offline. Errors and timeouts are logged and reported, never silently counted as benign or flagged.

- **L1 SpamAssassin:** pinned version and ruleset snapshot (no `sa-update` mid-study); local tests only; Bayes, auto-learn and AWL off; note the active scoreset. Record total score and per-rule hits. Partition rules into content-based vs header/URL-based (task R5).
- **L2 frozen TF-IDF + logistic regression:** trained on the train split (pre-LLM emails) only; hyperparameters chosen on dev; then frozen (artifact plus hash). Record logit and per-token contributions.
- **L3 URL-lexical layer** (static rules or features): sanity layer, since links are preserved.
- **L4 Lynceus:** see section 7.
- **Operating points:** SpamAssassin default threshold plus a dev-calibrated one. For L2 and L4, fix the threshold on **dev originals** at a target false-positive rate (default 1%). Always add threshold-free results (AUC, paired score shift), because baselines may sit near floor or ceiling. Never retune after seeing rewritten-data results.
- A non-static LLM-based detector is out of scope unless time remains, and would be labeled non-static.

### 5.5 Freeze

Before any rewritten data is scored: tag `protocol-freeze-v1` and write `PROTOCOL.md` listing SpamAssassin version and ruleset date, model digests, prompt hashes, decoding parameters, gate and semantic thresholds, detector thresholds, split seeds and analysis-script hashes. After the freeze, every change goes to `DEVIATIONS.md` (what, why, when). If it affects scoring, **re-run all conditions** (no selective re-runs).

## 6. Analysis plan

### 6.1 Primary (confirmatory)

For each layer x generator x class: paired outcomes (detected/missed for phishing, flagged/not for legitimate). Report lost (b) and gained (c) detections, net change in percentage points with a 95% cluster-bootstrap CI (cluster = template, 10,000 resamples, fixed seed), McNemar exact test, Wilcoxon signed-rank on paired scores, and AUC. Apply Holm correction across the confirmatory family. For null conditions run an equivalence test against a pre-declared margin (default +-2 pp). If it fails, stop and debug the pipeline before interpreting anything.

### 6.2 Difference vs cause (answers coordinator question 2)

Keep four levels separate in code, tables and prose:

1. **Observation:** the paired drop per layer (6.1).
2. **Accounting:** exact decomposition of the change. The SpamAssassin score is a sum of rule hits; the L2 logit is a sum of token weights times features. This shows *what moved*, not *why*.
3. **Causal explanation**, claimed only with intervention evidence:
   - *Sufficiency:* apply a single-property, **rule-based (non-LLM)** edit to the original (two or three property types fixed at the freeze, for example surface-error normalization, lexicon-class substitution, format normalization). Does the same layer lose detections? Report the fraction of the LLM effect reproduced.
   - *Necessity:* restore that property in the rewrite. Does detection recover?
   - *Dose-response* within pairs: more change, bigger drop?
   - Rule out alternatives: pipeline artifacts (null conditions), length and format (covariates), selection (discards), threshold choice (score-level results), single-generator quirks (replicate across generators).
   Anything without an intervention is labeled "exploratory" and phrased "consistent with". The paper lists the alternative explanations not excluded.
4. **Unique-catch (exposure):** the share of originally detected phishing caught **only** by content-based layers. Descriptive, not causal.

### 6.3 Claims policy

- May say: "Under this predeclared protocol, layer X lost N of M originally detected messages (95% CI ...); these confounders and limits remain."
- May not say: anything about commercial filters, real mail flow, adaptive attackers or human susceptibility; causal wording without an intervention; "evades" as a general conclusion.

## 7. Lynceus (the authors' own tool; Claude Code knows it)

Treat Lynceus as a pluggable layer (L4), **never as the contribution**. Do not assume capabilities: derive them from the code.

1. Write `LYNCEUS_NOTES.md`: what it does, inputs and outputs, version/commit, license, third-party components, known limits. **[GATE]** The authors confirm the authorship split (written by us / AI-assisted / third-party). Git history alone does not establish contributions, and the coordinator asked what we built ourselves.
2. Build an adapter for the common interface (deterministic, offline) with tests. If Lynceus cannot score an email as a static, offline layer, do not force it: write UNKNOWN in `LYNCEUS_NOTES.md` and ask the authors which role fits (for example the URL layer, or tooling only).
3. Freeze: tag `lynceus-eval-v1` before scoring any rewritten data. Never tune rules, weights or thresholds on rewritten data. A bug found after the freeze goes to `DEVIATIONS.md` and triggers a full re-run of all conditions.
4. Go/no-go **Sat 14 Nov**. Stable means: runs end to end on the full original test split, deterministic, adapter tests pass. Otherwise exclude it from the main analysis, list it as future work, and say so in the paper (the proposal made inclusion conditional on 14 Nov).
5. Conflict of interest: we evaluate our own tool. Report its results whatever they are, with the same controls as every other layer.

## 8. Research tasks for Claude Code

Outputs go in `research/`. Use only sources actually opened. Every file ends with "Open questions" and "Not verified". Search results are leads, not evidence.

- **R1 Related work** (`related_work.md`): table with columns ref · year · generators · rewrite vs generate · detectors · data · metrics/stats · rewrite-validity check? · null/lexical controls? · layer or rule analysis? · code/data released · limits. Leads found by web search on 2026-11-08 (**unverified until opened**): Afane et al. 2024, arXiv:2411.13874 · Josten & Weis 2024, arXiv:2408.14293 (public pipeline: github.com/MalteJosten/llm-spam-test) · Chen et al., SoK on LLM-generated phishing, arXiv:2508.21457 (title differs across versions; cite the version read) · Toth et al. 2025, arXiv:2511.21448 · Frontiers in Big Data 2026, doi:10.3389/fdata.2026.1883452 · EdgeGuard, Springer 2026, doi:10.1007/s44443-026-01351-9 · arXiv:2607.18429 (TF-IDF+LR vs DistilBERT robustness) · Kulal et al. 2025, arXiv:2510.11915 · dataset-age context: arXiv:1911.00953. Plus the coordinator's 2025 paper (authors read it).
- **R2 Data:** availability, license, hashes, PII risk, fallback sets.
- **R3 Rewrite validity:** accepted ways to check paraphrase equivalence (embedding, NLI, human) and how to calibrate thresholds.
- **R4 Attribution:** ablation and intervention designs for text classifiers; additive decompositions; propose 2-3 interventions.
- **R5 SpamAssassin:** scoresets, local-only behavior, content vs header/URL rule categories, version pinning.
- **R6 Statistics:** confirm tests; simulate precision to set n; pre-declare margins.

## 9. Working rules for Claude Code

- One milestone per session. Small commits. Never force-push. Never commit data or secrets.
- Tests alongside code. Every number in the paper comes from a script output file; nothing is hand-typed.
- No silent drops: every message is accounted for in every condition.
- Dev is for calibration only. Never tune on test. Freeze before scoring rewrites.
- Write UNKNOWN when unknown. Stop at every **[GATE]** and ask.
- Log every substantive AI use in `AI_LOG.md` (tool, date, purpose, how verified).
- Write code the authors can explain at the defense: simple, commented on the *why*.
- **Reply format, at most 100 words:** Done · Verified (how) · Needs human · Next. No log dumps.

## 10. Milestones (2026)

| ID | When | Deliverable and done-when |
|---|---|---|
| M0 Setup | Wed 11 Nov | Repo skeleton, pinned environment, SpamAssassin in a no-network container, `.gitignore` for data, secret/PII scan hook, `ENVIRONMENT.md`. Done when the check command passes and a test proves the container has no network. |
| M1 Data | 11-12 Nov | **[GATE]** license check, then acquire, manifests and hashes, parser, PII scrub, dedupe, cluster, splits, stats table. Done when hashes verify and a test proves no cluster sits in two splits. |
| M2 Detectors | 12 Nov | L1-L3 behind the interface; L2 trained on train only; re-runs give identical score hashes; Lynceus adapter (section 7). |
| M3 Rewrite and pilot | 12 Nov | Pinned models, hashed prompts, null-A/B, lex baseline, gates, refusal logging, 50-message pilot, shuffled blind audit sheet for the authors, pilot report (gate pass rates, refusal rate, floor/ceiling check, runtime, proposed thresholds). |
| M4 Freeze | Fri 13 Nov | **[GATE]** authors approve. Write `PROTOCOL.md`, tag `protocol-freeze-v1`, start `DEVIATIONS.md`. |
| M5 Main run | Sat 14 - Fri 20 Nov | Lynceus go/no-go on 14 Nov. Generate, gate, score all layers and conditions. Resumable, incremental outputs. Done when counts reconcile across conditions. |
| M6 Analysis | 21-25 Nov | **[GATE]** authors deliver audit ratings by 21 Nov. Primary tests, comparability, accounting, interventions, unique-catch; all tables and figures generated by scripts. A minimum-viable results summary exists by 24 Nov. |
| M7 Paper and package | 26-29 Nov | Draft from result files; authors rewrite and verify every claim; reference audit; AI declaration; clean-environment reproduction dry run; release scan (PII, live URLs); final PDF. **[GATE]** authors submit on Platon by Sun 29 Nov (deadline Mon 30 Nov). |

**Cut order if behind** (drop from the top of this list first): external dataset → third generator → Lynceus → unique-catch → interventions → token-level accounting. **Never cut:** paired comparison, null and lexical controls, comparability audit, freeze, limitations, reproducibility package.

**Risks and fallbacks:** floor effect on L1 (report AUC and score shift, never retune post hoc) · model refusals (count them, use other generators) · compute (reduce n or k, not below 200 per class) · Lynceus unstable (exclude and say so) · dataset access (fallback to Toth et al.).

## 11. Paper and submission

- Format: research letter of at most 3,000 words including the abstract. PDF correctly named **[GATE: check the Platon instructions]**, with title, authors, **student IDs**, abstract, method, results/discussion, references, **AI-use declaration**, repo and evidence links.
- Word budget: abstract 200 · introduction and related work 450 · methods 800 · results 700 · discussion and limitations 500 · declarations and references the rest. Three or four figures.
- Must state, in one sentence, what we establish **beyond** the coordinator's 2025 paper (written after the authors read it).
- References: only sources an author has opened. Keep `references/evidence_trail.csv` (title, authors, year, venue, link/DOI, claim supported, verified by, date). No AI-generated bibliography. No paraphrasing tools on the text.
- AI declaration: built from `AI_LOG.md` in the handbook's style: tools used (Claude, Claude Code), what for, and that the authors verified sources, tested code and checked all calculations.
- Definition of done: clear question · method answers it · real data and honest conclusions · sources opened and checked · AI use declared · names and IDs present · reproducibility links work · correct final PDF · Platon upload completed.

## 12. Repo layout and reproduction

```
README.md PROTOCOL.md DEVIATIONS.md LIMITATIONS.md DATA_PROVENANCE.md
LYNCEUS_NOTES.md CONTRIBUTIONS.md AI_LOG.md ENVIRONMENT.md
prompts/ configs/ src/{data,rewrite,gates,detectors,interventions,analysis}/
research/ references/ paper/ tests/ results/ data/ (gitignored)
```

One command per stage (data, rewrite, score, analyze, paper). At M7, move this brief to `docs/BRIEF.md` and write a short reviewer-facing README with exact run instructions, so a reviewer can reproduce everything from manifests and hashes.

## 13. Open items for the authors

1. Kavish's surname, and roles in `CONTRIBUTIONS.md`. Both authors must be able to defend everything (7-11 Dec).
2. Read the coordinator's 2025 paper; fill the comparison row in `research/related_work.md`.
3. Confirm the Lynceus authorship split and status.
4. Approve generators, n, thresholds and interventions (M3-M4).
5. Do the human audit (M6).
6. Confirm Platon PDF naming and repo visibility (public vs reviewer-only).

## 14. Limitations to state in the paper

Non-adaptive attacker (underestimates the worst case) · old corpora (era confound) · small open-weight local models, not frontier ones · SpamAssassin in offline mode is not Gmail or Microsoft · text-only, English-only, single pass · static layers only (no sender reputation, DNS or authentication checks) · we evaluate our own tool · small human-audit sample.
