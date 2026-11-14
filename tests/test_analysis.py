"""Statistics checks on made-up numbers whose answers are known."""
import pytest

from src.analysis.stats import Z95, cluster_bootstrap_ci, holm, mcnemar_exact, paired_score_ci, wilson_ci


def test_mcnemar_exact():
    assert mcnemar_exact(0, 0) == 1.0
    assert mcnemar_exact(5, 5) == 1.0
    assert mcnemar_exact(10, 0) == pytest.approx(2 * 0.5**10)  # two-sided binomial tail


def test_cluster_bootstrap_ci_contains_the_mean_and_is_deterministic():
    diffs = [-1, -1, 0, 0, 0, -1, 0, 0, -1, 0] * 10
    clusters = [f"c{i // 2}" for i in range(100)]
    low, high = cluster_bootstrap_ci(diffs, clusters)
    assert low < -0.4 < high and (low, high) == cluster_bootstrap_ci(diffs, clusters)
    assert cluster_bootstrap_ci([0] * 10, list(range(10))) == (0.0, 0.0)


def test_margin_reading_follows_the_protocol_order():
    from src.analysis.primary import reading

    assert reading(-5.0, -0.5) == "change"
    assert reading(0.2, 1.5) == "change"  # excludes 0 comes first, even inside the margin
    assert reading(-1.5, 1.8) == "no change larger than 2 pp"
    assert reading(-4.0, 1.0) == "inconclusive"


def test_intervention_edit_changes_only_listed_words_and_never_links():
    from src.analysis.intervention import edit

    text = "Verify your account at http://example.com/verify today. Account closure follows."
    out = edit(text, ["verify", "account"])
    assert "http://example.com/verify" in out and "today" in out
    assert "Verify" not in out.replace("http://example.com/verify", "") and "account" not in out.lower().replace(
        "http://example.com/verify", "")


def test_judge_answers_are_yes_no_or_left_blank():
    from src.analysis.judge import parse

    assert parse('{"same_action": "Yes", "same_target": "no", "same_urgency": "yes", "same_label": "yes"}') == {
        "same_action": "yes", "same_target": "no", "same_urgency": "yes", "same_label": "yes"}
    assert parse('{"same_action": "maybe"}') == {"same_action": "", "same_target": "", "same_urgency": "",
                                                 "same_label": ""}
    assert set(parse("not json").values()) == {""}


def test_only_an_author_name_counts_as_checked():
    from src.analysis.judge import checker

    assert checker("Sodik") == "Sodik Tursunboev" and checker(" kavish ") == "Kavish Chaudhari"
    assert checker("") is None and checker("yes") is None and checker("someone else") is None


def test_holm():
    assert holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])


def test_wilson_ci_at_zero_has_its_closed_form_upper_limit():
    low, high = wilson_ci(0, 200)
    assert low == pytest.approx(0, abs=1e-12) and high == pytest.approx(Z95**2 / (200 + Z95**2))


def test_paired_score_ci_does_not_collapse_without_discordant_pairs():
    # Nothing flagged under either condition: the bootstrap gives [0, 0]; this interval is
    # symmetric with the width of a Wilson interval at 0 of 200 (about 1.9 points each side).
    low, high = paired_score_ci(0, 0, 0, 200)
    assert high == pytest.approx(Z95**2 / (200 + Z95**2)) and low == pytest.approx(-high)


def test_paired_score_ci_contains_the_change_and_flips_with_the_direction():
    low, high = paired_score_ci(31, 0, 1, 168)  # one gained detection out of 200
    assert low < 0.005 < high and high - low > 0.02
    assert paired_score_ci(31, 1, 0, 168) == pytest.approx((-high, -low))
    low, high = paired_score_ci(59, 0, 9, 132)  # nine gained, none lost: clearly a change
    assert low > 0


def test_decomposition_steps_add_up_and_the_table_is_rebuilt_from_the_row():
    from src.analysis.exact import decomposition_rows, table

    def row(contrast, rate_a, rate_b, lost, gained):
        return {"layer": "x", "set": "gate_passed", "class": "phishing", "point": "native", "n": "200",
                "excluded_errors": "0", "contrast": contrast, "rate_a": str(rate_a), "rate_b": str(rate_b),
                "lost": str(lost), "gained": str(gained)}

    canon, wording = row("null_a vs orig", 0.55, 0.295, 51, 0), row("llm vs null_a", 0.295, 0.34, 0, 9)
    assert table(wording) == (59, 0, 9, 132)
    [out] = decomposition_rows([canon, wording])
    assert (out["canonicalization_pp"], out["wording_pp"], out["end_to_end_pp"]) == (-25.5, 4.5, -21.0)
