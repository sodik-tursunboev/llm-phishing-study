<!--
Manuscript source. Every number is a {{placeholder}} filled from result and config files by
`python -m src.paper.build`; never type a number here. Student IDs come from the git-ignored
paper/authors.local.json. Before submitting, the authors must make every statement in the
Declarations true: Kavish verifies each reference and number; both authors read the full texts of
[2]-[4], revise the text in their own words, and can explain every sentence.
Structure follows the course's Research Paper Template and Academic Research & Writing guide
(title of at most 12 words, one-paragraph abstract, keywords, numbered objectives, conclusion),
with IEEE references, the style the guide maps to computer science. Limit: 3,000 words from the
title to the conclusion, tables included; declarations and references are back matter.
-->

# Does a Small Language Model's Paraphrase Help Phishing Evade Static Email Filters?

*Official topic: The Evasion Capabilities of LLM-Generated Phishing Payloads Against Static Security Architectures*

{{student_ids}} · Vistula University · Architecture of Computers 2026/27

## Abstract

Studies report that phishing emails rewritten by large language models (LLMs) evade existing filters. We asked whether one paraphrase by a small local model, with no feedback from any filter, lowers detection by static email defences, and which defence loses it. We tested SpamAssassin, a term frequency–inverse document frequency (TF-IDF) classifier with logistic regression, and the static message engine of Lynceus, a phishing-defence system the first author built with an AI assistant. Each of {{gates_phishing_passed}} phishing and {{gates_ham_passed}} legitimate emails was scored in four versions: the original, a canonical plain-text version, a dictionary synonym swap, and a gemma3:4b rewrite that had to keep every link, number and name. Against the plain-text version, the rewrite did not lower phishing detection at thresholds calibrated to flag at most 1% of legitimate mail: SpamAssassin changed by {{spamassassin_phishing_calibrated_llm_vs_null_a_signed}} percentage points (95% confidence interval {{spamassassin_phishing_calibrated_llm_vs_null_a_ci}}) and TF-IDF by {{tfidf_lr_phishing_calibrated_llm_vs_null_a_signed}} ({{tfidf_lr_phishing_calibrated_llm_vs_null_a_ci}}), ruling out a drop larger than two points; Lynceus sat at its floor at that threshold. The synonym swap lowered default-threshold detection for all three layers. Converting emails to plain text, which strips their HTML and drops links outside anchors, lowered Lynceus's default detection from {{lynceus_phishing_native_null_a_vs_orig_a_pct}} to {{lynceus_phishing_native_null_a_vs_orig_b_pct}}. For these filters, how a message was represented mattered far more than the wording of a constraint-preserving rewrite.

**Keywords:** phishing detection; large language models; paraphrasing; email security; SpamAssassin; paired evaluation

## 1. Introduction

In 2025, phishing and spoofing was the crime type most often reported to the FBI's Internet Crime Complaint Center: 191,561 of 1,008,597 complaints [1, pp. 6–7]. The report also warns that chat generators can quickly create official-sounding emails containing phishing links [1, p. 39]. Studies report that rewriting by LLMs lowers detection by SpamAssassin, commercial filters and machine-learning detectors [2]–[4]. Yet rewriting can also change the message's representation, lose a link or alter the request, and it remains unclear how much of the reported loss comes from the wording itself.

We study the simplest version of the threat: an attacker asks a local, open-weight model to rewrite each existing phishing email once, with a neutral instruction and no feedback from any filter. Our research question is: **how much does detection by static email-security layers drop, and which layer accounts for the loss?** Our objectives are to:

1. measure the paired change in detection for three static layers;
2. separate the LLM's wording from rewording in general and from conversion to plain text;
3. check that each rewrite keeps the links, numbers and meaning of its original.

Ferrell et al. [2] measured machine-learning detectors; we test static layers, including rule-based ones, with a neutral prompt, require every rewrite to keep its links and numbers, and separate the wording from the conversion to plain text.

## 2. Related work

