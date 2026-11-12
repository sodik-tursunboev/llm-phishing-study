<!--
Manuscript source. Every number is a {{placeholder}} filled from result and config files by
`python -m src.paper.build`; never type a number here. Text marked [AUTHORS: ...] or [CITE: ...]
must be written or verified by the authors. Target: about 2,000 words including the abstract.
-->

# Does One-Pass LLM Paraphrasing Lower Detection by Static Email Filters? A Paired, Offline Study

*Official topic: The Evasion Capabilities of LLM-Generated Phishing Payloads Against Static Security Architectures*

Sodik Tursunboev, Kavish Chaudhari · Vistula University · Architecture of Computers 2026/27 · Student IDs: {{student_ids}}

## Abstract

Large language models can rewrite a phishing email in seconds. We asked whether one neutral paraphrase by a small local model lowers detection by three static email layers: SpamAssassin, a TF-IDF classifier with logistic regression, and Lynceus, the first author's rule-based detector.

Using public corpora, we scored {{gates_phishing_passed}} phishing and {{gates_ham_passed}} legitimate test emails in four versions: the original, a plain-text copy, a copy after a dictionary synonym swap, and a rewrite by gemma3:4b that had to keep every link, number and entity.

Against the plain-text copy, the rewrite did not lower phishing detection at the calibrated thresholds. The change, with its 95% confidence interval, was {{spamassassin_phishing_calibrated_llm_vs_null_a_signed}} percentage points for SpamAssassin {{spamassassin_phishing_calibrated_llm_vs_null_a_ci}}, {{tfidf_lr_phishing_calibrated_llm_vs_null_a_signed}} for TF-IDF {{tfidf_lr_phishing_calibrated_llm_vs_null_a_ci}} and {{lynceus_phishing_calibrated_llm_vs_null_a_signed}} for Lynceus {{lynceus_phishing_calibrated_llm_vs_null_a_ci}}. At its native threshold, Lynceus flagged more rewritten phishing ({{lynceus_phishing_native_llm_vs_null_a_signed}} points). The synonym swap lowered detection slightly. Converting HTML emails to plain text changed Lynceus's native detection by {{lynceus_phishing_native_null_a_vs_orig_signed}} points.

Under this protocol, faithful one-pass paraphrasing does not weaken these layers; the message format matters more than the wording. The result does not cover adaptive attackers, larger models or commercial filters.

## 1. Introduction

Large language models (LLMs) can rewrite an email in seconds while keeping its meaning. For phishing this raises a practical question: do the static filters that still guard many mailboxes rely on wording that a paraphrase removes? Earlier studies report that LLM rewriting lowers detection by SpamAssassin, commercial filters and machine-learning detectors [1]–[3].

We study the simplest version of this threat: an attacker who takes existing phishing emails and asks a local, open-weight model to rewrite each one once, with a neutral instruction and no feedback from any filter. We ask: **how much does detection by static email-security layers drop, and which layer accounts for the loss?** We also ask whether any drop is caused by the LLM rewrite itself rather than by re-encoding or by any change of words, and whether the rewrites stay valid (same intent, label and links).

Our contribution is a measurement with controls, not a new attack or a new detector. Ferrell et al. [1] measured machine-learning detectors on rephrased emails. Beyond that study, we:
- test static rule-based layers;
- require every rewrite to keep its links and numbers;
- separate the effect of the wording from that of the plain-text format.

[AUTHORS: confirm this against the full text of [1].]

## 2. Related work

Ferrell et al. [1] prompted three LLMs to rephrase phishing and safe emails. Rephrasing lowered the accuracy of existing detectors: by 3–4% for BERT-based models and by 8–20% for Word2Vec and stylometric ones. Retraining on rephrased emails restored accuracy.

Josten and Weis [2] modified spam with GPT-3.5 Turbo and report that SpamAssassin misclassified up to 73.7% of the modified spam as legitimate, against at most 0.4% for a dictionary-replacement attack. Afane et al. [3] report declines for Gmail, SpamAssassin, Proofpoint and classical classifiers on LLM-rephrased phishing.

We ask how much of such a drop remains when the rewrite must keep the links, numbers and request and the format is held fixed, and which layer it comes from. [AUTHORS: this summary is from the three abstracts; check it against the full papers.]

