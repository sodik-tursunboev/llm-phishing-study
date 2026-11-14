# LLM-rewritten phishing vs. static email defences

A paired, offline study by **Sodik Tursunboev** and **Kavish Chaudhari** (Vistula University, Architecture of Computers 2026/27, Student Research Challenge).

**Question.** When existing phishing emails are rewritten once by a local open-weight model, with no feedback from any filter, does detection by static email layers drop, and which layer accounts for it?

**Answer, under our protocol.** We compared each LLM rewrite with a canonical plain-text version of the same email (null-A). At the calibrated thresholds, the rewrite did not lower phishing detection: for SpamAssassin and a TF-IDF classifier a drop larger than 2 points is ruled out, and Lynceus sat at its floor. The large effect came from canonicalizing the emails to plain text, which strips the HTML and drops links outside anchors: sending the rewrite as plain text instead of the original cost Lynceus 21 points at its default threshold, all of it from canonicalization. Every number is in `results/`, and the paper is filled from those files.

## Audit map: where to check each claim

| To check | Look at |
|---|---|
| The paper and where its numbers come from | `paper/manuscript.md`; `src/paper/build.py` fills every `{{number}}` from `results/` and `configs/` |
| The plan was fixed before any rewrite was scored | `PROTOCOL.md`, git tag `protocol-freeze-v1` (`cf4accd`) |
| Lynceus was frozen before scoring | `LYNCEUS_NOTES.md`, git tag `lynceus-eval-v1` (`450e6d8`), Lynceus commit `ac2a5af` |
| Every change to the plan, and why | `DEVIATIONS.md` (#1–#25) |
| Pinned environment | `Dockerfile` (base image by digest, SpamAssassin by version, WordNet by hash), `requirements.txt`, `ENVIRONMENT.md` |
| Data sources, licences, file hashes | `DATA_PROVENANCE.md`, `configs/raw_files.csv` |
| Every message, its hash, cluster and split | `results/m1_messages.csv`, `results/m1_sources.csv`, `results/m1_splits.csv` |
| Thresholds (fixed on dev) and the frozen classifier | `configs/thresholds.json`, `configs/tfidf_lr.json` |
| Prompts (hashed) | `prompts/paraphrase.txt`, `prompts/judge.txt` |
| Main results (Table 1) | `results/primary_test.csv` (rows `set=gate_passed`) |
| Paired score intervals; end-to-end change split into canonicalization and wording (added after the freeze) | `results/exact_test.csv`, `results/decomposition_test.csv` |
| Gates, kept vs discarded, canonicalization | `results/gates_test.csv`, `results/selection_test.csv`, `results/canonical_test.json` |
| What moved (rules and words) | `results/accounting_test.csv` |
| 30-pair meaning check | `results/judge.json` (model judge, checked by Kavish); blind two-author rating: `docs/RATING.md`, then `results/ratings.json` |
| Pilot | `results/m3_pilot.json`, `results/*_pilot.*` |
| Who did what; AI use | `CONTRIBUTIONS.md`, `AI_LOG.md` |
| Every reference and the claim it supports | `references/evidence_trail.csv` |
| Related work compared field by field | `research/related_work.md` |
| The original brief (the docs' "README section N") | `docs/BRIEF.md` |

## Reproduce

You need Docker. Rewriting also needs Ollama 0.34.4 on the host with `gemma3:4b` (manifest SHA-256 `68ceab7e…8df7`) and `llama3.2:3b` (`a80c4f17…8b72`); full digests are in `PROTOCOL.md` and `src/analysis/judge.py`.

Run every command from the repository root; `${PWD}` works in bash and in PowerShell. Steps 2, 6 and 8a need the network. Every other step runs with `--network none`.

1. **Build the image:**

```bash
docker build -t llm-phishing-study .
```

2. **Download the corpora and check their hashes:**

```bash
docker run --rm -v "${PWD}:/work" -v llm-phishing-data:/work/data llm-phishing-study python -m src.data.download
```

3. **Lynceus snapshot.** The source is shared with reviewers on request. Create the snapshot with the `git archive` command in `ENVIRONMENT.md`, at commit `ac2a5af`.

4. **Data stage:** parse, scrub personal data, filter, deduplicate, cluster, split. About 5 minutes.

```bash
docker run --rm --network none -v "${PWD}:/work" -v llm-phishing-data:/work/data llm-phishing-study python -m src.data.prepare
```

5. **Detectors:** fit the classifier, score dev with each layer, fix the thresholds.

```bash
docker run --rm --network none -v "${PWD}:/work" -v llm-phishing-data:/work/data -v lynceus-src:/opt/lynceus:ro llm-phishing-study sh -c "python -m src.detectors.tfidf_lr && python -m src.detectors.run spamassassin dev && python -m src.detectors.run tfidf_lr dev && python -m src.detectors.run lynceus dev && python -m src.detectors.calibrate"
```

6. **Rewriting, through the host's Ollama.** It stops once 200 rewrites per class pass the gates; about 5 hours on a 4 GB GPU.

```bash
docker run --rm -v "${PWD}:/work" -v llm-phishing-data:/work/data llm-phishing-study python -m src.rewrite.generate test 200
```

7. **Scoring and analysis:**

```bash
docker run --rm --network none -v "${PWD}:/work" -v llm-phishing-data:/work/data -v lynceus-src:/opt/lynceus:ro llm-phishing-study sh -c "python -m src.analysis.score spamassassin test && python -m src.analysis.score tfidf_lr test && python -m src.analysis.score lynceus test && python -m src.analysis.primary test && python -m src.analysis.accounting test && python -m src.analysis.canonical test && python -m src.analysis.exact test"
```

8. **Meaning check.**

a. The judge model pre-fills `ratings/sheet_model.csv`:

```bash
docker run --rm -v "${PWD}:/work" -v llm-phishing-data:/work/data llm-phishing-study python -m src.analysis.judge run
```

b. A human types their name in `checked` for each pair. Then the summary counts who checked what:

```bash
docker run --rm --network none -v "${PWD}:/work" -v llm-phishing-data:/work/data llm-phishing-study python -m src.analysis.judge summary
```

c. Both authors rate the same 30 pairs blind and independently; then the agreement and Cohen's kappa are computed. Steps and rules: `docs/RATING.md`.

9. **Paper:** fill every number from the result files.

```bash
docker run --rm --network none -v "${PWD}:/work" llm-phishing-study python -m src.paper.build
```

10. **Check command:** 47 tests, offline.

```bash
docker run --rm --network none -v "${PWD}:/work" -v llm-phishing-data:/work/data -v lynceus-src:/opt/lynceus:ro llm-phishing-study python -m pytest -q -p no:cacheprovider
```

**What reproduces exactly:**
- Data preparation, classifier fitting and all scoring are deterministic: two runs give byte-identical outputs (hashes in `ENVIRONMENT.md` and `LYNCEUS_NOTES.md`).
- Rewriting uses temperature 0, a fixed seed and one discarded warm-up request; repeated requests gave identical output in our checks.
- A full regeneration on other hardware was **not** verified byte for byte.

## Not in this repository

- **Raw corpora:** download them with step 2; the hashes are checked.
- **Rewrites and the rating sheet:** they contain phishing text, so they go to reviewers on request.
- **Student IDs:** in the PDF only.
- **The Lynceus source:** a separate repository, available to reviewers on request.
