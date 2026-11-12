<!--
Manuscript source. Every number is a {{placeholder}} filled from result and config files by
`python -m src.paper.build`; never type a number here. Student IDs come from the git-ignored
paper/authors.local.json. Before submitting, the authors must make every statement in the
Declarations true: Kavish verifies each reference and number; both authors read the full texts of
[1]-[3], revise the text in their own words, and can explain every sentence.
-->

# Does One-Pass LLM Paraphrasing Lower Detection by Static Email Filters? A Paired, Offline Study

*Official topic: The Evasion Capabilities of LLM-Generated Phishing Payloads Against Static Security Architectures*

Sodik Tursunboev, Kavish Chaudhari · Vistula University · Architecture of Computers 2026/27 · Student IDs: {{student_ids}}

## Abstract

Several studies report that LLM-rewritten phishing slips past existing filters. We asked whether one paraphrase by a small local model, with no feedback from any filter, lowers detection by static email defences, and which layer loses it.

We tested three static layers: SpamAssassin, a TF-IDF classifier with logistic regression, and Lynceus, a rule-based detector built by the first author. We scored each of {{gates_phishing_passed}} phishing and {{gates_ham_passed}} legitimate emails from public corpora in four versions:
- as received;
- as a canonical plain-text version;
- after a dictionary synonym swap;
- after a gemma3:4b rewrite that had to keep every link, number and name.

Compared with the plain-text version, the rewrite did not lower phishing detection at the calibrated thresholds. SpamAssassin changed by {{spamassassin_phishing_calibrated_llm_vs_null_a_signed}} percentage points (95% CI {{spamassassin_phishing_calibrated_llm_vs_null_a_ci}}), TF-IDF by {{tfidf_lr_phishing_calibrated_llm_vs_null_a_signed}} ({{tfidf_lr_phishing_calibrated_llm_vs_null_a_ci}}) and Lynceus by {{lynceus_phishing_calibrated_llm_vs_null_a_signed}} ({{lynceus_phishing_calibrated_llm_vs_null_a_ci}}). At its default threshold, Lynceus even caught more rewritten phishing ({{lynceus_phishing_native_llm_vs_null_a_signed}} points). The synonym swap cost a few points. Canonicalizing the emails to plain text, which strips their HTML and drops links outside anchors, lowered Lynceus's detection from {{lynceus_phishing_native_null_a_vs_orig_a_pct}} to {{lynceus_phishing_native_null_a_vs_orig_b_pct}}.

Under this protocol, the wording of a gate-passed, constraint-preserving rewrite did not weaken these filters; how the message was represented mattered far more. Adaptive attackers, larger models and commercial filters remain outside our scope.

## 1. Introduction

Many filters catch what scams share: clumsy phrasing, odd spelling, familiar wording. Large language models (LLMs) can turn an awkward scam into fluent text in seconds, at almost no cost. Earlier studies report that LLM rewriting lowers detection by SpamAssassin, commercial filters and machine-learning detectors [1]–[3].

When detection drops, is it the new wording, or something else that changes along the way: the message's representation, a lost link, a different request? We study the simplest version of the threat. An attacker takes existing phishing emails and asks a local, open-weight model to rewrite each one once, with a neutral instruction and no feedback from any filter.

Our research question is: **how much does detection by static email-security layers drop, and which layer accounts for the loss?** We also check whether any drop comes from the LLM itself, rather than from re-encoding or from changing words at all, and whether the rewrites still say the same thing.

Our contribution is a careful measurement, not a new attack or a new detector. Ferrell et al. [1] measured machine-learning detectors on rephrased emails. We go further in three ways: we test static, rule-based layers; we require every rewrite to keep its links and numbers; and we separate the effect of the wording from the effect of canonicalizing the message to plain text.

## 2. Related work

Ferrell et al. [1] asked three LLMs to rephrase phishing and safe emails, then tested existing detectors on the results. Accuracy fell by 3–4% for BERT-based models and by 8–20% for Word2Vec and stylometric models, and retraining on rephrased emails restored it.

Josten and Weis [2] rewrote spam with GPT-3.5 Turbo. SpamAssassin let up to 73.7% of the modified spam through as legitimate, while a simple dictionary-replacement attack succeeded at most 0.4% of the time. Afane et al. [3] report declines for Gmail, SpamAssassin, Proofpoint and classical classifiers on LLM-rephrased phishing.

