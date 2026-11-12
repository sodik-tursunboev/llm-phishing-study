"""Fill paper/manuscript.md's {{placeholders}} from result and config files: no number is typed by hand.

python -m src.paper.build   ->  paper/manuscript_filled.md, plus the word count and the list of
placeholders that have no value yet (they appear in the output as [MISSING name]).
"""
import csv
import json
import pathlib
import re

from src.data.prepare import REASONS

SOURCE = pathlib.Path("paper/manuscript.md")
OUTPUT = pathlib.Path("paper/manuscript_filled.md")


def _csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def values():
    v = {}
    sources = _csv("results/m1_sources.csv")
    for label in ("phishing", "ham"):
        rows = [r for r in sources if r["label"] == label]
        for column in ["read", "kept", *REASONS]:
            v[f"{label}_{column}"] = sum(int(r[column]) for r in rows)
    for r in _csv("results/m1_splits.csv"):
        v[f"{r['label']}_{r['split']}"] = int(r["messages"])
    l2 = json.loads(pathlib.Path("configs/tfidf_lr.json").read_text())
    v["l2_C"], v["l2_dev_auc"] = l2["C"], l2["dev_auc_by_C"][str(l2["C"])]
    thresholds = pathlib.Path("configs/thresholds.json")
    if thresholds.exists():
        for layer, t in json.loads(thresholds.read_text())["layers"].items():
            v[f"{layer}_threshold"] = round(t["threshold"], 2)
            v[f"{layer}_version"] = t["version"]
    pilot = json.loads(pathlib.Path("results/m3_pilot.json").read_text())
    v["lex_dose"] = f"{100 * pilot['change_fraction_passed']['median']:.1f}%"
    v["pilot_passed"] = pilot["gate_passed"]
    # Main results, once they exist: e.g. {{spamassassin_phishing_calibrated_llm_vs_null_a_net_pp}}
    primary = pathlib.Path("results/primary_test.csv")
    if primary.exists():
        for r in _csv(primary):
            prefix = "" if r["set"] == "gate_passed" else "all_"  # all_ = sensitivity on all rewrites
            key = f"{prefix}{r['layer']}_{r['class']}_{r['point']}_{r['contrast'].replace(' ', '_')}"
            v |= {f"{key}_{k}": r[k] for k in r if k not in ("layer", "set", "class", "point", "contrast")}
            # Ready-to-print forms: rates as %, the change with its sign, the interval in brackets.
            v[f"{key}_a_pct"] = f"{100 * float(r['rate_a']):.1f}%"
            v[f"{key}_b_pct"] = f"{100 * float(r['rate_b']):.1f}%"
            v[f"{key}_signed"] = f"{float(r['net_pp']):+.1f}"
            v[f"{key}_ci"] = f"[{float(r['ci_low_pp']):+.1f}, {float(r['ci_high_pp']):+.1f}]"
    selection = pathlib.Path("results/selection_test.csv")
    if selection.exists():
        for r in _csv(selection):
            v[f"sel_{r['label']}_{r['group']}_words"] = r["median_words"].removesuffix(".0")
            v[f"sel_{r['label']}_{r['group']}_urls"] = r["median_urls"].removesuffix(".0")
    accounting = pathlib.Path("results/accounting_test.csv")
    if accounting.exists():
        for r in _csv(accounting):
            if r["item"] == "email.social_engineering starts":
                v["lynceus_social_starts"] = f"{100 * float(r['mean_change']):.0f}%"
    if primary.exists():
        v["table_main"] = table_main()
    gates = pathlib.Path("results/gates_test.csv")
    if gates.exists():
        v["table_gates"] = table_gates()
        for r in _csv(gates):
            v |= {f"gates_{r['label']}_{k}": int(r[k]) for k in r if k != "label"}
        v["refusals"] = v["gates_phishing_refusal"] + v["gates_ham_refusal"]
        v["rewritten_total"] = v["gates_phishing_rewritten"] + v["gates_ham_rewritten"]
    ids = pathlib.Path("paper/authors.local.json")  # git-ignored: IDs reach the PDF, never the repository
    if ids.exists():
        v["student_ids"] = ", ".join(f"{a['name']} {a['student_id']}" for a in json.loads(ids.read_text())["authors"])
    judge = pathlib.Path("results/judge.json")
    if judge.exists():
        out = json.loads(judge.read_text())
        v["judge_equivalent_rate"] = f"{100 * out['equivalent_rate']:.0f}%"
        for q, s in out["questions"].items():
            v[f"judge_yes_{q}"] = f"{100 * s['final_yes_rate']:.0f}%"
        v["judge_checks"] = "; ".join(
            f"{name} checked {d['pairs_checked']} of {out['pairs']} pairs and changed {d['answers_changed']} "
            f"of {d['answers']} model answers" for name, d in out["checked_by"].items()) + "."
        if "entry" in out:  # names typed in on the checker's behalf
            v["judge_checks"] += (" The confirmation was entered into the sheet by Claude Code at the "
                                  "authors' request, because the checker could not save the file.")
    ratings = pathlib.Path("results/ratings.json")
    if ratings.exists():
        out = json.loads(ratings.read_text())
        v["ratings_equivalent_both"] = f"{100 * out['equivalent_both']:.0f}%"
        for q, s in out["questions"].items():
            v[f"kappa_{q}"], v[f"agreement_{q}"] = s["cohen_kappa"], f"{100 * s['agreement']:.0f}%"
    return v


