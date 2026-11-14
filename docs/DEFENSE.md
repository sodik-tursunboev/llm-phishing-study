# Defence briefing: learn this, then explain it without notes

Numbers below come from `results/` (file in brackets). If a number in the paper ever differs, the paper is right: it is filled from the files.

## 1. The study in one minute

"Papers report that LLM-rewritten phishing slips past filters. We asked whether that is really the *wording*. We took real phishing and legitimate emails from public corpora and made four versions of each:
- the original;
- a canonical plain-text version;
- a dictionary synonym swap;
- one rewrite by a small local model that had to keep every link, number and name.

Three static detectors scored all four versions: SpamAssassin, a TF-IDF classifier, and Lynceus, Sodik's own rule-based tool. The rewrite did **not** lower detection: for SpamAssassin and TF-IDF a drop larger than 2 points is ruled out, and Lynceus was at its floor at the strict threshold. The big drop came from turning HTML emails into plain text, not from the new wording."

## 2. Why our controls isolate the wording

- **Paired design.** Every email is compared only with itself, so differences between emails cannot explain the result.
- **null-A (canonical plain text).** The model can only rewrite plain text, so we first turn every email into plain text by a fixed rule. The rewrite is compared with *that*, not with the original HTML email. Rewrite vs null-A therefore differ only in wording.
- **lex (synonym swap).** It changes as many words as the model does (36.4%, the pilot median), but with a dictionary and no AI. It answers whether *any* rewording of that size hurts. It did, a little (about 3 points); the LLM rewrite did not.
- **Gates.** A rewrite counts only if it keeps every link, number, address and placeholder, stays a similar length, stays English, and adds no refusal. So the detectors see the same links and facts.
- **Freeze.** Thresholds, models and the plan were fixed before any rewrite was scored (tag `protocol-freeze-v1`), so nothing was tuned to the result.

## 3. What null-A really changes (be precise)

null-A is a **controlled canonicalization**, not "format only" (`canonical_test.json`). For phishing:
- 64% were HTML-only and became visible text with `<URL>`;
- 30% had a plain part, so the HTML part was dropped;
- 71% lost at least one link, mostly image or style links outside anchors.

So orig → null-A is causal for this **bundle**. We cannot say whether the HTML structure or the lost links matter more. Say exactly that.

## 4. Why the meaning check matters, and what it showed

Gates check facts (links, numbers), not meaning. A rewrite could keep every link and still change what the email asks for. So a second local model (llama3.2:3b) judged 30 pairs on four questions, and Kavish read all 30 and accepted every answer (`judge.json`). Kavish worked from Sodik's account; the assistant only typed Kavish's name into the sheet:
- action kept 70%;
- target kept 83%;
- urgency kept 73%;
- **category kept only 30%**;
- all four 23%.

**Your honest answer:** "The meaning check is our weakest point. Taken at face value, many rewrites no longer read like their category. TF-IDF still flags 100% of rewritten phishing and only 2.5% of rewritten legitimate mail, but that is weak evidence: it separates our two corpora almost perfectly (AUC 0.9995), probably partly by era and source. With a 3B judge and 30 pairs we can't settle it, so we report both and call it a limitation."

## 5. Difference versus cause (the coordinator's second question)

- **Observation:** the paired change and its confidence interval (Table 1).
- **Accounting (what moved):**
  - SpamAssassin's score is a sum of rule points, so we see which rules changed;
  - TF-IDF's score is a sum of word contributions, so we see which words changed;
  - Lynceus lists the rules that fired.
- **Cause:** claimed only when a fixed rule, with no AI, changed the message: the canonicalization. Everything else is "consistent with". Example: on gate-passed rewrites, Lynceus caught *more* phishing (+4.5 points), and its social-engineering phrase rule started firing on 15% of them. That is consistent with the model adding urgent wording, but we did not test it. It also does not survive the sensitivity check: on all 435 rewrites the change is −0.7 (inconclusive), because rewrites that dropped a link lost Lynceus detections. Say this before you are asked.

## 6. Lynceus: what you built and how it fits

- **What it is:** Sodik's local, rule-based phishing detector (URL rules, sender rules, HTML and link rules, one phrase rule), built before this study. Sodik designed and directed it and approved every rule; the AI assistant wrote the code and proposed the rules and weights. The paper says exactly that (`LYNCEUS_NOTES.md` section 9).
- **How it fits:** one of three layers, used through its own message engine. Only the Windows sandbox launcher was swapped, so it runs offline in Docker. It was frozen (tag `lynceus-eval-v1`) before any rewrite was scored.
- **Conflict of interest:** we evaluated our own tool under the same controls and reported its results as they came:
  - at the 1% false-alarm threshold it sits near the floor (catching 1–2%);
  - at its default threshold, canonicalization cut it from 55% to 29.5%.
