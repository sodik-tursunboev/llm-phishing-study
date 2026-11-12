<!--
Manuscript source. Every number is a {{placeholder}} filled from result and config files by
`python -m src.paper.build`; never type a number here. Student IDs come from the git-ignored
paper/authors.local.json. Before submitting, the authors must make every statement in the
Declarations true: Kavish verifies each reference and number; both authors read the full texts of
[1]-[3], revise the text in their own words, and can explain every sentence.
Structure follows the course's Research Paper Template and Academic Research & Writing guide
(title of at most 12 words, one-paragraph abstract, keywords, numbered objectives, conclusion),
with IEEE references, the style the guide maps to computer science. Limit: 3,000 words from the
title to the conclusion, tables included; declarations and references are back matter.
-->

# Does a Small Language Model's Paraphrase Help Phishing Evade Static Email Filters?

*Official topic: The Evasion Capabilities of LLM-Generated Phishing Payloads Against Static Security Architectures*

{{student_ids}} · Vistula University · Architecture of Computers 2026/27

## Abstract

Recent studies report that phishing emails rewritten by large language models (LLMs) evade existing filters. We asked whether one paraphrase by a small local model, with no feedback from any filter, lowers detection by static email defences, and which defence loses it. We tested three static layers: SpamAssassin, a term frequency–inverse document frequency (TF-IDF) classifier with logistic regression, and Lynceus, a rule-based detector built by the first author. Each of {{gates_phishing_passed}} phishing and {{gates_ham_passed}} legitimate emails from public corpora was scored in four versions: as received, as a canonical plain-text version, after a dictionary synonym swap, and after a gemma3:4b rewrite that had to keep every link, number and name. Compared with the plain-text version, the rewrite did not lower phishing detection at thresholds calibrated to flag at most 1% of legitimate mail: SpamAssassin changed by {{spamassassin_phishing_calibrated_llm_vs_null_a_signed}} percentage points (95% confidence interval {{spamassassin_phishing_calibrated_llm_vs_null_a_ci}}), TF-IDF by {{tfidf_lr_phishing_calibrated_llm_vs_null_a_signed}} ({{tfidf_lr_phishing_calibrated_llm_vs_null_a_ci}}) and Lynceus by {{lynceus_phishing_calibrated_llm_vs_null_a_signed}} ({{lynceus_phishing_calibrated_llm_vs_null_a_ci}}). At its default threshold, Lynceus caught more rewritten phishing ({{lynceus_phishing_native_llm_vs_null_a_signed}} points). The synonym swap lowered default-threshold detection for all three layers. Converting the emails to plain text, which strips their HTML and drops links outside anchors, lowered Lynceus's detection from {{lynceus_phishing_native_null_a_vs_orig_a_pct}} to {{lynceus_phishing_native_null_a_vs_orig_b_pct}}. Under this protocol, the wording of a constraint-preserving rewrite did not weaken these filters; how the message was represented mattered far more. Adaptive attackers, larger models and commercial filters remain outside our scope.

**Keywords:** phishing detection; large language models; paraphrasing; email security; SpamAssassin; paired evaluation

## 1. Introduction

Large language models (LLMs) can turn a scam email into fluent text from a one-line instruction. Earlier studies report that such rewriting lowers detection by SpamAssassin, commercial filters and machine-learning detectors [1]–[3]. If wording alone defeats static filters, they lose much of their value. Yet rewriting can also change the message's representation, lose a link or alter the request, and it remains unclear how much of the reported loss comes from the wording itself (Section 2).

We study the simplest version of the threat: an attacker asks a local, open-weight model to rewrite each existing phishing email once, with a neutral instruction and no feedback from any filter. Our research question is: **how much does detection by static email-security layers drop, and which layer accounts for the loss?** Our objectives are to:

1. measure the paired change in detection for three static layers;
2. separate the LLM's wording from rewording in general and from conversion to plain text;
3. check that each rewrite keeps the links, numbers and meaning of its original.

This is original research: a controlled measurement, not a new attack or detector. Unlike Ferrell et al. [1], who measured machine-learning detectors, we test static, rule-based layers, require every rewrite to keep its links and numbers, and separate the wording from the conversion to plain text. Sections 2 to 6 cover related work, method, results, discussion and conclusions.

