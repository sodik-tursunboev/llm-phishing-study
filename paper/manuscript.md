<!--
Manuscript source. Every number is a {{placeholder}} filled from result and config files by
`python -m src.paper.build`; never type a number here. Text marked [AUTHORS: ...] or [CITE: ...]
must be written or verified by the authors. Target: about 2,000 words including the abstract.
-->

# Does One-Pass LLM Paraphrasing Lower Detection by Static Email Filters? A Paired, Offline Study

*Official topic: The Evasion Capabilities of LLM-Generated Phishing Payloads Against Static Security Architectures*

Sodiq Tursunboev, Kavish [AUTHORS: surname] · Vistula University · Architecture of Computers 2026/27 · [AUTHORS: student IDs]

## Abstract

[AUTHORS: write last, about 200 words, after the results exist.] Structure: problem (phishing text can now be rewritten by open-weight language models at no cost); question (when existing phishing emails are paraphrased once, how much does detection by static filters drop, and which layer loses it); method (paired, offline comparison of {{phishing_test}} phishing and {{ham_test}} legitimate test emails under four conditions, against SpamAssassin, a TF-IDF classifier and our own rule-based detector, Lynceus); main result with its confidence interval; the one cause tested by intervention; main limitation.

## 1. Introduction

Large language models (LLMs) can rewrite an email in seconds while keeping its meaning. For phishing this raises a practical question: do the static filters that still guard many mailboxes rely on wording that a paraphrase removes? [CITE: one or two sources on LLM-generated phishing, opened and checked]

We study the simplest version of this threat: an attacker who takes existing phishing emails and asks a local, open-weight model to rewrite each one once, with a neutral instruction and no feedback from any filter. We ask: **how much does detection by static email-security layers drop, and which layer accounts for the loss?** We also ask whether any drop is caused by the LLM rewrite itself rather than by re-encoding or by any change of words, and whether the rewrites stay valid (same intent, label and links).

