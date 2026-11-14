# AI use

The basis for the paper's *Declaration of Generative AI and AI-Assisted Technologies* (handbook p. 13). An earlier, session-by-session version of this log is kept in the repository's git history.

| Tool | What it did | What the authors did |
|---|---|---|
| Claude Code (Anthropic; Claude Opus 5.5, Claude Sonnet 5.5) | Wrote the data pipeline, detector adapters, analysis scripts and their tests to our specification; drafted and edited the documentation and the manuscript; found sources and opened their pages; typed our check results into the record files (the meaning-check sheet, the `verified_by` column). Lynceus, built before this study, was also written with its help. It never received email text, only counts and aggregates. | We read and checked everything by hand. Kavish verified every reference against its source and every reported number against the result files. Sodik ran every stage on Sodik's own machine. The tests run offline, and every number in the paper is filled from result files by `src/paper/build.py`. The assistant did not rate, judge or verify anything. |
| gemma3:4b, local through Ollama | Part of the experiment: produced the rewrites under study | Comparability gates on links, numbers, entities, length and language, plus the 30-pair meaning check |
| llama3.2:3b, local through Ollama | Part of the experiment: pre-filled the 30-pair meaning-check sheet | Kavish read all 30 pairs and checked every answer |

Every methodological decision was taken and approved by the authors: the question, the data, the detectors, the generator, the gates and the freeze. `DEVIATIONS.md` records each one.