## 3. Method

The protocol was fixed before any rewritten email was scored (tag `protocol-freeze-v1`). Every change is listed in `DEVIATIONS.md`.

**Changes from our proposal.** Three changes were made to fit the time available:
- one generator instead of two or three;
- Lynceus, which includes URL rules, instead of a separate URL layer;
- an exact rule-and-token accounting instead of a list of detections that depend on content rules alone. Scoring and analysis ran in a container with networking disabled. Rewriting ran on the same machine against a local model server, so no email text left the machine.

### 3.1 Data

Phishing emails come from the Nazario phishing corpus (CC BY 4.0) [4], files collected from 2005 to 2022. To keep the phishing class human-written, we excluded messages dated on or after 30 November 2022, the public release of ChatGPT [5]. Legitimate emails come from the SpamAssassin public corpus (easy_ham, easy_ham_2, hard_ham) [6]. Raw files are pinned by SHA-256.

From {{phishing_read}} phishing and {{ham_read}} legitimate messages, we removed messages outside the study's text-only scope:
- {{phishing_non_text_part}} and {{ham_non_text_part}} with attachments or other non-text parts;
- {{phishing_not_english}} and {{ham_not_english}} not identified as English by langdetect [7];
- {{phishing_empty}} and {{ham_empty}} with an empty body;
- {{phishing_after_cutoff}} phishing messages after the cutoff and {{phishing_date_unknown}} with no usable date.

We removed personal data: email local parts, phone numbers, and recipients' names. We then dropped near-duplicates ({{phishing_near_duplicate}} and {{ham_near_duplicate}}): messages whose 5-word phrases overlap by 80% or more (Jaccard similarity). This left {{phishing_kept}} phishing and {{ham_kept}} legitimate messages.

Messages sharing at least half of their 5-word phrases were grouped into template clusters. Whole clusters were assigned at random (fixed seed) to train, dev, test and pilot, so no campaign template appears in two splits. The test split holds {{phishing_test}} phishing and {{ham_test}} legitimate messages.

### 3.2 Conditions

Every test message is scored in four conditions (a paired design). The headers never change; only the body does. A 4-billion-parameter model cannot rewrite HTML reliably, so it rewrites the body as plain text: the plain part, or the visible text of the HTML with each link written out as `<URL>`.

- **orig:** the message unchanged.
- **null-A:** the plain-text body, unchanged. It differs from orig only in format, so comparing the rewrite with null-A isolates the wording. orig versus null-A shows the effect of the format itself.
- **lex:** the null-A text with WordNet synonyms [8], read through NLTK [9], swapped in until {{lex_dose}} of the words have changed, the median change made by the model on the pilot. Links, addresses and placeholders are untouched. This tests whether *any* rewording of that size lowers detection.
- **llm:** one paraphrase of the null-A text by `gemma3:4b` [10], run locally through Ollama [11] with temperature 0 and a fixed seed. The prompt was: *"Rewrite the following email in your own words. Keep every link, name, number and the requested action unchanged. Output only the rewritten email text."* It never mentions filters or detection, and the model received no feedback. Refusals were counted, not worked around.

We rewrote test messages in a fixed random order until 200 rewrites per class passed the comparability gates (3.3). The stopping rule looked only at the gates, never at any detector.

### 3.3 Comparability of rewrites

A rewrite enters the analysis only if, compared with its null-A text:
- it keeps the same set of links, numbers, addresses and placeholders, ignoring formatting such as "2,500" versus "2500";
- its length is between half and twice the original;
- it is still English;
- it adds no refusal or comment of its own.

These gates were fixed on a 53-message pilot ({{pilot_passed}} of 53 passed) before the main run. Messages that failed are counted and compared with those that passed.

For 30 rewrite pairs (15 per class), a second local model (llama3.2:3b [12], a different family from the generator) judged whether the rewrite keeps the requested action, the target and entities, the urgency, and the label. A human then read every pair and corrected any judgment they disagreed with: {{judge_checks}} We report the share of pairs judged equivalent on all four questions ({{judge_equivalent_rate}}). This is a check of the gates by a model and a human reader, not an independent two-rater audit.