LAYER_NAMES = {"spamassassin": "SpamAssassin", "tfidf_lr": "TF-IDF + LR", "lynceus": "Lynceus"}


def table_main():
    """Table 1: flag rate per condition (calibrated threshold, gate-passed pairs) and the primary change."""
    rows = [r for r in _csv("results/primary_test.csv") if r["set"] == "gate_passed" and r["point"] == "calibrated"]
    get = {(r["layer"], r["class"], r["contrast"]): r for r in rows}
    pct = lambda x: f"{100 * float(x):.1f}"  # noqa: E731
    out = ["| Layer | Class | n | orig | null-A | lex | llm | llm vs null-A (pp, 95% CI) | Holm p | Reading |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for layer, name in LAYER_NAMES.items():
        for cls, label in (("phishing", "phishing (detected)"), ("ham", "legitimate (flagged)")):
            fmt_ = get.get((layer, cls, "null_a vs orig"))
            llm, lex = get.get((layer, cls, "llm vs null_a")), get.get((layer, cls, "lex vs null_a"))
            if not (fmt_ and llm and lex):
                continue
            out.append(f"| {name} | {label} | {llm['n']} | {pct(fmt_['rate_a'])} | {pct(llm['rate_a'])} | "
                       f"{pct(lex['rate_b'])} | {pct(llm['rate_b'])} | {float(llm['net_pp']):+.1f} "
                       f"[{float(llm['ci_low_pp']):+.1f}, {float(llm['ci_high_pp']):+.1f}] | "
                       f"{llm['holm_p'] or '–'} | {llm['reading']} |")
    return "\n".join(out)


def table_gates():
    """Table 2: rewrites, gate passes and failures per class."""
    rows = _csv("results/gates_test.csv")
    gates = [k for k in rows[0] if k not in ("label", "rewritten", "passed")]
    out = ["| Class | Rewritten | Passed | " + " | ".join(gates) + " |", "|---|---|---|" + "---|" * len(gates)]
    for r in rows:
        name = "phishing" if r["label"] == "phishing" else "legitimate"
        out.append(f"| {name} | {r['rewritten']} | {r['passed']} | " + " | ".join(r[g] for g in gates) + " |")
    return "\n".join(out)


def fmt(value):
    return f"{value:,}" if isinstance(value, int) else str(value)


def main():
    text = re.sub(r"<!--.*?-->\s*", "", SOURCE.read_text(encoding="utf-8"), flags=re.S)  # drop notes to authors
    v = values()
    missing = sorted(set(re.findall(r"\{\{(\w+)\}\}", text)) - set(v))
    filled = re.sub(r"\{\{(\w+)\}\}", lambda m: fmt(v[m[1]]) if m[1] in v else f"[MISSING {m[1]}]", text)
    OUTPUT.write_text(filled, encoding="utf-8")
    body = filled.split("## Declarations")[0]  # abstract to discussion: what the 3,000-word guide counts
    prose = "\n".join(line for line in body.splitlines() if not line.lstrip().startswith("|"))  # tables aside
    print(f"{OUTPUT}: {len(filled.split())} words in all; title to discussion {len(body.split())}, "
          f"of which prose (tables excluded) {len(prose.split())}; missing: {', '.join(missing) or 'none'}")


if __name__ == "__main__":
    main()
