# Environment

Every stage runs in one Docker image (`Dockerfile`). Every stage except the corpus download runs with `--network none`, so experiments cannot reach the internet (README section 4). The network is used only to build the image and to download the corpora.

## Pinned versions (recorded 2026-11-11)

| Component | Version | Pinned by |
|---|---|---|
| Base image | `python:3.12-slim-bookworm` | digest `sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df` in `Dockerfile` |
| Python | 3.12.16 | base image digest |
| SpamAssassin | 4.0.1 (Debian package `4.0.1-1~deb12u1`), Perl 5.36.0 | exact package version in `Dockerfile` |
| SpamAssassin rules | as shipped in the package, `/usr/share/spamassassin` | no `sa-update` is run; `/var/lib/spamassassin` holds only signing keys |
| Python packages | scikit-learn 1.9.1, langdetect 1.0.9, pytest 9.2.0 and their dependencies | exact versions in `requirements.txt` |
| Corpus files | 16 files | SHA-256 in `configs/raw_files.csv` |
| Host used | Windows 11, Docker 29.9.2, git 2.55.0 | not pinned; only Docker is needed to reproduce |

## Lynceus snapshot (L4)

Lynceus is evaluated at commit `d9c3ba88f9b995d9079434d39ad8d977dbb49b05`. Only its `core/` and `rules/` folders are copied, into the Docker volume `lynceus-src`, mounted read-only at `/opt/lynceus`. The adapter refuses any other commit. Its Python dependencies are pinned in `requirements.txt`. Create the snapshot once (git 2.40 or later; run in `cmd` or bash, because PowerShell 5.1 corrupts binary pipes):

```bash
git -C <path-to-lynceus-repo> archive --add-virtual-file=COMMIT:d9c3ba88f9b995d9079434d39ad8d977dbb49b05 d9c3ba88f9b995d9079434d39ad8d977dbb49b05 core rules | docker run --rm -i -v lynceus-src:/opt/lynceus llm-phishing-study tar -x -C /opt/lynceus
```

## Where the data lives

The corpora live in a Docker volume, `llm-phishing-data`, mounted at `/work/data`. They never sit on the host disk. When `phishing3.mbox` was first saved to the Windows disk, Microsoft Defender quarantined it as `PWS:HTML/Bankfraud`, which is expected for real phishing. The volume lives inside Docker's Linux VM, so the phishing files never reach the host filesystem and stay behind the container boundary. We did not change any antivirus setting.

## Commands (run from the repository root; `${PWD}` works in PowerShell and bash)

Build the image (after any change to `Dockerfile` or `requirements.txt`):

```bash
docker build -t llm-phishing-study .
```

Download the corpora and verify their hashes (the only step with network):

```bash
docker run --rm -v "${PWD}:/work" -v llm-phishing-data:/work/data llm-phishing-study python -m src.data.download
```

Prepare the data offline: parse, scrub, filter, deduplicate, cluster, split (about 5 minutes):

```bash
docker run --rm --network none -v "${PWD}:/work" -v llm-phishing-data:/work/data llm-phishing-study python -m src.data.prepare
```

Fit and freeze L2 (train only; C chosen on dev; writes `configs/tfidf_lr.json` with the model hash):

```bash
docker run --rm --network none -v "${PWD}:/work" -v llm-phishing-data:/work/data llm-phishing-study python -m src.detectors.tfidf_lr
```

Score one split with one layer (`spamassassin`, `tfidf_lr` or `lynceus`), offline. It prints only counts, errors, runtime and the output hash:

```bash
docker run --rm --network none -v "${PWD}:/work" -v llm-phishing-data:/work/data -v lynceus-src:/opt/lynceus:ro llm-phishing-study python -m src.detectors.run lynceus test
```

Fix the dev-calibrated thresholds (after scoring dev with all three layers; writes `configs/thresholds.json`), then fill the manuscript's numbers from the result files:

```bash
docker run --rm --network none -v "${PWD}:/work" -v llm-phishing-data:/work/data llm-phishing-study python -m src.detectors.calibrate
docker run --rm --network none -v "${PWD}:/work" llm-phishing-study python -m src.paper.build
```

Rewrite with the local model (needs Ollama 0.34.4 on the host with `gemma3:4b` at the pinned digest; this container has network so it can reach the host's Ollama, DEVIATIONS.md #11). Then write the pilot report offline:

```bash
docker run --rm -v "${PWD}:/work" -v llm-phishing-data:/work/data llm-phishing-study python -m src.rewrite.generate pilot
docker run --rm --network none -v "${PWD}:/work" -v llm-phishing-data:/work/data llm-phishing-study python -m src.rewrite.pilot
```

Main run (M5). Generation stops when 200 rewrites per class pass the gates. Scoring of the conditions and the analysis run offline, and only after the freeze (PROTOCOL.md). The rating sheets go to `ratings/` (git-ignored); `kappa` reads them back once both authors have filled them in:

```bash
docker run --rm -v "${PWD}:/work" -v llm-phishing-data:/work/data llm-phishing-study python -m src.rewrite.generate test 200
docker run --rm --network none -v "${PWD}:/work" -v llm-phishing-data:/work/data -v lynceus-src:/opt/lynceus:ro llm-phishing-study python -m src.analysis.score spamassassin test
docker run --rm --network none -v "${PWD}:/work" -v llm-phishing-data:/work/data -v lynceus-src:/opt/lynceus:ro llm-phishing-study python -m src.analysis.primary test
docker run --rm --network none -v "${PWD}:/work" -v llm-phishing-data:/work/data llm-phishing-study python -m src.analysis.ratings make
```

(`score` runs once per layer: `spamassassin`, `tfidf_lr`, `lynceus`.)

Check command (all tests, offline):

```bash
docker run --rm --network none -v "${PWD}:/work" -v llm-phishing-data:/work/data -v lynceus-src:/opt/lynceus:ro llm-phishing-study python -m pytest -q -p no:cacheprovider
```

`tests/test_environment.py` proves the container has no network (only the loopback interface exists) and that SpamAssassin flags its GTUBE test message with local rules only. As a negative control, running the same command without `--network none` makes the network test fail. Without the data volume the raw-hash test is skipped; without the Lynceus volume the Lynceus tests are skipped.

Enable the secret/PII/data scan once per clone (uses host Python, standard library only):

```bash
git config core.hooksPath hooks
```

`hooks/scan.py` blocks a commit that stages anything under `data/`, `.eml`/`.mbox` files, private keys, common access tokens, email addresses (except reserved `example.com/org/net`) or international phone numbers. `tests/test_scan.py` checks it.

## Open questions

- Should the Ollama rewriting stage (M3) also run in a container? It needs a local network to the model server, unlike scoring.

## Not verified

- Debian dependencies of SpamAssassin (Perl modules) are not pinned individually; a later rebuild could pick up a Debian security update.
- SpamAssassin scores were checked to be independent of the run date in one diagnostic: re-scoring dev with Perl's clock set to 2040 changed no rule hit on any of 997 messages (2026-11-11). The script was not kept.
- The scan cannot recognise student IDs (format unknown) or names; authors must keep IDs out of the repo by hand.
- Not yet built or run on the co-author's machine. The hook was tested on Windows only (it blocked a staged file containing an email address); not yet on macOS or Linux.