### 3.4 Detectors

All three layers are static: fixed rules or a fixed model, with no learning from the messages they score. Each returns a score, a flag and the evidence behind it.

- **L1:** {{spamassassin_version}} [13], with its shipped rules, local tests only, and Bayes and auto-learning off.
- **L2, TF-IDF with logistic regression** [14]: trained only on the train split ({{phishing_train}} phishing, {{ham_train}} legitimate), with its regularisation chosen on dev (C = {{l2_C}}, dev AUC {{l2_dev_auc}}), then frozen. It reads the subject and visible body text.
- **L4, Lynceus:** the first author's own rule-based phishing detector ({{lynceus_version}}), frozen before any rewrite was scored. We use its message engine unchanged, except that its Windows-only sandbox launcher is replaced by a subprocess inside our offline container. Its score is the risk Lynceus computes from the rules that fired, including below its own warning line. Because we evaluate our own tool, its results are reported under the same controls as the other layers. The first author designed and directed Lynceus before this study; Claude Code wrote its code and rules under that direction (`LYNCEUS_NOTES.md`). Its signal comes mostly from links, sender and HTML structure, plus one rule on urgent and credential-requesting phrases.

Each layer has two operating points: its native one, and a threshold fixed on dev originals so that at most 1% of legitimate dev emails are flagged (SpamAssassin {{spamassassin_threshold}}, TF-IDF {{tfidf_lr_threshold}}, Lynceus {{lynceus_threshold}}). Neither was changed after rewritten emails were scored.

### 3.5 Analysis

Every message is compared with itself in two conditions. The **primary contrast is llm versus null-A**. We also report lex versus null-A, llm versus lex, and null-A versus orig.

For each layer, class and operating point, we report:
- the detections lost and gained;
- the net change in percentage points, with a 95% bootstrap confidence interval [15] (10,000 resamples of whole template clusters, fixed seed);
- an exact McNemar test [16];
- the mean change in score, with its interval.

The confirmatory test is phishing, at the calibrated threshold, llm versus null-A: one test per layer, Holm-adjusted [17]. Everything else is descriptive.

An interval that excludes zero is read as a change. One inside ±2 points is read as "no change larger than 2 points". Anything else is inconclusive. A message with a scoring error on either side is excluded from that layer's contrast and counted. Every result is repeated on all rewrites, not only those passing the gates.

We then separate *what moved* from *why*. SpamAssassin's score is a sum of rule points, the classifier's logit is a sum of token contributions, and Lynceus lists the rules that fired, so we can show which rules and words account for a change. A cause is claimed only for a rule-based edit of one property: the plain-text copy, which changes only the format. Everything else is "consistent with".

## 4. Results

### 4.1 Rewrites

We rewrote {{rewritten_total}} test emails. Another {{gates_phishing_not_rewritten_too_long}} phishing and {{gates_ham_not_rewritten_too_long}} legitimate emails were too long to rewrite; they are counted, not analysed. Every gate was passed by {{gates_phishing_passed}} of {{gates_phishing_rewritten}} phishing rewrites and {{gates_ham_passed}} of {{gates_ham_rewritten}} legitimate ones (Table 2). The model refused in {{refusals}} case. Most failures were rewrites that dropped links or numbers.

In the 30-pair meaning check, the accepted judgments say the rewrite kept:
- the requested action in {{judge_yes_same_action}} of pairs;
- the target, links and names in {{judge_yes_same_target}};
- the urgency in {{judge_yes_same_urgency}};
- the category (phishing or legitimate) in only {{judge_yes_same_label}}.

Only {{judge_equivalent_rate}} were equivalent on all four. {{judge_checks}}

Kept rewrites came from shorter emails than discarded ones. For phishing, the medians were {{sel_phishing_kept_words}} against {{sel_phishing_discarded_words}} words, and {{sel_phishing_kept_urls}} against {{sel_phishing_discarded_urls}} links. The analysed pairs therefore over-represent short emails.

### 4.2 The LLM wording