Ferrell et al. [2] had three LLMs rephrase phishing and safe emails: detector accuracy fell by 3–4% for BERT-based models and by 8–20% for Word2Vec and stylometric models, and retraining on rephrased emails improved it. Josten and Weis [3] asked GPT-3.5 Turbo to make spam less aggressive and replace spam-like words: SpamAssassin let 9.4% of it through as legitimate with the original headers and 73.7% with minimal headers, while a dictionary-replacement attack succeeded at most 0.4% of the time. Afane et al. [4] prompted GPT-4o to rewrite phishing so as to bypass detectors, and report lower recall for Gmail, SpamAssassin, Proofpoint and classical classifiers. These studies leave open how much of the drop survives with a neutral prompt, a rewrite that must keep its links, numbers and request, and the representation held fixed.

## 3. Method

We fixed the protocol before any rewritten email was scored (git tag `protocol-freeze-v1`) and logged every later change in `DEVIATIONS.md`. Scoring ran in a Docker container without networking, and a local model server produced the rewrites, so no email text left our computer.

### 3.1 Data

Phishing emails come from the Nazario corpus [5] (CC BY 4.0, 2005–2022), without messages dated on or after 30 November 2022, when ChatGPT was released [6], so that this class is human-written. Legitimate emails come from the SpamAssassin public corpus [7].

Of {{phishing_read}} phishing and {{ham_read}} legitimate messages, we kept only English text emails, removing (phishing / legitimate):

- {{phishing_non_text_part}} / {{ham_non_text_part}} with attachments or other non-text parts;
- {{phishing_not_english}} / {{ham_not_english}} not identified as English by langdetect [8];
- {{phishing_empty}} / {{ham_empty}} with an empty body;
- {{phishing_after_cutoff}} phishing sent after the cutoff, and {{phishing_date_unknown}} with no usable date.