- **The improvement made during the study** changed no verdict on our data: 997 of 997 dev messages were identical before and after (DEVIATIONS #17).

## 7. What we add beyond Ferrell et al. [2]

[2] measured machine-learning detectors (BERT, Word2Vec, stylometric) on rephrased emails and found 3–20% drops. **We have only read its abstract; read the full text before the defence** and check the open questions in `research/related_work.md`. We add:
- static **rule-based** layers;
- rewrites forced to keep links and numbers;
- a **paired** test with confidence intervals;
- the separation of **wording** from **canonicalization**.

Our result: wording alone did not lower detection here; canonicalization did. End to end (`decomposition_test.csv`), sending the rewrite as plain text instead of the original cost Lynceus 21.0 points at its default threshold: −25.5 from canonicalization, +4.5 from the wording. An evasion study that compares a plain-text rewrite with the HTML original would credit that loss to the LLM.

## 8. Likely questions, short answers

- **Why do you disagree with Josten & Weis (73.7%)?** Read their Table 4: 73.7% is for spam cut to minimal headers; with the original headers it was 9.4%. Their prompt also told GPT-3.5 to "replace spam-like words", an evasion instruction; ours was neutral. Afane et al. [4] likewise asked for emails "designed to bypass email phishing detectors". We did not test these differences, but they test a different attacker (`research/related_work.md`).
- **Why only one model?** Time and a 4 GB GPU. It is logged as a deviation and listed as a limitation.
- **Why Gemma, given its licence?** It was the strongest model that fitted. Its policy bans phishing content with no research exception; we used it offline, sent nothing, published no rewrites, and declare it in the paper.
- **Why 200 per class?** Our pre-set minimum. Generation stopped when 200 per class passed the gates; that rule looked only at the gates, never at any detector.
- **Why a 1% false-alarm threshold?** It gives every layer a comparable, realistic operating point, fixed on dev data. We also report each tool's default.
- **What does McNemar test?** Whether, among emails that changed outcome, losses and gains are unbalanced. Ours were balanced (Holm p = 1.0).
- **Why a cluster bootstrap?** Emails from the same campaign template are not independent, so we resample whole templates when computing the interval.
- **Why only 46% / 36% passing the gates?** The small model often dropped a link or a number. Analysed emails are therefore shorter; we report kept vs discarded and repeat every result on all rewrites. The calibrated-threshold readings for SpamAssassin and TF-IDF stay the same; the Lynceus default-threshold gain does not.
- **Did AI write this?** Claude Code wrote the code to our specification and drafted the text, and the paper declares it. We designed the study, took every decision and ran it on our machine. We read and checked everything by hand: Kavish checked the meaning judgments, every reference and every number. The assistant typed our check results into files; it never rated, judged or verified anything.
- **Why is every commit under Sodik's name?** Kavish worked from Sodik's account. `CONTRIBUTIONS.md` records who did each task; commit authorship does not.
- **Your interval is [0, 0]. Are you certain of zero change?** No. With zero or one changed outcome, a bootstrap interval collapses. We added Newcombe's paired interval as a check (`exact_test.csv`, DEVIATIONS #24): it is [−1.3, +2.4] for SpamAssassin and [−1.4, +2.8] for TF-IDF, so a drop larger than 2 points is still ruled out, but not a gain of that size.
- **TF-IDF has an AUC of 0.9995. What is it detecting?** Partly the difference between our corpora: legitimate mail from 2002–2003 mailing lists, phishing from 2005–2022. That is why it sits at its ceiling. Its score shift is the useful number: +0.03 logits for phishing rewrites, so the wording barely moved it; and +0.67 for legitimate rewrites, towards phishing.
- **Why did XPRIO, a header rule, move when the headers never change?** It is a meta rule: it fires only if, among other conditions, the body has no non-ASCII character (`__L_BODY_8BITS` in SpamAssassin's `72_active.cf`). Typographic quotes or dashes added by the model would switch it off. We did not check that.
- **Why did the TF-IDF word "subject" move when the subject never changes?** Each email's vector is scaled to unit length, so any change in other words changes every word's weight.
- **Isn't "canonicalization hurts" just "deleting information hurts"?** Partly, yes, and we say it is a bundle. The point is where the deletion happens: a layer placed after text extraction loses its signal, and an evasion study that compares a plain-text rewrite with an HTML original credits that loss to the LLM.
- **What next?** Several models, an adaptive attacker, HTML-preserving rewrites, and a larger human meaning check.

## 9. Weaknesses to admit before they are pointed out

- The meaning check (category 30%), one small judge, and a checker who saw its answers first.
- The Lynceus default-threshold gain holds only for gate-passed rewrites.
- Our phishing is 95% HTML and our legitimate mail 4% HTML, unlike modern mail.
- The synonym swap (first WordNet synonym) is a crude baseline.
- One small model, and a non-adaptive attacker.
- The analysed emails are shorter than the rest.
- Old corpora: style mixed with era.
- The canonicalization effect is a bundle.
- Lynceus is near its floor at the strict threshold.
- We evaluated our own tool.