## 2. Related work

Three recent studies found that LLM rewriting lowers detection. Ferrell et al. [1] had three LLMs rephrase phishing and safe emails: detector accuracy fell by 3–4% for BERT-based models and by 8–20% for Word2Vec and stylometric models, and retraining on rephrased emails improved it. Josten and Weis [2] rewrote spam with GPT-3.5 Turbo; SpamAssassin let up to 73.7% of it through as legitimate, while a simple dictionary-replacement attack succeeded at most 0.4% of the time. Afane et al. [3] report declines for Gmail, SpamAssassin, Proofpoint and classical classifiers.

The effect therefore reaches learned detectors, a Bayesian spam filter and commercial services. These studies leave open how much of the drop survives when the rewrite must keep its links, numbers and request and the representation is held fixed, and which part of a filtering pipeline is responsible.

## 3. Method

We fixed the protocol before any rewritten email was scored (git tag `protocol-freeze-v1`) and logged every later change, including three changes from our proposal, in `DEVIATIONS.md`. Scoring and analysis ran in a Docker container with networking switched off, and a local model server produced the rewrites, so no email text left our computer.

### 3.1 Data

Phishing emails come from the Nazario phishing corpus [4] (CC BY 4.0, 2005–2022). To keep this class human-written, we dropped messages dated on or after 30 November 2022, when ChatGPT was released [5]. Legitimate emails come from the SpamAssassin public corpus [6] (easy_ham, easy_ham_2, hard_ham). Every raw file is pinned by its SHA-256 hash.

Of {{phishing_read}} phishing and {{ham_read}} legitimate messages, we kept only English text emails, removing (phishing / legitimate):

- {{phishing_non_text_part}} / {{ham_non_text_part}} with attachments or other non-text parts;
- {{phishing_not_english}} / {{ham_not_english}} not identified as English by langdetect [7];
- {{phishing_empty}} / {{ham_empty}} with an empty body;
- {{phishing_after_cutoff}} phishing sent after the cutoff, and {{phishing_date_unknown}} with no usable date.