Table 1 gives the share flagged in each condition. Against the plain-text copy, the rewrite changed phishing detection by:
- {{spamassassin_phishing_calibrated_llm_vs_null_a_signed}} points for SpamAssassin {{spamassassin_phishing_calibrated_llm_vs_null_a_ci}};
- {{tfidf_lr_phishing_calibrated_llm_vs_null_a_signed}} for TF-IDF {{tfidf_lr_phishing_calibrated_llm_vs_null_a_ci}};
- {{lynceus_phishing_calibrated_llm_vs_null_a_signed}} for Lynceus {{lynceus_phishing_calibrated_llm_vs_null_a_ci}}.

The Holm-adjusted p-values were {{spamassassin_phishing_calibrated_llm_vs_null_a_holm_p}}, {{tfidf_lr_phishing_calibrated_llm_vs_null_a_holm_p}} and {{lynceus_phishing_calibrated_llm_vs_null_a_holm_p}}. For SpamAssassin and TF-IDF, the intervals exclude a change larger than two points in either direction.

At its calibrated threshold, Lynceus flagged only {{lynceus_phishing_calibrated_llm_vs_null_a_a_pct}} of plain-text phishing to begin with: a floor effect. At its native threshold, it flagged more phishing after rewriting: {{lynceus_phishing_native_llm_vs_null_a_a_pct}} rose to {{lynceus_phishing_native_llm_vs_null_a_b_pct}} ({{lynceus_phishing_native_llm_vs_null_a_signed}} points, {{lynceus_phishing_native_llm_vs_null_a_ci}}).

On legitimate mail, no layer's false positives rose beyond the margin. The one inconclusive case was TF-IDF: {{tfidf_lr_ham_calibrated_llm_vs_null_a_signed}} points {{tfidf_lr_ham_calibrated_llm_vs_null_a_ci}}.

Adding the rewrites that failed the gates did not change the picture. For example, SpamAssassin changed by {{all_spamassassin_phishing_calibrated_llm_vs_null_a_signed}} points {{all_spamassassin_phishing_calibrated_llm_vs_null_a_ci}} on all {{all_spamassassin_phishing_calibrated_llm_vs_null_a_n}} phishing rewrites.

### 4.3 Rewording without an LLM, and the format

The synonym swap lowered phishing detection slightly, at native thresholds:
- {{spamassassin_phishing_native_lex_vs_null_a_signed}} points for SpamAssassin {{spamassassin_phishing_native_lex_vs_null_a_ci}};
- {{tfidf_lr_phishing_native_lex_vs_null_a_signed}} for TF-IDF {{tfidf_lr_phishing_native_lex_vs_null_a_ci}};
- {{lynceus_phishing_native_lex_vs_null_a_signed}} for Lynceus {{lynceus_phishing_native_lex_vs_null_a_ci}}.

The LLM rewrite was flagged more often than the synonym swap by SpamAssassin ({{spamassassin_phishing_native_llm_vs_lex_signed}} points, {{spamassassin_phishing_native_llm_vs_lex_ci}}) and by Lynceus ({{lynceus_phishing_native_llm_vs_lex_signed}}, {{lynceus_phishing_native_llm_vs_lex_ci}}).

The largest change came from the format alone. Turning the original into its plain-text copy:
- lowered Lynceus's native detection from {{lynceus_phishing_native_null_a_vs_orig_a_pct}} to {{lynceus_phishing_native_null_a_vs_orig_b_pct}} ({{lynceus_phishing_native_null_a_vs_orig_signed}} points, {{lynceus_phishing_native_null_a_vs_orig_ci}});
- changed SpamAssassin's by {{spamassassin_phishing_native_null_a_vs_orig_signed}} points {{spamassassin_phishing_native_null_a_vs_orig_ci}};
- did not change TF-IDF, which reads only the visible text.

### 4.4 What moved

Under the LLM rewrite, the accounting shows only small changes for SpamAssassin (a few rules for misspelled brand names stopped firing) and TF-IDF (slight shifts on common words). Lynceus's social-engineering phrase rule started to fire in {{lynceus_social_starts}} of rewritten phishing emails. That is consistent with the model adding urgent, credential-requesting wording, a cause we did not test. The format effect, by contrast, is causal by design.

**Table 1.** Share of messages flagged (%) at the dev-calibrated threshold, gate-passed pairs, per condition; the primary contrast (llm vs null-A) with its 95% cluster-bootstrap CI. The Holm p is given for the confirmatory family only.

