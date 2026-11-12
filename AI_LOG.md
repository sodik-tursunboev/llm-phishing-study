# AI use

The basis for the paper's *Declaration of Generative AI and AI-Assisted Technologies* (handbook p. 13). An earlier, session-by-session version of this log is kept in the repository's git history.

| Tool | What it was used for | How we checked it |
|---|---|---|
| Claude Code (Anthropic; Claude Opus 5.5, Claude Sonnet 5.5) | Programming and writing assistant: helping write and test the data pipeline, detector adapters and analysis scripts; finding and opening sources; drafting and editing text. Lynceus, built before this study, was also written with its help. | Every script is covered by tests (48, run offline). Every number in the paper is filled from result files by `src/paper/build.py`. Every reference was opened on its official page (`references/evidence_trail.csv`). The assistant never received email text, only counts and aggregates. |
| gemma3:4b, local through Ollama | Part of the experiment: produced the rewrites under study | Comparability gates on links, numbers, entities, length and language, plus the 30-pair meaning check |
| llama3.2:3b, local through Ollama | Part of the experiment: pre-filled the 30-pair meaning-check sheet | Kavish read all 30 pairs and checked the answers |

Every methodological decision was taken and approved by the authors: the question, the data, the detectors, the generator, the gates and the freeze. `DEVIATIONS.md` records each one.