These studies show that rewriting can hurt detection. They leave open how much of the drop survives when the rewrite must keep the links, numbers and request and the representation is held fixed, and which part of a pipeline is responsible.

## 3. Method

We fixed the full protocol before any rewritten email was scored (git tag `protocol-freeze-v1`), and logged every later change in `DEVIATIONS.md`. Scoring and analysis ran in a Docker container with networking switched off. A local model server on the same computer produced the rewrites, so no email text ever left the machine.

Compared with our proposal, we made three changes to fit the time available. We used one generator instead of two or three. Lynceus, which includes URL rules, replaced a separate URL layer. And an exact rule-and-word accounting replaced the planned list of content-only detections.

### 3.1 Data

Phishing emails come from the Nazario phishing corpus [4] (CC BY 4.0), collected between 2005 and 2022. To keep this class human-written, we dropped messages dated on or after 30 November 2022, the day ChatGPT was released [5]. Legitimate emails come from the SpamAssassin public corpus [6] (easy_ham, easy_ham_2 and hard_ham). Every raw file is pinned by its SHA-256 hash.

We started from {{phishing_read}} phishing and {{ham_read}} legitimate messages, and kept only English text emails. That removed:
- {{phishing_non_text_part}} phishing and {{ham_non_text_part}} legitimate messages with attachments or other non-text parts;
- {{phishing_not_english}} and {{ham_not_english}} that langdetect [7] did not identify as English;
- {{phishing_empty}} and {{ham_empty}} with an empty body;
- {{phishing_after_cutoff}} phishing messages sent after the cutoff, and {{phishing_date_unknown}} with no usable date.

We then removed personal data: the local part of every address, phone numbers and recipients' names. We also dropped near-duplicates, meaning messages that share at least 80% of their five-word phrases ({{phishing_near_duplicate}} phishing, {{ham_near_duplicate}} legitimate). This left {{phishing_kept}} phishing and {{ham_kept}} legitimate emails.

Phishing campaigns reuse templates. So we grouped messages that share at least half of their five-word phrases into clusters, and assigned whole clusters at random to the training, development, test and pilot splits. No template appears in two splits. The test split holds {{phishing_test}} phishing and {{ham_test}} legitimate emails.

### 3.2 Four versions of every email

We scored every test email in four versions, so each message is only ever compared with itself. The headers never change; only the body does. A model with four billion parameters cannot rewrite HTML reliably, so all rewriting starts from the canonical plain-text version, null-A.

- **orig** is the email as received.
- **null-A** is a controlled canonicalization of orig, made by a fixed rule with no model involved.
  - It keeps the headers, but replaces the body with one UTF-8 text/plain part.
  - That part is the email's own plain part if it has one, and any HTML alternative is dropped. Otherwise it is the visible text of the HTML, with each link's address written after its anchor text as `<URL>`.
  - HTML tags, styles and scripts disappear, and so does every link that appears only outside an anchor, for example in an image or a stylesheet.
  
  Comparing the rewrite with null-A isolates the wording. Comparing null-A with orig measures this canonicalization as a whole.
- **lex** is the null-A text after a dictionary synonym swap, using WordNet [8] through NLTK [9]. We swapped words until {{lex_dose}} of them had changed, the median change the model made on the pilot. Links, addresses and placeholders were never touched. This version answers whether *any* rewording of that size lowers detection.
- **llm** is one paraphrase of the null-A text by gemma3:4b [10], run locally through Ollama [11] at temperature 0 with a fixed seed. The prompt was: *"Rewrite the following email in your own words. Keep every link, name, number and the requested action unchanged. Output only the rewritten email text."* It never mentions filters or detection, and the model received no feedback. We counted refusals and did not work around them.

We rewrote test emails in a fixed random order until 200 rewrites per class had passed the checks below. The stopping rule looked only at those checks, never at any detector.

### 3.3 Is the rewrite still the same email?

A rewrite entered the analysis only if, compared with its null-A text, it:
- kept the same set of links, numbers, addresses and placeholders, ignoring formatting such as "2,500" against "2500";
- stayed between half and twice the original length;
- was still in English;
- added no refusal or comment of its own.

We fixed these gates on a 53-message pilot ({{pilot_passed}} of 53 passed) before the main run. We compare the emails that failed them with those that passed.

