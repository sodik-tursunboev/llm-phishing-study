"""The rewrite run refuses any Ollama version but the pinned one, at start and before every rewrite,
and records the version in every record (DEVIATIONS #19). A fake server stands in for Ollama; the
run writes into a temporary folder, never into the study's data."""
import json

import pytest

from src.rewrite import generate


def fake_server(versions):
    """An Ollama stand-in whose /api/version answers the given versions in turn (the last repeats)."""
    calls = iter(versions)
    last = [versions[-1]]

    def ollama(path, payload=None):
        if path == "/api/version":
            last[0] = next(calls, last[0])
            return {"version": last[0]}
        if path == "/api/tags":
            return {"models": [{"name": generate.MODEL, "digest": generate.DIGEST}]}
        return {"response": "Please send the report by Friday.", "done_reason": "stop",
                "eval_count": 7, "prompt_eval_count": 20}
    return ollama


def made_up(i, label):
    return {"id": f"m{i}", "label": label, "split": "x", "subject": "Report",
            "headers": [("From", "Alice <alice@example.org>"), ("Subject", "Report")],
            "text": "Please send the report on Friday.", "html": "", "urls": []}


@pytest.fixture
def run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # the run writes data/rewrites/ here, not in the study's volume
    msgs = [made_up(1, "phishing"), made_up(2, "ham"), made_up(3, "phishing")]
    monkeypatch.setattr(generate, "ordered", lambda split: msgs)

    def go(versions):
        monkeypatch.setattr(generate, "ollama", fake_server(versions))
        generate.main("x")
        out = tmp_path / "data" / "rewrites" / "llm_x.jsonl"
        return [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    return go, tmp_path


def test_the_pinned_version_runs_and_is_recorded(run):
    go, _ = run
    records = go(["0.34.4"])
    assert len(records) == 3 and all(r["ollama_version"] == "0.34.4" for r in records)


def test_another_version_is_refused_before_anything_is_written(run):
    go, tmp_path = run
    with pytest.raises(RuntimeError, match="0.40.16"):
        go(["0.40.16"])
    assert not (tmp_path / "data" / "rewrites" / "llm_x.jsonl").exists()


def test_an_update_mid_run_stops_the_run_and_keeps_what_was_written(run):
    go, tmp_path = run
    # start check, first rewrite, then the server reports a new version before the second rewrite
    with pytest.raises(RuntimeError, match="run stopped"):
        go(["0.34.4", "0.34.4", "0.40.16"])
    out = tmp_path / "data" / "rewrites" / "llm_x.jsonl"
    records = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [r["id"] for r in records] == ["m1"] and records[0]["ollama_version"] == "0.34.4"
