# Contributions

Who did what in this study. A task is marked done only when it has happened; planned tasks say "planned". AI use is listed in `AI_LOG.md` and declared in the paper.

| Who | Role | Contributions |
|---|---|---|
| **Sodik Tursunboev** | First author; runs the study | Set the research direction and scope (README brief, scope update v3); approved every gate (data licences, protocol freeze); chose the generator; ran the study on Sodik's own machine. **Authored Lynceus (L4) before this study** (`LYNCEUS_NOTES.md` section 9: designed and directed it, with AI assistance for the code and rules), and improved it before the freeze without study data (DEVIATIONS.md #17). Planned: rewrite and verify the manuscript. |
| **Kavish Chaudhari** | Project partner, second author | **Checked the local model's judgments of the 30 rewrite pairs** (2026-11-12): read all 30 and agreed with every pre-filled answer. Kavish could not save the sheet, so the confirmation was entered at the authors' request (DEVIATIONS.md #20, #22). **Verified all 19 cited references** (2026-11-13: the first 18, then the FBI IC3 report added that day as [1]; Kavish was unavailable to edit the file, so the `verified_by` entries in `references/evidence_trail.csv` were filled in at the authors' request). **Checked the reported numbers against the result files** (2026-11-13, reported by the authors). **Did not write Lynceus.** [AUTHORS: add Kavish's other contributions.] |
| AI assistant | Tool, not an author | Programming and writing assistance, declared in the paper and summarised in `AI_LOG.md`. |

**The 30-pair meaning check** (DEVIATIONS.md #20):
- A local model, `llama3.2:3b`, pre-fills the four answers for each pair.
- The `checked` column stays empty until a human reads the pair and types their own name there.
- `python -m src.analysis.judge summary` refuses to run while any pair is unchecked.
- It records, per named person, how many pairs they checked and how many answers they changed. The paper reports exactly that.
