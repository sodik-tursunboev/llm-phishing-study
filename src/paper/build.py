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
        v[f"{r['label']}_{r['split']}_pct_html"] = f"{float(r['pct_html']):.0f}%"
    l2 = json.loads(pathlib.Path("configs/tfidf_lr.json").read_text())
    v["l2_C"] = int(l2["C"]) if float(l2["C"]).is_integer() else l2["C"]  # "C = 100", not "100.0"
    v["l2_dev_auc"] = l2["dev_auc_by_C"][str(l2["C"])]
    thresholds = pathlib.Path("configs/thresholds.json")
    if thresholds.exists():
        for layer, t in json.loads(thresholds.read_text())["layers"].items():
            v[f"{layer}_threshold"] = round(t["threshold"], 2)
            v[f"{layer}_version"] = t["version"]
        v["spamassassin_version_number"] = v["spamassassin_version"].split()[1]  # "SpamAssassin 4.0.1 scoreset 0"
        v["lynceus_commit"] = v["lynceus_version"].split()[1][:7]  # "lynceus ac2a5af9b4f2 email-... rules ..."
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
            v[f"{key}_shift"] = f"{float(r['score_shift']):+.2f}"  # mean paired score change, threshold-free
            v[f"{key}_shift_ci"] = f"[{float(r['shift_ci_low']):+.2f}, {float(r['shift_ci_high']):+.2f}]"
    exact = pathlib.Path("results/exact_test.csv")
    if exact.exists():  # paired score intervals, a check on the bootstrap (src/analysis/exact.py)
        for r in _csv(exact):
            prefix = "" if r["set"] == "gate_passed" else "all_"
            key = f"{prefix}{r['layer']}_{r['class']}_{r['point']}_{r['contrast'].replace(' ', '_')}"
            v[f"{key}_exact_ci"] = f"[{float(r['exact_low_pp']):+.1f}, {float(r['exact_high_pp']):+.1f}]"
    decomposition = pathlib.Path("results/decomposition_test.csv")
    if decomposition.exists():  # llm vs orig = canonicalization step + wording step
        for r in _csv(decomposition):
            prefix = "" if r["set"] == "gate_passed" else "all_"
            key = f"{prefix}{r['layer']}_{r['class']}_{r['point']}_llm_vs_orig"
            v[f"{key}_a_pct"] = f"{float(r['orig_pct']):.1f}%"
            v[f"{key}_b_pct"] = f"{float(r['llm_pct']):.1f}%"
            v[f"{key}_signed"] = f"{float(r['end_to_end_pp']):+.1f}"
    selection = pathlib.Path("results/selection_test.csv")
    if selection.exists():
        for r in _csv(selection):
            v[f"sel_{r['label']}_{r['group']}_words"] = r["median_words"].removesuffix(".0")
            v[f"sel_{r['label']}_{r['group']}_urls"] = r["median_urls"].removesuffix(".0")
    accounting = pathlib.Path("results/accounting_test.csv")
    if accounting.exists():
        for r in _csv(accounting):
            if r["layer"] == "spamassassin":  # mean change in rule points per message, e.g. acct_spamassassin_XPRIO
                v[f"acct_spamassassin_{r['item']}"] = f"{float(r['mean_change']):+.2f}"
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
    canonical = pathlib.Path("results/canonical_test.json")
    if canonical.exists():  # what orig -> null-A changes (src/analysis/canonical.py)
        for label, stats in json.loads(canonical.read_text()).items():
            for k, x in stats.items():
                v[f"canon_{label}_{k}"] = f"{x:g}%" if k.startswith("pct") else f"{x:g}"
    ids = pathlib.Path("paper/authors.local.json")  # git-ignored: IDs reach the PDF, never the repository
    if ids.exists():
        v["student_ids"] = ", ".join(f"{a['name']} (ID {a['student_id']})" for a in json.loads(ids.read_text())["authors"])
    else:  # a reviewer's build: names without IDs
        v["student_ids"] = "Sodik Tursunboev, Kavish Chaudhari"
    judge = pathlib.Path("results/judge.json")
    if judge.exists():
        out = json.loads(judge.read_text())
        v["judge_equivalent_rate"] = f"{100 * out['equivalent_rate']:.0f}%"
        for q, s in out["questions"].items():
            v[f"judge_yes_{q}"] = f"{100 * s['final_yes_rate']:.0f}%"
        v["judge_checks"] = "; ".join(
            f"{name} checked {d['pairs_checked']} of {out['pairs']} pairs and changed {d['answers_changed']} "
            f"of {d['answers']} model answers" for name, d in out["checked_by"].items()) + "."
        # How the checker's names reached the sheet is recorded in results/judge.json ("entry") and
        # DEVIATIONS.md #22; the paper states who checked what.
    ratings = pathlib.Path("results/ratings.json")
    if ratings.exists():
        out = json.loads(ratings.read_text())
        v["ratings_equivalent_both"] = f"{100 * out['equivalent_both']:.0f}%"
        for q, s in out["questions"].items():  # the blind two-author rating (src/analysis/ratings.py)
            v[f"kappa_{q}"], v[f"agreement_{q}"] = s["cohen_kappa"], f"{100 * s['agreement']:.0f}%"
            if s.get("kappa_ci"):
                v[f"kappa_ci_{q}"] = f"[{s['kappa_ci'][0]:.2f}, {s['kappa_ci'][1]:.2f}]"
    return v


