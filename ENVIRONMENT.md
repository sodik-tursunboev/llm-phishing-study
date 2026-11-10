# Environment

Every stage runs in one Docker image (`Dockerfile`) started with `--network none`, so experiments cannot reach the internet (README section 4). The network is used only while building the image.

## Pinned versions (recorded 2026-11-11)

| Component | Version | Pinned by |
|---|---|---|
| Base image | `python:3.12-slim-bookworm` | digest `sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df` in `Dockerfile` |
| Python | 3.12.16 | base image digest |
| SpamAssassin | 4.0.1 (Debian package `4.0.1-1~deb12u1`), Perl 5.36.0 | exact package version in `Dockerfile` |
| SpamAssassin rules | as shipped in the package, `/usr/share/spamassassin` | no `sa-update` is run; `/var/lib/spamassassin` holds only signing keys |
| Python packages | `requirements.txt` | exact versions, including dependencies |
| Host used at M0 | Windows 11, Docker 29.9.2, git 2.55.0 | not pinned; only Docker is needed to reproduce |

## Commands (run from the repository root)

Build the image once:

```bash
docker build -t llm-phishing-study:m0 .
```

Check command (all tests, offline):

```bash
docker run --rm --network none -v "${PWD}:/work" llm-phishing-study:m0 python -m pytest -q -p no:cacheprovider
```

`tests/test_environment.py` proves the container has no network (only the loopback interface exists) and that SpamAssassin flags its GTUBE test message with local rules only. As a negative control, running the same command without `--network none` makes the network test fail.

Enable the secret/PII/data scan once per clone (uses host Python, standard library only):

```bash
git config core.hooksPath hooks
```

`hooks/scan.py` blocks a commit that stages anything under `data/`, `.eml`/`.mbox` files, private keys, common access tokens, email addresses (except reserved `example.com/org/net`) or international phone numbers. `tests/test_scan.py` checks it.

## Open questions

- Should the Ollama rewriting stage (M3) also run in a container? It needs a local network to the model server, unlike scoring.

## Not verified

- Debian dependencies of SpamAssassin (Perl modules) are not pinned individually; a later rebuild could pick up a Debian security update. The image ID built at M0 was `sha256:0a386709f0b1429b070997031d0ce3b7fad225eae0bc23a1baf00e4bb5fbd54e`.
- The scan cannot recognise student IDs (format unknown) or names; authors must keep IDs out of the repo by hand.
- Not yet built or run on the co-author's machine. The hook was tested on Windows only (it blocked a staged file containing an email address); not yet on macOS or Linux.