We then removed personal data (address local parts, phone numbers, recipients' names) and near-duplicates sharing at least 80% of their five-word phrases ({{phishing_near_duplicate}} / {{ham_near_duplicate}}), leaving {{phishing_kept}} phishing and {{ham_kept}} legitimate emails. Because phishing campaigns reuse templates, we clustered messages sharing at least half of their five-word phrases and assigned whole clusters at random to the training, development, test and pilot splits, so no template appears in two splits. The test split holds {{phishing_test}} phishing and {{ham_test}} legitimate emails.

### 3.2 Four versions of every email

We scored every test email in four versions, so each message is compared only with itself. The headers never change; only the body does. A model with four billion parameters cannot rewrite HTML reliably, so all rewriting starts from the canonical plain-text version, null-A.

- **orig** is the email as received.
- **null-A** is a controlled canonicalization of orig by a fixed rule, with no model involved. The body becomes one UTF-8 text/plain part: the email's own plain part if it has one, with any HTML alternative dropped, or otherwise the visible text of the HTML, with each link's address written after its anchor text as `<URL>`. Tags, styles and scripts disappear, and so does any link outside an anchor, for example in an image. Comparing llm with null-A isolates the wording; comparing null-A with orig measures the canonicalization as a whole.
- **lex** is null-A after a synonym swap with WordNet [8] through NLTK [9], until {{lex_dose}} of words had changed (the model's median change on the pilot), never touching links, addresses or placeholders. It tests whether *any* rewording of that size lowers detection.
- **llm** is one paraphrase of null-A by gemma3:4b [10], run locally through Ollama [11] at temperature 0 with a fixed seed, using the prompt *"Rewrite the following email in your own words. Keep every link, name, number and the requested action unchanged. Output only the rewritten email text."* The prompt never mentions filters, the model received no feedback, and refusals were counted, not worked around.

We rewrote test emails in a fixed random order until 200 per class had passed the gates below; the stopping rule never looked at any detector.

### 3.3 Is the rewrite still the same email?

A rewrite entered the analysis only if, compared with its null-A text, it:

- kept the same set of links, numbers, addresses and placeholders, ignoring formatting such as "2,500" against "2500";
- stayed between half and twice the original length;
- was still in English;
- added no refusal or comment of its own.

We fixed these gates on a 53-message pilot ({{pilot_passed}} passed) and compare the emails that failed them with those that passed. Gates check facts, not meaning. For meaning, llama3.2:3b [12], a local model from a different family than the generator, judged 30 pairs (15 per class): does the rewrite keep the requested action, the target and entities, the urgency, and the category (phishing or legitimate)? A human then read every pair and corrected any answer they disagreed with.

### 3.4 Detectors

All three layers are static: fixed rules, or a frozen model that does not learn from the emails it scores.

- **SpamAssassin** {{spamassassin_version_number}} [13], with its shipped rules, local tests only, and Bayesian learning switched off.
- **A TF-IDF classifier with logistic regression** [14], trained on the training split ({{phishing_train}} phishing, {{ham_train}} legitimate), with its one setting chosen on the development split (C = {{l2_C}}, area under the receiver operating characteristic curve {{l2_dev_auc}}) and then frozen. It reads the subject and the visible body text.
- **Lynceus** (commit {{lynceus_commit}}), a rule-based phishing detector that the first author developed, with AI assistance for the code, before this study. We use its message engine unchanged, except for its Windows sandbox launcher, which we replaced so that it runs offline in our container, and we froze it before any rewrite was scored. Its signal comes mostly from links, the sender and HTML structure, plus one rule for urgent, credential-requesting phrases. As our own tool, it went through exactly the same controls as the other layers.

Each layer ran at two operating points: its default, and a threshold fixed on the development split to flag at most 1% of legitimate emails (SpamAssassin {{spamassassin_threshold}}, TF-IDF {{tfidf_lr_threshold}}, Lynceus {{lynceus_threshold}}). Neither changed after rewritten emails were scored.

### 3.5 Analysis

The main comparison is llm against null-A, which differ only in wording. We also compare lex with null-A, llm with lex, and null-A with orig. For each layer, class and operating point, we report:

- the detections lost and gained;
- the net change in percentage points (pp), with a 95% confidence interval (CI) from a bootstrap [15] that resamples whole template clusters (10,000 resamples, fixed seed);
- an exact McNemar test [16].

The confirmatory test is phishing at the calibrated threshold, llm against null-A: one test per layer, with a Holm correction [17]. Everything else is descriptive. We read an interval that excludes zero as a change, an interval inside ±2 points as "no change larger than 2 points", and anything else as inconclusive. Every result is repeated on all rewrites, including those that failed the gates.

We keep an observed difference apart from its cause. Each score can be taken apart, into SpamAssassin's rule points, the classifier's word contributions and the Lynceus rules that fired, so we can show exactly what moved. We claim a cause only where a rule-based edit with no model involved changed the message. null-A is such an edit, but it changes several things at once, so its effect is causal for the canonicalization as a whole, not for any one of its parts. Everything else we describe as "consistent with".

## 4. Results

Table 1 gives the share of emails each layer flagged in each version; Table 2 gives the outcome of the gates.

**Table 1.** Emails flagged (%) at the calibrated threshold, gate-passed pairs, with the main comparison (llm against null-A), its 95% cluster-bootstrap CI and the Holm-adjusted *p* of the confirmatory tests.

{{table_main}}

### 4.1 The rewrites

We rewrote {{rewritten_total}} test emails; another {{gates_phishing_not_rewritten_too_long}} phishing and {{gates_ham_not_rewritten_too_long}} legitimate emails were too long to rewrite and were counted but not analysed. Of the rewrites, {{gates_phishing_passed}} of {{gates_phishing_rewritten}} phishing and {{gates_ham_passed}} of {{gates_ham_rewritten}} legitimate ones passed every gate (Table 2). The model refused in {{refusals}} case, and most failures dropped a link or a number. The emails that passed were shorter: for phishing, a median of {{sel_phishing_kept_words}} against {{sel_phishing_discarded_words}} words, and {{sel_phishing_kept_urls}} against {{sel_phishing_discarded_urls}} links.

**Table 2.** Rewrites per class, how many passed every gate, and how many failed each gate (a rewrite can fail several).

{{table_gates}}

In the meaning check, the accepted judgments say the rewrite kept the requested action in {{judge_yes_same_action}} of pairs, the target, links and names in {{judge_yes_same_target}}, the urgency in {{judge_yes_same_urgency}}, and the category in only {{judge_yes_same_label}}; {{judge_equivalent_rate}} were equivalent on all four. {{judge_checks}}

### 4.2 The wording of the rewrite

Against null-A, the rewrite changed phishing detection at the calibrated thresholds by:

- {{spamassassin_phishing_calibrated_llm_vs_null_a_signed}} points for SpamAssassin ({{spamassassin_phishing_calibrated_llm_vs_null_a_ci}});
- {{tfidf_lr_phishing_calibrated_llm_vs_null_a_signed}} for TF-IDF ({{tfidf_lr_phishing_calibrated_llm_vs_null_a_ci}});
- {{lynceus_phishing_calibrated_llm_vs_null_a_signed}} for Lynceus ({{lynceus_phishing_calibrated_llm_vs_null_a_ci}}).

The Holm-adjusted *p*-values were {{spamassassin_phishing_calibrated_llm_vs_null_a_holm_p}}, {{tfidf_lr_phishing_calibrated_llm_vs_null_a_holm_p}} and {{lynceus_phishing_calibrated_llm_vs_null_a_holm_p}}. For SpamAssassin and TF-IDF, the intervals rule out a change larger than two points in either direction. At its calibrated threshold, Lynceus flagged only {{lynceus_phishing_calibrated_llm_vs_null_a_a_pct}} of null-A phishing, a floor effect. At its default threshold, it flagged *more* phishing after the rewrite: {{lynceus_phishing_native_llm_vs_null_a_b_pct}} against {{lynceus_phishing_native_llm_vs_null_a_a_pct}} ({{lynceus_phishing_native_llm_vs_null_a_signed}} points, {{lynceus_phishing_native_llm_vs_null_a_ci}}).

On legitimate mail, no layer's false positives rose beyond the margin; the one inconclusive case was TF-IDF ({{tfidf_lr_ham_calibrated_llm_vs_null_a_signed}} points, {{tfidf_lr_ham_calibrated_llm_vs_null_a_ci}}). Adding back the rewrites that failed the gates changes nothing: SpamAssassin, for example, moved by {{all_spamassassin_phishing_calibrated_llm_vs_null_a_signed}} points ({{all_spamassassin_phishing_calibrated_llm_vs_null_a_ci}}) across all {{all_spamassassin_phishing_calibrated_llm_vs_null_a_n}} phishing rewrites.

### 4.3 Rewording without an LLM, and canonicalization

The synonym swap lowered phishing detection at the default thresholds by:

- {{spamassassin_phishing_native_lex_vs_null_a_signed}} points for SpamAssassin ({{spamassassin_phishing_native_lex_vs_null_a_ci}});
- {{tfidf_lr_phishing_native_lex_vs_null_a_signed}} for TF-IDF ({{tfidf_lr_phishing_native_lex_vs_null_a_ci}});
- {{lynceus_phishing_native_lex_vs_null_a_signed}} for Lynceus ({{lynceus_phishing_native_lex_vs_null_a_ci}}).

The LLM rewrite was flagged *more* often than the synonym swap by SpamAssassin ({{spamassassin_phishing_native_llm_vs_lex_signed}} points, {{spamassassin_phishing_native_llm_vs_lex_ci}}) and by Lynceus ({{lynceus_phishing_native_llm_vs_lex_signed}}, {{lynceus_phishing_native_llm_vs_lex_ci}}).

The largest change in the study came from canonicalization alone. For the phishing pairs, it:

- turned the HTML of {{canon_phishing_pct_html_only_converted_to_text}} of emails into text;
- dropped the HTML alternative of another {{canon_phishing_pct_html_part_dropped_plain_part_kept}};
- removed at least one link from {{canon_phishing_pct_losing_at_least_one_url}}, almost always a link outside an anchor (median distinct links {{canon_phishing_median_distinct_urls_orig}} before, {{canon_phishing_median_distinct_urls_null_a}} after).

Legitimate mail, almost all plain text already, was barely affected. Canonicalization lowered Lynceus's default detection from {{lynceus_phishing_native_null_a_vs_orig_a_pct}} to {{lynceus_phishing_native_null_a_vs_orig_b_pct}} ({{lynceus_phishing_native_null_a_vs_orig_signed}} points, {{lynceus_phishing_native_null_a_vs_orig_ci}}) and changed SpamAssassin's by {{spamassassin_phishing_native_null_a_vs_orig_signed}} points ({{spamassassin_phishing_native_null_a_vs_orig_ci}}). TF-IDF did not move, although its input changed for {{canon_phishing_pct_tfidf_input_changed}} of phishing emails, where the `<URL>` strings now appear in the visible text.

### 4.4 Which rules and words moved

Under the LLM rewrite, the accounting shows only small changes for SpamAssassin, where a few rules for misspelled brand names stopped firing, and for TF-IDF, where common words shifted slightly. Lynceus's social-engineering phrase rule started to fire on {{lynceus_social_starts}} of rewritten phishing emails.

## 5. Discussion

### 5.1 Interpretation

The accounting suggests why the rewrite did not lower detection. These layers draw much of their signal from links, headers, HTML structure and familiar phishing vocabulary. A rewrite that must keep the links, numbers and request keeps most of that signal, and the new firings of Lynceus's phrase rule are consistent with fluent LLM prose adding urgent wording, a cause we did not test. The synonym swap removed some vocabulary signal; canonicalization removed far more, although we cannot say whether its lost HTML structure or its lost links matter more for Lynceus.

Our result differs from the large drops reported in [1]–[3], and the settings differ in ways that could explain it, none of which we tested:

- our SpamAssassin ran without the Bayesian component that is central to [2];
- we used a four-billion-parameter local model, not GPT-3.5 Turbo;
- we rewrote phishing rather than spam;
- every analysed rewrite had to keep its links and numbers.

The main open question is comparability. The meaning check judged only {{judge_yes_same_label}} of pairs to keep their category, which would mean many rewrites no longer read like their original. Yet the TF-IDF classifier, trained only on human-written emails, still flagged {{tfidf_lr_phishing_calibrated_llm_vs_null_a_b_pct}} of rewritten phishing and only {{tfidf_lr_ham_calibrated_llm_vs_null_a_b_pct}} of rewritten legitimate mail. With one small judge model and 30 pairs, we cannot tell which signal is right, so we report both.

### 5.2 Practical implications

For defenders, how a message reached the detector mattered more than its wording. Converting HTML email to plain text before a link- or structure-based detector, as null-A does, removes much of that detector's signal, so such layers should see the message as received. For researchers, a claim that LLM rewriting evades a filter is stronger when the rewrite keeps its links and request and the representation is held fixed; otherwise a loss caused by conversion or by lost links can be credited to the wording.

### 5.3 Limitations

- The emails that passed the gates are shorter than the rest, so the analysed pairs lean towards short emails.
- TF-IDF sits near its ceiling, and Lynceus near its floor at the calibrated threshold, which limits those two comparisons.
- The attacker is non-adaptive and makes one pass, which underestimates a determined attacker.
- The corpora are old (legitimate mail 2002–2003, phishing 2005–2022), so writing style is mixed with era; pairing controls content, not era.
- We used one small open-weight model rather than frontier models.
- Offline SpamAssassin is not a commercial filter, and we tested only static layers, without sender reputation, DNS or authentication checks.
- All emails were text-only and in English.
- The wording comparison uses canonicalized emails, which have already lost their HTML and some links. It describes rewriting a plain-text message, not an attacker's full HTML email.

## 6. Conclusion

We asked whether one paraphrase by a small local LLM lowers detection by static email filters. For rewrites that kept their links, numbers and names, it did not: at the calibrated thresholds, phishing detection changed by {{spamassassin_phishing_calibrated_llm_vs_null_a_signed}}, {{tfidf_lr_phishing_calibrated_llm_vs_null_a_signed}} and {{lynceus_phishing_calibrated_llm_vs_null_a_signed}} points for SpamAssassin, TF-IDF and Lynceus, with no significant change after Holm correction. The largest effect came instead from converting emails to plain text, which cost Lynceus {{lynceus_phishing_native_null_a_vs_orig_signed}} points at its default threshold. For these layers, a message's links and structure matter more than its wording. Future work should test adaptive attackers that receive feedback from a filter, larger models, rewrites that keep the original HTML, and a larger meaning check rated by several people.

## Declarations

**Declaration of Generative AI and AI-Assisted Technologies.** We used Claude Code (Anthropic) as a programming and writing assistant. It helped us write and test the data pipeline and analysis scripts, find and open sources, and draft and edit this text. Lynceus, the first author's detector, was also built with its help before this study. Two local models were part of the experiment itself: gemma3:4b produced the rewrites under study, and llama3.2:3b pre-filled the meaning-check sheet. We designed the study, took every methodological decision, ran the experiments on our own computer, checked the meaning judgments, verified every source and checked every reported number against the result files. Every use of AI is logged in `AI_LOG.md` in our repository.

**Ethics and model licence.** We rewrote only existing phishing emails from a public corpus, offline, after removing personal data. Nothing was sent, no email text left our computer, and the rewrites are not published. The generator's use policy [18] bars generating content for phishing and makes no research exception. We used it only for this defensive evaluation, and we declare that choice here.

**Data and code.** Code, configurations, hashes and aggregate results are at https://github.com/sodik-tursunboev/llm-phishing-study. Raw corpora are not redistributed: anyone can download them again and check them against our hashes. Raw rewrites are available to reviewers on request.

**Contributions.**

- Sodik Tursunboev and Kavish Chaudhari jointly proposed the research question.
- Sodik led the study: designing the protocol, choosing the data, the detectors and the generator, running the experiments, and writing. Sodik developed Lynceus before the study.
- Kavish checked the 30 meaning-check pairs, verified every reference, and checked the reported numbers against the result files.
- Both authors interpreted the results and revised the manuscript.

**Conflict of interest.** Lynceus is the first author's own tool. It went through the same controls as the other layers.

## References

<!-- IEEE style. Every entry below was opened on its official page on 2026-11-11/12 and is listed in references/evidence_trail.csv; Kavish verifies each one before submission. -->

[1] A. Ferrell, J. Xu, H. Moradi, R. E. Davis, and K. Roy, "Evaluating the effectiveness of existing phishing detectors on AI generated phishing emails," in *Proc. 2025 Cyber Awareness and Research Symposium (CARS)*, Grand Forks, ND, USA, Oct. 2025, doi: 10.1109/CARS67163.2025.11337548.

[2] M. Josten and T. Weis, "Investigating the effectiveness of Bayesian spam filters in detecting LLM-modified spam mails," arXiv:2408.14293, Aug. 2024. [Online]. Available: https://arxiv.org/abs/2408.14293

[3] K. Afane, W. Wei, Y. Mao, J. Farooq, and J. Chen, "Next-generation phishing: How LLM agents empower cyber attackers," arXiv:2411.13874, Nov. 2024. [Online]. Available: https://arxiv.org/abs/2411.13874

[4] J. Nazario, "Phishing corpus." [Online]. Available: https://monkey.org/~jose/phishing/ (accessed Nov. 11, 2026).

[5] OpenAI, "Introducing ChatGPT," Nov. 30, 2022. [Online]. Available: https://openai.com/index/chatgpt/ (accessed Nov. 11, 2026).

[6] Apache SpamAssassin Project, "SpamAssassin public mail corpus." [Online]. Available: https://spamassassin.apache.org/old/publiccorpus/ (accessed Nov. 11, 2026).

[7] M. M. Danilak, "langdetect 1.0.9," Python Package Index, May 2021. [Online]. Available: https://pypi.org/project/langdetect/1.0.9/

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

[18] Google, "Gemma prohibited use policy," last modified Feb. 21, 2024. [Online]. Available: https://gemma.ai/resources/prohibited-use/ (accessed Nov. 12, 2026).