Gates check facts, not meaning. For meaning, llama3.2:3b [12], a local model from a different family than the generator, judged 30 rewrite pairs (15 per class). For each pair it answered four questions: does the rewrite keep the requested action, the target and entities, the urgency, and the category (phishing or legitimate)? A human then read every pair and corrected any answer they disagreed with.

### 3.4 Detectors

All three layers are static: fixed rules, or a frozen model that does not learn from the emails it scores.

- **SpamAssassin** ({{spamassassin_version}}) [13], with its shipped rules, local tests only, and its Bayesian learning switched off.
- **A TF-IDF classifier with logistic regression** [14], trained only on the training split ({{phishing_train}} phishing, {{ham_train}} legitimate). We chose its one setting on the development split (C = {{l2_C}}, AUC {{l2_dev_auc}}) and then froze it. It reads the subject and the visible body text.
- **Lynceus** ({{lynceus_version}}), a rule-based phishing detector that the first author developed before this study, with AI assistance for the code. We use its message engine unchanged, except for its Windows sandbox launcher, which we replaced so it runs offline in our container. We froze it before any rewrite was scored. Its signal comes mostly from links, the sender and HTML structure, plus one rule for urgent, credential-requesting phrases. Because we are evaluating our own tool, it went through exactly the same controls as the other layers.

We used each layer at two operating points: its own default, and a threshold fixed on the development split so that at most 1% of legitimate emails are flagged (SpamAssassin {{spamassassin_threshold}}, TF-IDF {{tfidf_lr_threshold}}, Lynceus {{lynceus_threshold}}). Neither was touched after rewritten emails were scored.

### 3.5 Analysis

Our main comparison is the LLM rewrite against null-A, because the two differ only in wording. We also compare the synonym swap with null-A, the rewrite with the synonym swap, and null-A with the original.

For each layer, class and operating point, we report:
- the detections lost and gained;
- the net change in percentage points, with a 95% confidence interval from a bootstrap [15] that resamples whole template clusters (10,000 resamples, fixed seed);
- an exact McNemar test [16].

The confirmatory test is phishing at the calibrated threshold, rewrite against null-A: one test per layer, with a Holm correction [17]. Everything else is descriptive. We read an interval that excludes zero as a change, an interval inside ±2 points as "no change larger than 2 points", and anything else as inconclusive. We repeat every result on all rewrites, including those that failed the gates.

Finally, we keep an observed difference apart from its cause. SpamAssassin's score is a sum of rule points, the classifier's score is a sum of word contributions, and Lynceus lists the rules that fired. So we can show exactly which rules and words moved. We claim a cause only where a rule-based edit, with no model involved, changed the message. null-A is such an edit, but it changes several things at once. Its effect is therefore causal for the canonicalization as a whole, not for any one of its parts. Everything else we describe as "consistent with".

## 4. Results

### 4.1 The rewrites

We rewrote {{rewritten_total}} test emails. Another {{gates_phishing_not_rewritten_too_long}} phishing and {{gates_ham_not_rewritten_too_long}} legitimate emails were too long to rewrite; we counted them but did not analyse them. Of the rewrites, {{gates_phishing_passed}} of {{gates_phishing_rewritten}} phishing and {{gates_ham_passed}} of {{gates_ham_rewritten}} legitimate ones passed every gate (Table 2).

The model refused in {{refusals}} case. Most failures were rewrites that dropped a link or a number. The emails that passed were shorter than those that did not: for phishing, a median of {{sel_phishing_kept_words}} against {{sel_phishing_discarded_words}} words, and {{sel_phishing_kept_urls}} against {{sel_phishing_discarded_urls}} links. Our analysed pairs therefore lean towards short emails.

In the meaning check, the accepted judgments say the rewrite kept:
- the requested action in {{judge_yes_same_action}} of pairs;
- the target, links and names in {{judge_yes_same_target}};
- the urgency in {{judge_yes_same_urgency}};
- the category in only {{judge_yes_same_label}}.

{{judge_equivalent_rate}} were equivalent on all four. {{judge_checks}}
### 4.2 The wording of the rewrite

