# Blind rating of the 30 pairs (both authors)

**Why.** The coordinator asked how the rewrites are shown to be comparable with their originals. Right now the only evidence besides the gates is a small model judge: it says only 30% of rewrites keep their category, and one author accepted every answer. Two independent human ratings with Cohen's kappa were the plan before that (README 5.3, DEVIATIONS #4), and they are reinstated (DEVIATIONS #25).

**Time.** About 2–3 hours each.

## Rules

1. **Rate alone.** Do not discuss pairs, show each other answers or open the other sheet until both of you are done.
2. **Do not open `ratings/sheet_model.csv`** (the model's answers) while rating. Kavish has already seen it for these pairs; the paper will say so.
3. **Rate from your own sheet only.** It shows the original and the rewrite, with no class label and no detector output.
4. **Answer every cell with `yes` or `no`.** Write anything unclear in `notes`.
5. **The AI assistant does not rate and must not see the sheets.** They hold phishing text, which never goes to a cloud service (README section 4).

## Steps

1. **Make the two sheets** (needs the data volume; offline). It writes `ratings/sheet_sodik.csv` and `ratings/sheet_kavish.csv` for the same 30 pairs as the model judge, and refuses to overwrite a sheet that already exists.

   ```bash
   docker run --rm --network none -v "${PWD}:/work" -v llm-phishing-data:/work/data llm-phishing-study python -m src.analysis.ratings make
   ```

2. **Each author fills in their own sheet.** In Excel, save it with "Save As → CSV UTF-8", keeping the name. The four answer columns are `same_action`, `same_target`, `same_urgency` and `same_label`.

3. **When both sheets are complete, compute the agreement.** It refuses while any answer is blank or not yes/no. It writes `results/ratings.json` with:
   - per question: agreement, Cohen's kappa with a 95% CI, each rater's yes-rate, and the pairs you disagree on;
   - how often the model judge agreed with each of you;
   - the SHA-256 of both sheets, so a reviewer can check them later.

   ```bash
   docker run --rm --network none -v "${PWD}:/work" -v llm-phishing-data:/work/data llm-phishing-study python -m src.analysis.ratings kappa
   ```

4. **Commit `results/ratings.json`.** The sheets stay out of git (they hold email text); keep them for reviewers. If Kavish can, Kavish fills in their own sheet and makes this commit from Kavish's own GitHub account, so the record shows Kavish's work directly.

5. **Only then talk through the disagreements.** Kappa is computed on your independent answers, before any discussion. Write the agreed answer in `notes` if you like; do not change the answer cells after step 3.

6. **Put the result into the paper.** It belongs in Methods 3.3, Results 4.1, the comparability paragraph in 5.1, the limitations, and DEVIATIONS #25.

## What each question means

These are the questions printed in the sheet.

- **same_action:** does the rewrite ask the reader to do the same thing (click the same link, log in, reply, call, pay)?
- **same_target:** same sender or brand, links, names, placeholders such as `[NAME]`, and numbers?
- **same_urgency:** same level of urgency or pressure (deadlines, threats, warnings)? A clearly softer or stronger tone is `no`.
- **same_label:** would a careful reader still put the rewrite in the same category as the original (phishing stays phishing, legitimate stays legitimate)? Judge the category from the original text; the sheet does not say which class it came from.
