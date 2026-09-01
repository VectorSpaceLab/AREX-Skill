import math

from binary_nce import (
    binary_objective,
    build_section_4_3_protocol,
    run_binary_diagnostic,
    section_4_3_binary_limit,
    section_4_3_score_from_params,
    self_normalization_report,
)


def test_binary_limit_matches_paper_counterexample():
    limit = section_4_3_binary_limit()
    assert math.isclose(limit["ratio_x1"], 3.0 / 7.0)
    assert not math.isclose(limit["ratio_x1"], limit["true_ratio_x1"])


def test_binary_objective_and_self_normalization_report():
    protocol = build_section_4_3_protocol(k_negatives=2)
    score_fn = section_4_3_score_from_params({"log_theta1": 0.0, "log_theta2": math.log(3.0)})
    assert binary_objective(protocol, score_fn, offset=0.0) < 0.0
    report = self_normalization_report()
    assert report["constant_partition"] is False
    assert math.isclose(report["partition_range"], 2.0)
    diagnostic = run_binary_diagnostic(k_negatives=2)
    assert diagnostic["binary_ratio_error_against_true"] > 0.09


def test_self_normalization_report_accepts_equal_partitions():
    report = self_normalization_report(theta1=3.0, theta2=3.0)
    assert report["constant_partition"] is True
    assert math.isclose(report["partition_range"], 0.0)