def minus(text):
    """Typographic minus sign for negative numbers ("−25.5", not "-25.5"); hyphens inside words stay."""
    return re.sub(r"(?<![\w-])-(?=\d)", "\u2212", text)


LAYER_NAMES = {"spamassassin": "SpamAssassin", "tfidf_lr": "TF-IDF", "lynceus": "Lynceus"}
READING = {"no change larger than 2 pp": "within ±2 pp"}  # the paper's reading rule, shortened for the table


def table_main():
    """Table 1: flag rate per condition (calibrated threshold, gate-passed pairs) and the primary change."""
    rows = [r for r in _csv("results/primary_test.csv") if r["set"] == "gate_passed" and r["point"] == "calibrated"]
    get = {(r["layer"], r["class"], r["contrast"]): r for r in rows}
    pct = lambda x: f"{100 * float(x):.1f}"  # noqa: E731
    out = ["| Layer | Class | *n* | orig | null-A | lex | llm | llm vs null-A (pp, 95% CI) | Holm *p* | Reading |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for layer, name in LAYER_NAMES.items():
        for cls, label in (("phishing", "phishing"), ("ham", "legitimate")):
            fmt_ = get.get((layer, cls, "null_a vs orig"))
            llm, lex = get.get((layer, cls, "llm vs null_a")), get.get((layer, cls, "lex vs null_a"))
            if not (fmt_ and llm and lex):
                continue
            out.append(f"| {name} | {label} | {llm['n']} | {pct(fmt_['rate_a'])} | {pct(llm['rate_a'])} | "
                       f"{pct(lex['rate_b'])} | {pct(llm['rate_b'])} | {float(llm['net_pp']):+.1f} "
                       f"[{float(llm['ci_low_pp']):+.1f}, {float(llm['ci_high_pp']):+.1f}] | "
                       f"{llm['holm_p'] or '–'} | {READING.get(llm['reading'], llm['reading'])} |")
    return "\n".join(out)


def table_gates():
    """Table 2: rewrites, gate passes and failures per class."""
    rows = _csv("results/gates_test.csv")
    names = {"refusal": "Refusal", "meta_text": "Meta-text", "urls": "Links", "numbers": "Numbers",
             "entities": "Entities", "length": "Length", "language": "Language",
             "not_rewritten_too_long": "Too long"}
    gates = [k for k in rows[0] if k not in ("label", "rewritten", "passed")]
    out = ["| Class | Rewritten | Passed | " + " | ".join(names.get(g, g) for g in gates) + " |",
           "|---|---|---|" + "---|" * len(gates)]
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
    filled = re.sub(r"\{\{(\w+)\}\}", lambda m: minus(fmt(v[m[1]])) if m[1] in v else f"[MISSING {m[1]}]", text)
    OUTPUT.write_text(filled, encoding="utf-8")
    body = filled.split("## Declarations")[0]  # title to conclusion: what the 3,000-word limit counts
    prose = "\n".join(line for line in body.splitlines() if not line.lstrip().startswith("|"))  # tables aside
    print(f"{OUTPUT}: {words(filled)} words in all; title to conclusion {words(body)} (limit 3,000, "
          f"tables included), of which prose {words(prose)}; missing: {', '.join(missing) or 'none'}")


def words(text):
    """Words as a reader counts them: tokens with a letter or digit, so table pipes, list dashes and
    heading marks are not counted."""
    return sum(bool(re.search(r"[^\W_]", token)) for token in text.split())


if __name__ == "__main__":
    main()