We then removed personal data (address local parts, phone numbers, recipients' names) and near-duplicates sharing at least 80% of their five-word phrases ({{phishing_near_duplicate}} / {{ham_near_duplicate}}), leaving {{phishing_kept}} phishing and {{ham_kept}} legitimate emails. Because campaigns reuse templates, we clustered messages sharing at least half of their five-word phrases and assigned whole clusters at random to the training, development, test and pilot splits. The test split holds {{phishing_test}} phishing and {{ham_test}} legitimate emails; {{phishing_test_pct_html}} of the phishing and {{ham_test_pct_html}} of the legitimate ones contain HTML.

### 3.2 Four versions of every email

Each test email was scored in four versions, so it is compared only with itself. All four keep the same headers and pass through the same rendering code; only the body differs. A four-billion-parameter model cannot rewrite HTML reliably, so rewriting starts from the plain-text version, null-A.

- **orig** is the email after personal data was removed, with its own plain and HTML parts.
- **null-A** is a canonicalization of orig by a fixed rule. The body becomes one plain-text part: the email's plain part if it has one, or else the visible text of its HTML, with each link's address written after its anchor text as `<URL>`. Tags, scripts and links outside anchors, such as in images, disappear. Comparing llm with null-A isolates the wording; comparing null-A with orig measures the canonicalization as a whole.
- **lex** is null-A after a WordNet [9] synonym swap through NLTK [10], until {{lex_dose}} of words had changed (the model's median on the pilot), never touching links, addresses or placeholders. It tests whether *any* rewording of that size lowers detection.
- **llm** is one paraphrase of null-A by gemma3:4b [11], run locally through Ollama [12] at temperature 0 with a fixed seed, using the prompt *"Rewrite the following email in your own words. Keep every link, name, number and the requested action unchanged. Output only the rewritten email text."* The prompt never mentions filters, and the model received no feedback.

We rewrote test emails in a fixed random order until 200 per class had passed the gates below; this stopping rule never looked at any detector.

### 3.3 Is the rewrite still the same email?

A rewrite entered the analysis only if, compared with its null-A text, it kept the same set of links, numbers, addresses and placeholders (ignoring formatting such as "2,500" against "2500"), stayed between half and twice the length, was still in English, and added no refusal or comment of its own. We fixed these gates on a 53-message pilot ({{pilot_passed}} passed).

Gates check facts, not meaning. For meaning, llama3.2:3b [13], a local model from another family, judged 30 pairs (15 per class): does the rewrite keep the requested action, the target and entities, the urgency, and the category (phishing or legitimate)? The second author then read every pair, with the model's answers in view, and could correct any of them.

### 3.4 Detectors

All three layers are static: fixed rules, or a frozen model.

- **SpamAssassin** {{spamassassin_version_number}} [14], with its shipped rules, local tests only, and Bayesian learning off.
- **A TF-IDF classifier with logistic regression** [15], trained on the training split ({{phishing_train}} phishing, {{ham_train}} legitimate), with its one setting chosen on the development split (C = {{l2_C}}, area under the curve {{l2_dev_auc}}) and then frozen. It reads the subject and visible body text.
- **Lynceus** (commit {{lynceus_commit}}), a local phishing-defence system that the first author designed and built with an AI assistant before this study. Beyond its rules, it can open pages in a sandboxed browser, match threat-intelligence lists and consult a local AI reviewer; we used only its offline message engine, whose fixed rules and weights make it a static layer. We replaced only its Windows sandbox launcher and froze it before any rewrite was scored. Its message rules read mostly links, the sender and HTML structure, plus one phrase rule.

Each layer ran at its default threshold and at one fixed on the development split to flag at most 1% of legitimate emails (SpamAssassin {{spamassassin_threshold}}, TF-IDF {{tfidf_lr_threshold}}, Lynceus {{lynceus_threshold}}).

### 3.5 Analysis

The main comparison is llm against null-A; we also compare lex with null-A, llm with lex, and null-A with orig. For each layer, class and threshold, we report the detections lost and gained, the net change in percentage points (pp) with a 95% confidence interval (CI) from a bootstrap [16] that resamples whole template clusters, an exact McNemar test [17], and the mean paired change in the layer's score.

The confirmatory test is phishing at the calibrated threshold, llm against null-A, one per layer, with a Holm correction [18]; everything else is descriptive. An interval that excludes zero is a change, one inside ±2 points is "no change larger than 2 points", and anything else is inconclusive. When zero or one outcome changes, the bootstrap interval collapses towards zero, so after the freeze we added Newcombe's paired score interval [19] as a check. Every result is repeated on all rewrites, including those that failed the gates.

We keep an observed difference apart from its cause. SpamAssassin's rule points, the classifier's word contributions and the Lynceus rules that fired show what moved, but we claim a cause only where a rule-based edit changed the message: null-A, whose effect is causal for the canonicalization as a whole, since it changes several things at once. Everything else is "consistent with".

## 4. Results

**Table 1.** Emails flagged (%) at the calibrated threshold, gate-passed pairs, with the main comparison (llm against null-A), its 95% cluster-bootstrap CI and the Holm-adjusted *p* of the confirmatory tests. Intervals resting on zero or one changed outcome collapse towards zero.

{{table_main}}

### 4.1 The rewrites

We rewrote {{rewritten_total}} test emails; another {{gates_phishing_not_rewritten_too_long}} phishing and {{gates_ham_not_rewritten_too_long}} legitimate emails were too long to rewrite. Of the rewrites, {{gates_phishing_passed}} of {{gates_phishing_rewritten}} phishing and {{gates_ham_passed}} of {{gates_ham_rewritten}} legitimate ones passed every gate (Table 2). The model refused once; most failures dropped a link or a number. The phishing emails that passed were shorter: a median of {{sel_phishing_kept_words}} against {{sel_phishing_discarded_words}} words, and {{sel_phishing_kept_urls}} against {{sel_phishing_discarded_urls}} links.

**Table 2.** Rewrites per class, how many passed every gate, and how many failed each gate (a rewrite can fail several).

{{table_gates}}

In the meaning check, the accepted judgments say the rewrite kept the requested action in {{judge_yes_same_action}} of pairs, the target, links and names in {{judge_yes_same_target}}, the urgency in {{judge_yes_same_urgency}}, and the category in only {{judge_yes_same_label}}; {{judge_equivalent_rate}} were equivalent on all four. {{judge_checks}}

### 4.2 The wording of the rewrite

Against null-A, the rewrite changed phishing detection at the calibrated thresholds by {{spamassassin_phishing_calibrated_llm_vs_null_a_signed}} points for SpamAssassin ({{spamassassin_phishing_calibrated_llm_vs_null_a_ci}}), {{tfidf_lr_phishing_calibrated_llm_vs_null_a_signed}} for TF-IDF ({{tfidf_lr_phishing_calibrated_llm_vs_null_a_ci}}) and {{lynceus_phishing_calibrated_llm_vs_null_a_signed}} for Lynceus ({{lynceus_phishing_calibrated_llm_vs_null_a_ci}}); the Holm-adjusted *p*-values were {{spamassassin_phishing_calibrated_llm_vs_null_a_holm_p}}, {{tfidf_lr_phishing_calibrated_llm_vs_null_a_holm_p}} and {{lynceus_phishing_calibrated_llm_vs_null_a_holm_p}}. These intervals rest on one or two changed outcomes; the paired score intervals, {{spamassassin_phishing_calibrated_llm_vs_null_a_exact_ci}} for SpamAssassin and {{tfidf_lr_phishing_calibrated_llm_vs_null_a_exact_ci}} for TF-IDF, still rule out a drop larger than two points, but not a gain of that size. The scores barely moved: the mean paired shift was {{spamassassin_phishing_calibrated_llm_vs_null_a_shift}} SpamAssassin points ({{spamassassin_phishing_calibrated_llm_vs_null_a_shift_ci}}) and {{tfidf_lr_phishing_calibrated_llm_vs_null_a_shift}} in the TF-IDF logit ({{tfidf_lr_phishing_calibrated_llm_vs_null_a_shift_ci}}). Lynceus flagged only {{lynceus_phishing_calibrated_llm_vs_null_a_a_pct}} of null-A phishing at its calibrated threshold, a floor effect, so that test could not show a drop. At its default threshold, it flagged more gate-passed phishing after the rewrite ({{lynceus_phishing_native_llm_vs_null_a_signed}} points, {{lynceus_phishing_native_llm_vs_null_a_ci}}), but not across all rewrites ({{all_lynceus_phishing_native_llm_vs_null_a_signed}}, {{all_lynceus_phishing_native_llm_vs_null_a_ci}}): it lost detections among the rewrites that failed the gates, most of which had dropped a link.

On legitimate mail, no layer's false positives rose beyond the margin. The one inconclusive case was TF-IDF ({{tfidf_lr_ham_calibrated_llm_vs_null_a_signed}} points, {{tfidf_lr_ham_calibrated_llm_vs_null_a_ci}}), whose logit for rewritten legitimate mail moved {{tfidf_lr_ham_calibrated_llm_vs_null_a_shift}} ({{tfidf_lr_ham_calibrated_llm_vs_null_a_shift_ci}}) towards phishing. At the calibrated thresholds, adding back the failed rewrites leaves the SpamAssassin and TF-IDF readings unchanged.

### 4.3 Rewording without an LLM, and canonicalization

The synonym swap lowered phishing detection at the default thresholds by {{spamassassin_phishing_native_lex_vs_null_a_signed}} points for SpamAssassin ({{spamassassin_phishing_native_lex_vs_null_a_ci}}), {{tfidf_lr_phishing_native_lex_vs_null_a_signed}} for TF-IDF ({{tfidf_lr_phishing_native_lex_vs_null_a_ci}}) and {{lynceus_phishing_native_lex_vs_null_a_signed}} for Lynceus ({{lynceus_phishing_native_lex_vs_null_a_ci}}). SpamAssassin flagged the LLM rewrite more often than the swap ({{spamassassin_phishing_native_llm_vs_lex_signed}} points, {{spamassassin_phishing_native_llm_vs_lex_ci}}; {{all_spamassassin_phishing_native_llm_vs_lex_signed}} across all rewrites), and so did Lynceus for gate-passed rewrites only ({{lynceus_phishing_native_llm_vs_lex_signed}}, {{lynceus_phishing_native_llm_vs_lex_ci}}).

The largest change came from canonicalization. For the phishing pairs, it turned the HTML of {{canon_phishing_pct_html_only_converted_to_text}} of emails into text, dropped the HTML alternative of another {{canon_phishing_pct_html_part_dropped_plain_part_kept}}, and removed at least one link, almost always outside an anchor, from {{canon_phishing_pct_losing_at_least_one_url}}. It lowered Lynceus's default detection from {{lynceus_phishing_native_null_a_vs_orig_a_pct}} to {{lynceus_phishing_native_null_a_vs_orig_b_pct}} ({{lynceus_phishing_native_null_a_vs_orig_signed}} points, {{lynceus_phishing_native_null_a_vs_orig_ci}}) and changed SpamAssassin's by {{spamassassin_phishing_native_null_a_vs_orig_signed}} ({{spamassassin_phishing_native_null_a_vs_orig_ci}}); TF-IDF did not move. Legitimate mail, almost all plain text already, was barely affected.

End to end, sending the rewrite as plain text instead of the original email lowered default detection from {{lynceus_phishing_native_llm_vs_orig_a_pct}} to {{lynceus_phishing_native_llm_vs_orig_b_pct}} for Lynceus ({{lynceus_phishing_native_llm_vs_orig_signed}} points) and from {{spamassassin_phishing_native_llm_vs_orig_a_pct}} to {{spamassassin_phishing_native_llm_vs_orig_b_pct}} for SpamAssassin ({{spamassassin_phishing_native_llm_vs_orig_signed}}). Because the same emails appear in every version, this splits exactly into the two steps: all of the loss comes from canonicalization, none from the wording.

### 4.4 Which rules and words moved

Under the LLM rewrite, SpamAssassin's largest change was XPRIO ({{acct_spamassassin_XPRIO}} points per email), an X-Priority header rule that does not fire when the body holds any non-ASCII character, consistent with the model adding typographic quotes or dashes, which we did not check. In TF-IDF, common words shifted slightly, partly because each email's vector is scaled to unit length. Lynceus's social-engineering phrase rule started to fire on {{lynceus_social_starts}} of rewritten phishing emails.

## 5. Discussion

### 5.1 Interpretation

These layers draw much of their signal from links, headers, HTML structure and familiar phishing vocabulary. A rewrite that must keep the links, numbers and request keeps most of that signal; rewrites that dropped links did lose Lynceus detections. The new firings of Lynceus's phrase rule are consistent with fluent LLM prose adding urgent wording, a cause we did not test. The synonym swap removed some vocabulary signal; canonicalization, a bundle of changes (Section 3.5), removed far more.

Our result differs from the drops in [2]–[4], and the settings differ in ways that could explain it, none of which we tested: the prompts in [3] and [4] asked the model to replace spam-like words or remove urgency, while ours was neutral; [3]'s 73.7% applies to emails cut to minimal headers; we used a four-billion-parameter local model; and our rewrites had to keep their links and were compared with a version in the same format.

The main open question is comparability. The meaning check judged only {{judge_yes_same_label}} of pairs to keep their category. TF-IDF still flagged {{tfidf_lr_phishing_calibrated_llm_vs_null_a_b_pct}} of rewritten phishing and only {{tfidf_lr_ham_calibrated_llm_vs_null_a_b_pct}} of rewritten legitimate mail, but its near-perfect separation of our corpora may rest partly on their era and sources, so it is weak evidence of meaning. With one small judge and 30 pairs, we cannot settle the question.

### 5.2 Practical implications

For defenders, where a layer sits in the mail pipeline mattered more than the wording: a link- or structure-based layer that sees only text extracted from HTML loses much of its signal. For researchers, an evasion study should compare a rewrite with a version in the same format; otherwise a loss caused by conversion or lost links is credited to the wording.

### 5.3 Limitations

- The analysed emails are shorter than the rest, and the Lynceus default-threshold gain holds only for them.
- TF-IDF sits near its ceiling and Lynceus near its floor at the calibrated threshold.
- Our phishing is mostly HTML and our legitimate mail mostly plain text, unlike today's mail, so structure-based layers may raise more false alarms on modern mail than we measured.
- The corpora are old (legitimate 2002–2003, phishing 2005–2022), so style is mixed with era.
- The meaning check used one small judge and one checker, who saw its answers first.
- The synonym swap takes WordNet's first synonym, which often reads unnaturally: a crude baseline.
- The attacker is non-adaptive and single-pass, with one small model.
- We tested static layers only (Lynceus without its page, intelligence and AI-reviewer components), without sender reputation, DNS or authentication checks, on English text-only emails.
- The wording comparison describes rewriting a plain-text message, not an attacker's full HTML email.

## 6. Conclusion

For rewrites that kept their links, numbers and names, one paraphrase by a small local LLM did not lower detection: at the calibrated thresholds, phishing detection changed by {{spamassassin_phishing_calibrated_llm_vs_null_a_signed}} and {{tfidf_lr_phishing_calibrated_llm_vs_null_a_signed}} points for SpamAssassin and TF-IDF, with no drop larger than two points, while Lynceus sat at its floor. Converting emails to plain text changed Lynceus's default detection by {{lynceus_phishing_native_null_a_vs_orig_signed}} points, more than the whole end-to-end change of {{lynceus_phishing_native_llm_vs_orig_signed}}. For these layers, a message's links and structure matter more than its wording. Future work should test adaptive attackers, larger models, HTML-preserving rewrites, and a larger meaning check with several human raters.

## Declarations

**Declaration of Generative AI and AI-Assisted Technologies.** We designed this study: the research question, the study plan with its conditions, controls and analysis, and every methodological decision. We ran all experiments on our own computer, and we read and checked everything by hand: the meaning judgments, every source, and every reported number against the result files. We used Claude Code (Anthropic) as a programming and writing assistant under our direction. It implemented the data pipeline, detector adapters and analysis to our study plan, drafted and edited text that we reviewed, helped find sources, and entered our check results into the record files. Before this study, the first author designed Lynceus's architecture and built it with the assistant, which wrote the code and drafted rules and weights under the first author's direction. It did not rate, judge or verify anything. Two local models were part of the experiment itself: gemma3:4b produced the rewrites under study, and llama3.2:3b pre-filled the meaning-check sheet. Every use of AI is logged in `AI_LOG.md` in our repository.

**Ethics and model licence.** We rewrote only existing phishing emails from a public corpus, offline, after removing personal data. Nothing was sent, no email text left our computer, and the rewrites are not published. The generator's use policy [20] bars generating content for phishing and makes no research exception. We used it only for this defensive evaluation, and we declare that choice here.

**Data and code.** Code, configurations, hashes and aggregate results are at https://github.com/sodik-tursunboev/llm-phishing-study. Raw corpora are not redistributed: anyone can download them again and check them against our hashes. Raw rewrites are available to reviewers on request.

**Contributions.**

- Sodik Tursunboev and Kavish Chaudhari jointly proposed the research question.
- Sodik led the study: designing the protocol, choosing the data, the detectors and the generator, running the experiments, and writing. Sodik designed Lynceus's architecture and built it with an AI assistant before the study.
- Kavish checked the 30 meaning-check pairs, verified every reference, and checked the reported numbers against the result files.
- Both authors interpreted the results and revised the manuscript.

**Conflict of interest.** Lynceus is the first author's own tool. It went through the same controls as the other layers.

## References

<!-- IEEE style. Every entry below is listed in references/evidence_trail.csv. [19] was added on 2026-11-14 (metadata on Crossref and PubMed, abstract on PubMed) and verified by Kavish that day. -->

[1] Federal Bureau of Investigation, Internet Crime Complaint Center, "2025 IC3 annual report," 2026. [Online]. Available: https://www.ic3.gov/AnnualReport/Reports/2025_IC3Report.pdf (accessed Nov. 13, 2026).

[2] A. Ferrell, J. Xu, H. Moradi, R. E. Davis, and K. Roy, "Evaluating the effectiveness of existing phishing detectors on AI generated phishing emails," in *Proc. 2025 Cyber Awareness and Research Symposium (CARS)*, Grand Forks, ND, USA, Oct. 2025, doi: 10.1109/CARS67163.2025.11337548.

[3] M. Josten and T. Weis, "Investigating the effectiveness of Bayesian spam filters in detecting LLM-modified spam mails," arXiv:2408.14293, Aug. 2024. [Online]. Available: https://arxiv.org/abs/2408.14293

[4] K. Afane, W. Wei, Y. Mao, J. Farooq, and J. Chen, "Next-generation phishing: How LLM agents empower cyber attackers," arXiv:2411.13874, Nov. 2024. [Online]. Available: https://arxiv.org/abs/2411.13874

[5] J. Nazario, "Phishing corpus." [Online]. Available: https://monkey.org/~jose/phishing/ (accessed Nov. 11, 2026).

[6] OpenAI, "Introducing ChatGPT," Nov. 30, 2022. [Online]. Available: https://openai.com/index/chatgpt/ (accessed Nov. 11, 2026).

[7] Apache SpamAssassin Project, "SpamAssassin public mail corpus." [Online]. Available: https://spamassassin.apache.org/old/publiccorpus/ (accessed Nov. 11, 2026).

[8] M. M. Danilak, "langdetect 1.0.9," Python Package Index, May 2021. [Online]. Available: https://pypi.org/project/langdetect/1.0.9/

[9] G. A. Miller, "WordNet: A lexical database for English," *Commun. ACM*, vol. 38, no. 11, pp. 39–41, Nov. 1995, doi: 10.1145/219717.219748.

[10] NLTK Project, "NLTK: Natural Language Toolkit." [Online]. Available: https://www.nltk.org/ (accessed Nov. 12, 2026).

[11] Gemma Team, "Gemma 3 technical report," arXiv:2503.19786, Mar. 2025. [Online]. Available: https://arxiv.org/abs/2503.19786

[12] Ollama, "Ollama," GitHub repository. [Online]. Available: https://github.com/ollama/ollama (accessed Nov. 12, 2026).

[13] Meta AI, "Llama 3.2: Revolutionizing edge AI and vision with open, customizable models," Sep. 25, 2024. [Online]. Available: https://ai.meta.com/blog/llama-3-2-connect-2024-vision-edge-mobile-devices/

[14] Apache SpamAssassin Project, "Apache SpamAssassin." [Online]. Available: https://spamassassin.apache.org/ (accessed Nov. 12, 2026).

[15] F. Pedregosa *et al.*, "Scikit-learn: Machine learning in Python," *J. Mach. Learn. Res.*, vol. 12, no. 85, pp. 2825–2830, 2011. [Online]. Available: https://jmlr.org/papers/v12/pedregosa11a.html

[16] B. Efron, "Bootstrap methods: Another look at the jackknife," *Ann. Statist.*, vol. 7, no. 1, pp. 1–26, 1979, doi: 10.1214/aos/1176344552.

[17] Q. McNemar, "Note on the sampling error of the difference between correlated proportions or percentages," *Psychometrika*, vol. 12, no. 2, pp. 153–157, 1947, doi: 10.1007/BF02295996.

[18] S. Holm, "A simple sequentially rejective multiple test procedure," *Scand. J. Statist.*, vol. 6, no. 2, pp. 65–70, 1979. [Online]. Available: https://www.jstor.org/stable/4615733

[19] R. G. Newcombe, "Improved confidence intervals for the difference between binomial proportions based on paired data," *Stat. Med.*, vol. 17, no. 22, pp. 2635–2650, Nov. 1998, doi: 10.1002/(SICI)1097-0258(19981130)17:22<2635::AID-SIM954>3.0.CO;2-C.

[20] Google, "Gemma prohibited use policy," last modified Feb. 21, 2024. [Online]. Available: https://gemma.ai/resources/prohibited-use/ (accessed Nov. 12, 2026).
