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

The protocol was fixed before any rewritten email was scored (tag `protocol-freeze-v1`). Every later change is listed in `DEVIATIONS.md`. All experiments ran offline, in a container with networking disabled.

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

Every test message is scored in every condition (a paired design). Only the body changes; headers stay as they are.
- **orig:** the message unchanged.
- **null-A:** the body re-encoded through the same path as a rewrite, with no LLM. This checks that our pipeline itself changes nothing.
- **lex:** a deterministic synonym substitution that changes the same median share of words as the LLM rewrites. This answers whether *any* rewording lowers detection.
- **llm:** one paraphrase by {{generator}}, run locally with fixed decoding ({{decoding}}). The prompt was: *"Rewrite the following email in your own words. Keep every link, name, number and the requested action unchanged. Output only the rewritten email text."* It never mentions filters or detection. Refusals are counted, not worked around.

### 3.3 Comparability of rewrites

A rewrite enters the analysis only if it passes pre-declared gates:
- identical URL multiset;
- the same entities and numbers;
- length ratio within {{length_band}};
- the same language;
- no meta-text or refusal.

Failures are counted and compared with passing messages. We also report embedding similarity between original and rewrite. Both authors independently rated the same 30 randomly drawn pairs, blind to detector output, on whether the rewrite keeps the requested action, target, urgency and label; we report agreement (Cohen's kappa).

### 3.4 Detectors

All three layers are static: fixed rules or a fixed model, with no learning from the messages they score. Each returns a score, a flag and the evidence behind it.

- **L1:** {{spamassassin_version}} [CITE: SpamAssassin], with its shipped rules, local tests only, and Bayes and auto-learning off.
- **L2, TF-IDF with logistic regression** [CITE: scikit-learn]: trained only on the train split ({{phishing_train}} phishing, {{ham_train}} legitimate), with its regularisation chosen on dev (C = {{l2_C}}, dev AUC {{l2_dev_auc}}), then frozen. It reads the subject and visible body text.
- **L4, Lynceus:** the first author's own rule-based phishing detector ({{lynceus_version}}). We use its message engine unchanged, except that its Windows-only sandbox launcher is replaced by a subprocess inside our offline container. Because we evaluate our own tool, its results are reported under the same controls as the other layers. [AUTHORS: what was built by us and what was AI-assisted, from LYNCEUS_NOTES.md section 9.]

Each layer has two operating points: its native one, and a threshold fixed on dev originals so that at most 1% of legitimate dev emails are flagged (SpamAssassin {{spamassassin_threshold}}, TF-IDF {{tfidf_lr_threshold}}, Lynceus {{lynceus_threshold}}). Neither was changed after rewritten emails were scored.

### 3.5 Analysis

For each layer, class and condition, we compare each message with itself under orig. We count lost detections (detected as orig, missed after rewriting) and gained ones. We report the net change in percentage points with a 95% cluster-bootstrap confidence interval (10,000 resamples of template clusters, fixed seed), and an exact McNemar test.

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
- The human audit covers only 30 pairs.

## Declarations

**AI use.** [AUTHORS: build from AI_LOG.md.] Claude Code (Anthropic) wrote most of the study code and draft text under the authors' direction. The authors tested the code, re-ran the analyses, checked every number against the result files and verified every source.

**Data and code.** Code, configurations, manifests, hashes and aggregate results: [AUTHORS: repository link]. Raw corpora are not redistributed; they are re-downloaded and verified by hash. Raw rewrites are available to reviewers on request.

**Contributions.** Sodiq Tursunboev designed and ran the study and developed Lynceus. Kavish [AUTHORS: surname] rated the audit sample independently and verified every reference and number. [AUTHORS: confirm.]

**Conflict of interest.** Lynceus is the first author's own tool.

## References

[Only sources an author has opened, from references/evidence_trail.csv, after Kavish's check.]