Table 1 shows how often each layer flagged each version. Against the canonical version (null-A), the rewrite changed phishing detection at the calibrated thresholds by:
- {{spamassassin_phishing_calibrated_llm_vs_null_a_signed}} points for SpamAssassin ({{spamassassin_phishing_calibrated_llm_vs_null_a_ci}});
- {{tfidf_lr_phishing_calibrated_llm_vs_null_a_signed}} for TF-IDF ({{tfidf_lr_phishing_calibrated_llm_vs_null_a_ci}});
- {{lynceus_phishing_calibrated_llm_vs_null_a_signed}} for Lynceus ({{lynceus_phishing_calibrated_llm_vs_null_a_ci}}).

The Holm-adjusted p-values were {{spamassassin_phishing_calibrated_llm_vs_null_a_holm_p}}, {{tfidf_lr_phishing_calibrated_llm_vs_null_a_holm_p}} and {{lynceus_phishing_calibrated_llm_vs_null_a_holm_p}}. For SpamAssassin and TF-IDF, the intervals rule out a change larger than two points in either direction.

At its calibrated threshold, Lynceus flagged only {{lynceus_phishing_calibrated_llm_vs_null_a_a_pct}} of plain-text phishing to begin with: a floor effect. At its default threshold, it flagged *more* phishing after the rewrite: {{lynceus_phishing_native_llm_vs_null_a_a_pct}} rose to {{lynceus_phishing_native_llm_vs_null_a_b_pct}} ({{lynceus_phishing_native_llm_vs_null_a_signed}} points, {{lynceus_phishing_native_llm_vs_null_a_ci}}).

On legitimate mail, no layer's false positives rose beyond the margin. The one inconclusive case was TF-IDF ({{tfidf_lr_ham_calibrated_llm_vs_null_a_signed}} points, {{tfidf_lr_ham_calibrated_llm_vs_null_a_ci}}).

Adding back the rewrites that failed the gates changes nothing. SpamAssassin, for example, moved by {{all_spamassassin_phishing_calibrated_llm_vs_null_a_signed}} points ({{all_spamassassin_phishing_calibrated_llm_vs_null_a_ci}}) across all {{all_spamassassin_phishing_calibrated_llm_vs_null_a_n}} phishing rewrites.

### 4.3 Rewording without an LLM, and canonicalization

The synonym swap did lower phishing detection a little at the default thresholds:
- {{spamassassin_phishing_native_lex_vs_null_a_signed}} points for SpamAssassin ({{spamassassin_phishing_native_lex_vs_null_a_ci}});
- {{tfidf_lr_phishing_native_lex_vs_null_a_signed}} for TF-IDF ({{tfidf_lr_phishing_native_lex_vs_null_a_ci}});
- {{lynceus_phishing_native_lex_vs_null_a_signed}} for Lynceus ({{lynceus_phishing_native_lex_vs_null_a_ci}}).

The LLM rewrite was actually flagged *more* often than the synonym swap, by SpamAssassin ({{spamassassin_phishing_native_llm_vs_lex_signed}} points, {{spamassassin_phishing_native_llm_vs_lex_ci}}) and by Lynceus ({{lynceus_phishing_native_llm_vs_lex_signed}}, {{lynceus_phishing_native_llm_vs_lex_ci}}).

The biggest change in the whole study came from canonicalization alone. For the phishing pairs:
- it turned the HTML of {{canon_phishing_pct_html_only_converted_to_text}} of emails into text;
- it dropped the HTML alternative of another {{canon_phishing_pct_html_part_dropped_plain_part_kept}};
- {{canon_phishing_pct_losing_at_least_one_url}} lost at least one link, almost always a link outside an anchor (median distinct links {{canon_phishing_median_distinct_urls_orig}} before and {{canon_phishing_median_distinct_urls_null_a}} after).

Legitimate mail was barely affected, since almost all of it is plain text already.

Canonicalization lowered Lynceus's default detection from {{lynceus_phishing_native_null_a_vs_orig_a_pct}} to {{lynceus_phishing_native_null_a_vs_orig_b_pct}} ({{lynceus_phishing_native_null_a_vs_orig_signed}} points, {{lynceus_phishing_native_null_a_vs_orig_ci}}). It changed SpamAssassin's by {{spamassassin_phishing_native_null_a_vs_orig_signed}} points ({{spamassassin_phishing_native_null_a_vs_orig_ci}}). TF-IDF did not move, even though its input changed for {{canon_phishing_pct_tfidf_input_changed}} of phishing emails, where the `<URL>` strings now appear in the visible text.