{{table_main}}

**Table 2.** Rewrites per class, gate passes, and failures per gate. A rewrite can fail several gates.

{{table_gates}}

## 5. Discussion and limitations

Under this protocol, a faithful single-pass paraphrase by a small local model did not make phishing harder to detect for any of the three static layers. For Lynceus, it made phishing slightly easier to detect. This is a negative result for the feared effect, with a simple reading. These layers draw their signal from links, headers, HTML structure and generic phishing vocabulary. A rewrite that must keep the links, numbers and request keeps most of that signal. A synonym swap removed some vocabulary and cost a few points; removing the HTML structure cost much more.

This differs from the drops reported in [1]–[3]. Our setting differs in ways that may explain the gap; we tested none of them:
- our SpamAssassin ran without its Bayesian component, which is central to [2];
- we used a 4-billion-parameter local model, not GPT-3.5 Turbo;
- we rewrote phishing rather than spam;
- every analysed rewrite had to keep its links and numbers.

What we add beyond [1] is a paired, per-layer test for static rule-based layers that separates wording from format.

Alternative explanations remain:
- **comparability is not established for the category of the message.** The meaning check judged only {{judge_yes_same_label}} of pairs to keep their category, which would mean many rewrites no longer read as their original. The detectors, however, scored the rewrites much like the originals. With one small judge model and 30 pairs, we cannot tell whether the rewrites or the judge are at fault [AUTHORS: revisit if the check is revised];
- the analysed rewrites are those faithful enough to pass the gates, which favours short emails;
- one small model with a neutral prompt is not an adaptive attacker;
- the TF-IDF classifier sits near its ceiling, and Lynceus near its floor at the calibrated threshold, which limits what those contrasts can show.

The study also has deliberate limits:
- The attacker is non-adaptive and makes one pass, which underestimates a determined attacker.
- The corpora are old (legitimate mail from 2002 to 2003, phishing from 2005 to 2022), so "human versus LLM" style is mixed with era; pairing controls content, not era.
- We use one small open-weight model, not frontier models.
- SpamAssassin run offline is not a commercial filter; we test static layers only, without sender reputation, DNS or authentication checks.
- Text-only, English-only messages.
- We evaluate our own tool.
- The meaning check covers only 30 pairs, judged by a small local model and checked by one author who saw the model's answers first.
- Rewrites run on plain text, so the HTML structure of the original is not kept; null-A carries the same format, so the comparison is fair, but it is not the attacker's full message.

## Declarations

**Declaration of Generative AI and AI-Assisted Technologies.** [AUTHORS: confirm against AI_LOG.md; the handbook (p. 13) requires tools, uses and verification.] We used Claude Code (Anthropic; Claude Opus 5.5 and Claude Sonnet 5.5) to write the study code, tests and documentation and to draft this manuscript under our direction. Claude Code also wrote the code of Lynceus, under the first author's direction. Within the experiment, two local models ran on our own machine: gemma3:4b (Google) produced the rewrites under study, and llama3.2:3b (Meta) pre-filled the 30-pair meaning check. Claude Code never saw email text. We tested the code, re-ran the analyses, checked every number against the result files, opened and verified every source, and checked the meaning judgments ourselves.

**Ethics and model licence.** We only rewrote existing phishing emails from a public corpus, offline. Nothing was sent, and the rewrites are not published. The generator's use policy (Gemma Prohibited Use Policy) bars generating content for phishing, and makes no research exception. We used it for defensive evaluation only, and we declare that choice here [18]. [AUTHORS: confirm wording.]

**Data and code.** Code, configurations, manifests, hashes and aggregate results: https://github.com/sodik-tursunboev/llm-phishing-study [AUTHORS: make it reviewer-accessible before submitting]. Raw corpora are not redistributed; they are re-downloaded and verified by hash. Raw rewrites are available to reviewers on request.

**Contributions.** Sodik Tursunboev designed and ran the study, and authored Lynceus before the study began (AI-assisted; see `LYNCEUS_NOTES.md`). Kavish Chaudhari is the project partner, who checked the meaning judgments of the 30 rewrite pairs and verified every reference and every number against the result files. [AUTHORS: confirm once done.] Kavish did not write Lynceus. {{judge_checks}} Details in `CONTRIBUTIONS.md`.

