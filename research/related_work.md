# Related work (README task R1)

Prepared by Claude Code on 2026-11-14 from the sources it opened:
- [3] and [4]: full text, arXiv version 1 PDFs;
- [2]: abstract only, from its Semantic Scholar record. The IEEE full text is closed access, and no open copy was found.

Nothing here is from memory. **The comparison row for [2] needs the authors, who must read its full text (README section 2, coordinator guidance 1).** Reference numbers are those of `paper/manuscript.md`.

## Comparison table

| | [2] Ferrell et al. 2025 | [3] Josten and Weis 2024 | [4] Afane et al. 2024 | This study |
|---|---|---|---|---|
| **Generators** | "Three different LLMs" (not named in the abstract) | GPT-3.5 Turbo through the OpenAI API (GPT-4o tried; about 95% of requests refused) | GPT-4o for the detector tests; GPT-4 and Llama 3 for the augmented dataset | gemma3:4b, local |
| **Rewrite or generate** | Rewrite ("rephrased versions") | Rewrite of the body only; headers kept | Rewrite of subject and body; sender and receiver kept | Rewrite of the body only; headers kept |
| **Prompt** | UNKNOWN | Evasive: "rephrase the previous content to be less aggressive and replace spam-like words and formulations", plus "Preserve all links" (P2, P3) | Evasive: rewrite emails "designed to bypass email phishing detectors", remove urgency and money amounts; few-shot examples "crafted carefully to bypass phishing detectors"; a "for research" framing to get past model refusals | Neutral: "Rewrite the following email in your own words. Keep every link, name, number and the requested action unchanged." |
| **Detectors** | BERT-based, Word2Vec and stylometric models | SpamAssassin, default configuration of a Docker image, called a Bayesian filter; whether its Bayes database was trained is not stated | Gmail, SpamAssassin and Proofpoint (live services; emails sent to accounts); Naive Bayes, SVM and logistic regression with TF-IDF; five LLMs as detectors | SpamAssassin 4.0.1 offline with Bayes off; frozen TF-IDF with logistic regression; Lynceus's static message engine |
| **Data** | Phishing and safe emails (sources not in the abstract) | SpamAssassin public corpus spam (2,399); only emails SpamAssassin flagged before rewriting were kept (1,457 with original headers, 189 with minimal headers) | "Nazario" set of 600 phishing and 600 legitimate emails, plus 400 and 400 "Nigerian Fraud"; emails of 10–350 and 10–650 characters; only sender, receiver, subject and body kept | Nazario phishing (pre-ChatGPT) and SpamAssassin ham; 200 and 200 gate-passed test emails, cluster-disjoint splits |
| **Metrics and statistics** | Accuracy | Success rate (share of rewritten spam classified as ham); no intervals or tests | Accuracy, precision, recall, F1; no intervals or tests; LLM detectors run three times with a majority vote | Paired change per email, cluster-bootstrap CI, McNemar with Holm correction, paired score shift |
| **Rewrite-validity check** | UNKNOWN | Embedding cosine similarity (mean about 0.8); no human check | None reported | Hard gates (links, numbers, entities, length, language, refusals) plus a 30-pair model judgment checked by an author |
| **Null or lexical controls** | UNKNOWN | Dictionary replacement of 750 "spam words" with GPT-4-Turbo alternatives (success at most 0.4%) | None | Plain-text canonical version (null-A) and a dose-matched WordNet swap (lex) |
| **Layer or rule analysis** | UNKNOWN | Header effect: misclassification 9.4% with original headers vs 73.7% with minimal headers (Table 4) | Word-level discussion of the decision boundary (Naive Bayes, logistic regression) | SpamAssassin rule points, TF-IDF word contributions, Lynceus rules |
| **Code or data released** | UNKNOWN | Pipeline code at github.com/MalteJosten/llm-spam-test (stated; not opened) | LLM-Nazario dataset "will be shared" (not checked) | Code, configs, hashes, aggregate results; rewrites to reviewers on request |
| **Main result** | Accuracy fell 3–4% (BERT-based) and 8–20% (Word2Vec, stylometric); retraining on rephrased emails helped | 9.4% (original headers) and 73.7% (minimal headers) of rewritten spam passed as ham | SpamAssassin recall on Nazario phishing 95.99% (original), 91.26% (zero-shot), 80.96% (few-shot) (Table I) | No drop from the wording for SpamAssassin or TF-IDF at the calibrated threshold; plain-text conversion cost Lynceus 25.5 points |
| **Limits they state** | UNKNOWN | Old dataset; 20–25% of requests refused; possibly the choice of filter | Short emails; prompt design | See the paper, section 5.3 |

## What the comparison shows

1. **The prompt.** [3] and [4] asked the model to remove spam-like words, or urgency, so that the email would pass the filters. Our prompt was neutral and the model got no feedback. Both are "LLM rewriting", but they test different attackers.
2. **Headers.** In [3], SpamAssassin's misclassification of rewritten spam was 9.4% when the original headers were kept and 73.7% when they were cut to a minimum. Most of the headline number depends on removing header signal. We keep the headers in every version.
3. **Format.** [4] kept only sender, receiver, subject and body for original and rewritten emails alike, so its comparison seems to hold the format fixed. [3] does not say whether the rewritten body kept the original's HTML. Neither paper separates format from wording.
4. **Statistics and validity.** Neither [3] nor [4] reports confidence intervals, paired tests or a human meaning check.

## Sentence for the paper: what we add beyond [2]

On the abstract alone, the safe claim is that [2] measured machine-learning detectors and we test static, rule-based layers. The manuscript says this without implying that [2] lacked the other features: "Ferrell et al. [2] measured machine-learning detectors; we test static layers, including rule-based ones, with a neutral prompt, require every rewrite to keep its links and numbers, and separate the wording from the conversion to plain text."

Not known from the abstract, and needed before the sentence could be a direct contrast. Did [2]:
- named its three LLMs and its prompt;
- checked that rewrites kept links;
- tested any rule-based filter;
- held the email format fixed.

If [2] did none of these, the sentence could be a direct contrast ("Unlike [2], ...").

## Open questions

1. [2]: the full text, for every UNKNOWN cell above.
2. [3]: was SpamAssassin's Bayes database trained? An untrained Bayes adds nothing, which would make [3]'s filter closer to ours than its title suggests.
3. [4]: Tables I and III do not add up. Across the three conditions, TP and FP stay the same while TN and FN change. Since only phishing emails were rewritten, TP + FN (the number of phishing emails) should stay constant, but it does not: for Gmail on Nazario it is 584, then 614, then 690. We could not reconcile this from the text. Do not use [4]'s counts beyond the recall figures quoted above, and say "report" rather than "show".
4. [4]: were the original emails sent to Gmail and Proofpoint as received, or rebuilt from the four kept fields like the rewrites?

## Not verified

- Anything about [2] beyond its abstract.
- The repositories and datasets that [3] and [4] say they release (not opened).
- Later versions of [3] and [4] (only arXiv v1 was read). The arXiv comment on [3] mentions EAI ICDF2C 2024; the published version was not compared.
