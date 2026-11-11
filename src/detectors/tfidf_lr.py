"""L2: a frozen TF-IDF + logistic-regression text classifier, behind the common detector interface.

It reads what a person reads: the subject plus the visible body text (HTML markup is dropped, so
the model cannot simply learn "HTML means phishing"). It is fit on the train split only; its one
hyperparameter, the regularisation strength C, is chosen on dev; then the model file is frozen
and its SHA-256 recorded in configs/tfidf_lr.json (README section 5.4).

python -m src.detectors.tfidf_lr      fits, selects and freezes the model (offline, deterministic)
"""
import hashlib
import json
import pathlib
import pickle

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline

from src.data.emails import body_text

MODEL = pathlib.Path("data/models/tfidf_lr.pkl")
CONFIG = pathlib.Path("configs/tfidf_lr.json")
GRID_C = [0.1, 1.0, 10.0, 100.0]


def text(msg):
    return msg["subject"] + "\n" + body_text(msg)


def _split(name):
    with open("data/messages.jsonl", encoding="utf-8") as f:
        rows = [m for m in map(json.loads, f) if m["split"] == name]
    return [text(m) for m in rows], np.array([m["label"] == "phishing" for m in rows], dtype=int)


def fit():
    (x_train, y_train), (x_dev, y_dev) = _split("train"), _split("dev")
    results = {}
    for c in GRID_C:
        model = make_pipeline(
            TfidfVectorizer(sublinear_tf=True, min_df=2, ngram_range=(1, 2)),
            LogisticRegression(C=c, max_iter=5000),
        ).fit(x_train, y_train)
        results[c] = (roc_auc_score(y_dev, model.decision_function(x_dev)), model)
    best_c = max(GRID_C, key=lambda c: (results[c][0], -c))  # highest dev AUC; ties go to smaller C
    best = results[best_c][1]
    # _stop_words_id caches a memory address (id()), the only part of the fitted model that differs
    # between runs; scikit-learn reads it with a default, so dropping it makes the file reproducible.
    del best.named_steps["tfidfvectorizer"]._stop_words_id
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    MODEL.write_bytes(pickle.dumps(best))
    config = {
        "C": best_c,
        "dev_auc_by_C": {str(c): round(results[c][0], 4) for c in GRID_C},
        "n_train": {"phishing": int(y_train.sum()), "ham": int(len(y_train) - y_train.sum())},
        "model_sha256": hashlib.sha256(MODEL.read_bytes()).hexdigest(),
    }
    CONFIG.write_text(json.dumps(config, indent=2) + "\n")
    print(config)


_model, _names = None, None


def _load():
    """Load the frozen model, refusing any file whose hash differs from the recorded one."""
    global _model, _names
    expected = json.loads(CONFIG.read_text())["model_sha256"]
    blob = MODEL.read_bytes()
    if hashlib.sha256(blob).hexdigest() != expected:
        raise RuntimeError("data/models/tfidf_lr.pkl does not match configs/tfidf_lr.json")
    _model = pickle.loads(blob)  # our own file, verified by hash just above
    _names = _model.named_steps["tfidfvectorizer"].get_feature_names_out()


def score(msg):
    """Common interface. score = logit (log-odds of phishing); flagged at probability 0.5 (logit 0)."""
    if _model is None:
        _load()
    vectorizer, classifier = _model.named_steps.values()
    x = vectorizer.transform([text(msg)])
    logit = float(classifier.decision_function(x)[0])
    # Per-token contribution = TF-IDF weight x coefficient; the logit is their sum plus the intercept.
    contributions = x.multiply(classifier.coef_).tocoo()
    top = sorted(zip(contributions.col, contributions.data), key=lambda t: -abs(t[1]))[:10]
    return {
        "score": logit,
        "flagged": logit >= 0,
        "evidence": {_names[i]: round(float(v), 6) for i, v in top},
        "error": None,
        "version": f"tfidf_lr C={classifier.C}",
        "config_hash": json.loads(CONFIG.read_text())["model_sha256"],
    }


if __name__ == "__main__":
    fit()