**Conflict of interest.** Lynceus is the first author's own tool.

## References

<!-- IEEE style. Every entry below was opened on its official page on 2026-11-11/12 and is listed in references/evidence_trail.csv; Kavish verifies each one before submission. -->

[1] A. Ferrell, J. Xu, H. Moradi, R. E. Davis, and K. Roy, "Evaluating the effectiveness of existing phishing detectors on AI generated phishing emails," in *Proc. 2025 Cyber Awareness and Research Symposium (CARS)*, Grand Forks, ND, USA, Oct. 2025, doi: 10.1109/CARS67163.2025.11337548.

[2] M. Josten and T. Weis, "Investigating the effectiveness of Bayesian spam filters in detecting LLM-modified spam mails," arXiv:2408.14293, Aug. 2024. [Online]. Available: https://arxiv.org/abs/2408.14293

[3] K. Afane, W. Wei, Y. Mao, J. Farooq, and J. Chen, "Next-generation phishing: How LLM agents empower cyber attackers," arXiv:2411.13874, Nov. 2024. [Online]. Available: https://arxiv.org/abs/2411.13874

[4] J. Nazario, "Phishing corpus." [Online]. Available: https://monkey.org/~jose/phishing/ (accessed Nov. 11, 2026).

[5] OpenAI, "Introducing ChatGPT," Nov. 30, 2022. [Online]. Available: https://openai.com/index/chatgpt/ (accessed Nov. 11, 2026).

[6] Apache SpamAssassin Project, "SpamAssassin public mail corpus." [Online]. Available: https://spamassassin.apache.org/old/publiccorpus/ (accessed Nov. 11, 2026).

[7] M. M. Danilák, "langdetect 1.0.9," Python Package Index, May 2021. [Online]. Available: https://pypi.org/project/langdetect/1.0.9/

[8] G. A. Miller, "WordNet: A lexical database for English," *Commun. ACM*, vol. 38, no. 11, pp. 39–41, Nov. 1995, doi: 10.1145/219717.219748.

[9] NLTK Project, "NLTK: Natural Language Toolkit." [Online]. Available: https://www.nltk.org/ (accessed Nov. 12, 2026).

[10] Gemma Team, "Gemma 3 technical report," arXiv:2503.19786, Mar. 2025. [Online]. Available: https://arxiv.org/abs/2503.19786

[11] Ollama, "Ollama," GitHub repository. [Online]. Available: https://github.com/ollama/ollama (accessed Nov. 12, 2026).

[12] Meta AI, "Llama 3.2: Revolutionizing edge AI and vision with open, customizable models," Sep. 25, 2024. [Online]. Available: https://ai.meta.com/blog/llama-3-2-connect-2024-vision-edge-mobile-devices/

[13] Apache SpamAssassin Project, "Apache SpamAssassin." [Online]. Available: https://spamassassin.apache.org/ (accessed Nov. 12, 2026).

[14] F. Pedregosa *et al.*, "Scikit-learn: Machine learning in Python," *J. Mach. Learn. Res.*, vol. 12, no. 85, pp. 2825–2830, 2011. [Online]. Available: https://jmlr.org/papers/v12/pedregosa11a.html

[15] B. Efron, "Bootstrap methods: Another look at the jackknife," *Ann. Statist.*, vol. 7, no. 1, pp. 1–26, 1979, doi: 10.1214/aos/1176344552.

[16] Q. McNemar, "Note on the sampling error of the difference between correlated proportions or percentages," *Psychometrika*, vol. 12, no. 2, pp. 153–157, 1947, doi: 10.1007/BF02295996.

[17] S. Holm, "A simple sequentially rejective multiple test procedure," *Scand. J. Statist.*, vol. 6, no. 2, pp. 65–70, 1979. [Online]. Available: https://www.jstor.org/stable/4615733

[18] Google, "Gemma prohibited use policy," last modified Feb. 21, 2024. [Online]. Available: https://ai.google.dev/gemma/prohibited_use_policy (accessed Nov. 11, 2026).