### 4.4 What moved, and why

Under the LLM rewrite, the accounting shows only small changes for SpamAssassin, where a few rules for misspelled brand names stopped firing, and for TF-IDF, where common words shifted slightly.

Lynceus's social-engineering phrase rule started to fire on {{lynceus_social_starts}} of rewritten phishing emails. That is consistent with the model adding urgent, credential-requesting wording, although we did not test that cause.

The canonicalization effect is different. null-A is a fixed, rule-based edit of the same message, so its effect is causal by design, but only for the bundle as a whole. We cannot say whether the lost HTML structure or the lost links matter more for Lynceus. Both are consistent with its rules, which read anchors and HTML as well as URLs.

**Table 1.** Share of emails flagged (%) at the calibrated threshold, gate-passed pairs, for each version. The last columns give the main comparison (rewrite against null-A) with its 95% cluster-bootstrap confidence interval, and the Holm p for the three confirmatory tests.

{{table_main}}

**Table 2.** Rewrites per class, how many passed every gate, and how many failed each gate. A rewrite can fail several gates.

{{table_gates}}

## 5. Discussion and limitations

Under our protocol, a gate-passed, constraint-preserving rewrite by a small local model did not make phishing harder to detect for any of the three static layers; for Lynceus, it made phishing slightly easier to detect. That is a negative result, with a simple explanation.

These layers draw much of their signal from links, headers, HTML structure and familiar phishing vocabulary. A rewrite that must keep the links, numbers and request keeps most of that signal, and fluent LLM prose may even add vocabulary. A crude synonym swap removed some of it and cost a few points. Canonicalization, which strips the HTML and drops links outside anchors, cost far more.

Our result differs from the large drops reported in [1]–[3], and the settings differ in ways that could explain it. We tested none of these differences:
- our SpamAssassin ran without the Bayesian component that is central to [2];
- we used a four-billion-parameter local model, not GPT-3.5 Turbo;
- we rewrote phishing rather than spam;
- every analysed rewrite had to keep its links and numbers.
The main open question is comparability. The meaning check judged only {{judge_yes_same_label}} of pairs to keep their category, which would mean many rewrites no longer read like their original. The detectors disagree. The TF-IDF classifier, trained only on human-written emails, still flagged {{tfidf_lr_phishing_calibrated_llm_vs_null_a_b_pct}} of rewritten phishing and only {{tfidf_lr_ham_calibrated_llm_vs_null_a_b_pct}} of rewritten legitimate mail. With one small judge model and 30 pairs, we cannot tell which signal is right, so we report both.

Two further limits apply. The emails that passed the gates are shorter than the rest. And the TF-IDF classifier sits close to its ceiling, while Lynceus sits close to its floor at the calibrated threshold, which limits what those two comparisons can show.

The study also has deliberate limits:
- The attacker is non-adaptive and makes one pass, which underestimates a determined attacker.
- The corpora are old: legitimate mail from 2002–2003, phishing from 2005–2022. Writing style is therefore mixed with era. Pairing controls content, not era.
- We used one small open-weight model rather than frontier models.
- SpamAssassin running offline is not a commercial filter, and we tested only static layers, without sender reputation, DNS or authentication checks.
- All emails were text-only and in English.
- Rewriting needs plain text, so the wording comparison is made on canonicalized emails, which have already lost their HTML and some links. It describes rewriting a plain-text message, not an attacker's full HTML email.

## Declarations

**Declaration of Generative AI and AI-Assisted Technologies.** We used Claude Code (Anthropic) as a programming and writing assistant. It helped us write and test the data pipeline and analysis scripts, find and open sources, and draft and edit this text. Lynceus, the first author's detector, was also built with Claude Code's help before this study.

Two local models were part of the experiment itself: gemma3:4b produced the rewrites under study, and llama3.2:3b pre-filled the meaning-check sheet.

We designed the study and took every methodological decision. We ran the experiments on our own computer, checked the meaning judgments, opened and verified every source, and checked every reported number against the result files. Every use of AI is logged in `AI_LOG.md` in our repository.

**Ethics and model licence.** We only rewrote existing phishing emails from a public corpus, offline. Nothing was sent, no email text left our computer, and the rewrites are not published. The generator's use policy [18] bars generating content for phishing and makes no research exception. We used it only for this defensive evaluation, and we declare that choice here.

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
