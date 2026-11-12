# Contributions

Who did what in this study. A task is marked done only when it has happened; planned tasks say "planned". AI use is listed in `AI_LOG.md` and declared in the paper.

| Who | Role | Contributions |
|---|---|---|
| **Sodik Tursunboev** | First author; runs the study | Set the research direction and scope (README brief, scope update v3); approved every gate (data licences, protocol freeze); chose the generator; ran the study on Sodik's own machine. **Authored Lynceus (L4) before this study** (`LYNCEUS_NOTES.md` section 9: designed and directed it, with Claude Code writing the code and rules), and improved it before the freeze without study data (DEVIATIONS.md #17). Planned: check the local model's judgments of the 30 pairs (DEVIATIONS.md #20), then rewrite and verify the manuscript. |
| **Kavish [surname]** | Project partner, second author | Planned (scope v3): after the draft, verify every reference and check each number against the result files. **Did not write Lynceus.** [AUTHORS: add Kavish's other contributions.] |
| Claude Code (Anthropic) | AI assistant, not an author | Wrote the study code, tests and documents under the authors' direction, and drafted the manuscript from result files (`AI_LOG.md`). It saw only counts, hashes and aggregates, never email text. It did not rate or verify anything on the authors' behalf. |

**The 30-pair meaning check** (DEVIATIONS.md #20):
- A local model, `llama3.2:3b`, pre-fills the four answers for each pair.
- The `checked` column stays empty until a human reads the pair and types their own name there.
- `python -m src.analysis.judge summary` refuses to run while any pair is unchecked.
- It records, per named person, how many pairs they checked and how many answers they changed. The paper reports exactly that.
