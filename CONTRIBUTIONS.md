# Contributions

Who did what in this study. A task is marked done only when it has happened; planned tasks say "planned". AI use is listed in `AI_LOG.md` and declared in the paper.

Kavish worked from Sodik's account, so every commit in this repository is under Sodik's name. Commit authorship therefore does not show who did a task; this table does.

| Who | Role | Contributions |
|---|---|---|
| **Sodik Tursunboev** | First author; runs the study | Set the research direction and scope (README brief, scope update v3); approved every gate (data licences, protocol freeze); chose the generator; ran the study on Sodik's own machine. **Designed and directed Lynceus (L4) before this study** (an AI assistant wrote its code and proposed its rules and weights, which Sodik approved; `LYNCEUS_NOTES.md` section 9), and directed its improvement before the freeze, without study data (DEVIATIONS.md #17). Planned: rewrite and verify the manuscript. |
| **Kavish Chaudhari** | Project partner, second author | **Checked the local model's judgments of the 30 rewrite pairs** (2026-11-12): read all 30 pairs and agreed with every pre-filled answer (DEVIATIONS.md #20, #22). **Verified all 19 cited references** against their sources (2026-11-13: the first 18, then the FBI IC3 report added that day as [1]), recorded in the `verified_by` column of `references/evidence_trail.csv`. **Checked every reported number against the result files** (2026-11-13). **Did not write Lynceus.** |
| AI assistant (Claude Code) | Tool, not an author | Wrote the code to the authors' specification, drafted and edited the documentation and manuscript, found sources and opened their pages, and typed the authors' check results into the record files. It did not rate, judge or verify anything (`AI_LOG.md`). |

**The 30-pair meaning check** (DEVIATIONS.md #20):
- A local model, `llama3.2:3b`, pre-fills the four answers for each pair.
- The `checked` column stays empty until a human has read the pair. The checker's name is then entered, by hand or, for a checker who agrees with every answer, with `python -m src.analysis.judge confirm`, which changes no answer.
- `python -m src.analysis.judge summary` refuses to run while any pair is unchecked.
- It records, per named person, how many pairs they checked and how many answers they changed. The paper reports exactly that.