Our contribution is a measurement with controls, not a new attack or a new detector. [AUTHORS: one sentence on what this study establishes beyond the coordinator's 2025 paper, written after reading it.]

## 2. Related work

[AUTHORS + CITE: about 150 words. Fill from research/related_work.md once the sources are opened. Must include the coordinator's 2025 paper, DOI 10.1109/CARS67163.2025.11337548, read by the authors.]

## 3. Method

The protocol was fixed before any rewritten email was scored (tag `protocol-freeze-v1`). Every change is listed in `DEVIATIONS.md`. Scoring and analysis ran in a container with networking disabled. Rewriting ran on the same machine against a local model server, so no email text left the machine.

### 3.1 Data

Phishing emails come from the Nazario phishing corpus (CC BY 4.0) [CITE: Nazario corpus], files collected from 2005 to 2022. To keep the phishing class human-written, we excluded messages dated on or after 30 November 2022, the public release of ChatGPT [CITE: OpenAI 2022]. Legitimate emails come from the SpamAssassin public corpus (easy_ham, easy_ham_2, hard_ham) [CITE: SpamAssassin corpus]. Raw files are pinned by SHA-256.

From {{phishing_read}} phishing and {{ham_read}} legitimate messages, we removed messages outside the study's text-only scope:
- {{phishing_non_text_part}} and {{ham_non_text_part}} with attachments or other non-text parts;
- {{phishing_not_english}} and {{ham_not_english}} not identified as English by langdetect [CITE: langdetect];
- {{phishing_empty}} and {{ham_empty}} with an empty body;
- {{phishing_after_cutoff}} phishing messages after the cutoff and {{phishing_date_unknown}} with no usable date.

We removed personal data: email local parts, phone numbers, and recipients' names. We then dropped near-duplicates ({{phishing_near_duplicate}} and {{ham_near_duplicate}}): messages whose 5-word phrases overlap by 80% or more (Jaccard similarity). This left {{phishing_kept}} phishing and {{ham_kept}} legitimate messages.

Messages sharing at least half of their 5-word phrases were grouped into template clusters. Whole clusters were assigned at random (fixed seed) to train, dev, test and pilot, so no campaign template appears in two splits. The test split holds {{phishing_test}} phishing and {{ham_test}} legitimate messages.

### 3.2 Conditions

Every test message is scored in four conditions (a paired design). The headers never change; only the body does. A 4-billion-parameter model cannot rewrite HTML reliably, so it rewrites the body as plain text: the plain part, or the visible text of the HTML with each link written out as `<URL>`.

- **orig:** the message unchanged.
- **null-A:** the plain-text body, unchanged. It differs from orig only in format, so comparing the rewrite with null-A isolates the wording. orig versus null-A shows the effect of the format itself.
- **lex:** the null-A text with WordNet synonyms [CITE: WordNet] swapped in until {{lex_dose}} of the words have changed, the median change made by the model on the pilot. Links, addresses and placeholders are untouched. This tests whether *any* rewording of that size lowers detection.
- **llm:** one paraphrase of the null-A text by `gemma3:4b` [CITE: Gemma 3], run locally through Ollama with temperature 0 and a fixed seed. The prompt was: *"Rewrite the following email in your own words. Keep every link, name, number and the requested action unchanged. Output only the rewritten email text."* It never mentions filters or detection, and the model received no feedback. Refusals were counted, not worked around.

We rewrote test messages in a fixed random order until 200 rewrites per class passed the comparability gates (3.3). The stopping rule looked only at the gates, never at any detector.

### 3.3 Comparability of rewrites

A rewrite enters the analysis only if, compared with its null-A text:
- it keeps the same set of links, numbers, addresses and placeholders, ignoring formatting such as "2,500" versus "2500";
- its length is between half and twice the original;
- it is still English;
- it adds no refusal or comment of its own.

These gates were fixed on a 53-message pilot ({{pilot_passed}} of 53 passed) before the main run. Messages that failed are counted and compared with those that passed.

For 30 rewrite pairs (15 per class), a second local model (llama3.2:3b, a different family from the generator) judged whether the rewrite keeps the requested action, the target and entities, the urgency, and the label. The first author then read every pair and corrected any judgment they disagreed with ({{judge_changed}} of 120 answers). We report the share of pairs judged equivalent on all four questions ({{judge_equivalent_rate}}). This is a check of the gates by a model and one author, not an independent two-rater audit.

### 3.4 Detectors

All three layers are static: fixed rules or a fixed model, with no learning from the messages they score. Each returns a score, a flag and the evidence behind it.

- **L1:** {{spamassassin_version}} [CITE: SpamAssassin], with its shipped rules, local tests only, and Bayes and auto-learning off.
- **L2, TF-IDF with logistic regression** [CITE: scikit-learn]: trained only on the train split ({{phishing_train}} phishing, {{ham_train}} legitimate), with its regularisation chosen on dev (C = {{l2_C}}, dev AUC {{l2_dev_auc}}), then frozen. It reads the subject and visible body text.
- **L4, Lynceus:** the first author's own rule-based phishing detector ({{lynceus_version}}), frozen before any rewrite was scored. We use its message engine unchanged, except that its Windows-only sandbox launcher is replaced by a subprocess inside our offline container. Its score is the risk Lynceus computes from the rules that fired, including below its own warning line. Because we evaluate our own tool, its results are reported under the same controls as the other layers. [AUTHORS: what was built by us and what was AI-assisted, from LYNCEUS_NOTES.md section 9.]

Each layer has two operating points: its native one, and a threshold fixed on dev originals so that at most 1% of legitimate dev emails are flagged (SpamAssassin {{spamassassin_threshold}}, TF-IDF {{tfidf_lr_threshold}}, Lynceus {{lynceus_threshold}}). Neither was changed after rewritten emails were scored.

### 3.5 Analysis

Every message is compared with itself in two conditions. The **primary contrast is llm versus null-A**. We also report lex versus null-A, llm versus lex, and null-A versus orig.

For each layer, class and operating point, we report:
- the detections lost and gained;
- the net change in percentage points, with a 95% cluster-bootstrap confidence interval (10,000 resamples of template clusters, fixed seed);
- an exact McNemar test;
- the mean change in score, with its interval.

The confirmatory test is phishing, at the calibrated threshold, llm versus null-A: one test per layer, Holm-adjusted. Everything else is descriptive.

An interval that excludes zero is read as a change. One inside ±2 points is read as "no change larger than 2 points". Anything else is inconclusive. A message with a scoring error on either side is excluded from that layer's contrast and counted. Every result is repeated on all rewrites, not only those passing the gates.

We then separate *what moved* from *why*. SpamAssassin's score is a sum of rule points, and the classifier's logit is a sum of token contributions, so we can list which rules and tokens account for the change. We claim a cause only for {{intervention_property}}: we apply that one change to the originals with a rule-based (non-LLM) edit and measure whether the same layer loses detections.

## 4. Results

[Filled after the main run. Planned content, all from result files:]

**Table 1.** Detection by layer and condition for phishing (detection rate) and legitimate mail (false-positive rate): native and dev-calibrated operating points, net change versus orig with 95% CI, McNemar p.

**Table 2.** Rewrite validity: gate pass rates, refusals, embedding similarity, audit agreement (kappa).

**Figure 1.** Paired score shift per layer (orig to llm), phishing and legitimate.

[AUTHORS: describe the findings in plain words. Observation first, then accounting, then the intervention result.]

## 5. Discussion and limitations

[AUTHORS: discussion after the results.] The study has deliberate limits:
- The attacker is non-adaptive and makes one pass, which underestimates a determined attacker.
- The corpora are old (legitimate mail from 2002 to 2003, phishing from 2005 to 2022), so "human versus LLM" style is mixed with era; pairing controls content, not era.
- We use one small open-weight model, not frontier models.
- SpamAssassin run offline is not a commercial filter; we test static layers only, without sender reputation, DNS or authentication checks.
- Text-only, English-only messages.
- We evaluate our own tool.
- The meaning check covers only 30 pairs, judged by a small local model and checked by one author who saw the model's answers first.
- Rewrites run on plain text, so the HTML structure of the original is not kept; null-A carries the same format, so the comparison is fair, but it is not the attacker's full message.
- Only rewrites that kept every link and number are analysed; this is a selection, which we compare with the discarded rewrites.

## Declarations

**AI use.** [AUTHORS: build from AI_LOG.md.] Claude Code (Anthropic) wrote most of the study code and draft text under the authors' direction. The authors tested the code, re-ran the analyses, checked every number against the result files and verified every source.

**Ethics and model licence.** We only rewrote existing phishing emails from a public corpus, offline. Nothing was sent, and the rewrites are not published. The generator's use policy (Gemma Prohibited Use Policy) bars generating content for phishing, and makes no research exception. We used it for defensive evaluation only, and we declare that choice here [CITE: Gemma Prohibited Use Policy]. [AUTHORS: confirm wording.]

**Data and code.** Code, configurations, manifests, hashes and aggregate results: [AUTHORS: repository link]. Raw corpora are not redistributed; they are re-downloaded and verified by hash. Raw rewrites are available to reviewers on request.

**Contributions.** Sodiq Tursunboev designed and ran the study and developed Lynceus. Kavish [AUTHORS: surname] rated the audit sample independently and verified every reference and number. [AUTHORS: confirm.]

**Conflict of interest.** Lynceus is the first author's own tool.

## References

[Only sources an author has opened, from references/evidence_trail.csv, after Kavish's check.]
