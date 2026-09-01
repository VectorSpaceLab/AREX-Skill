from harness_utils import mechanism_summary

def test_mechanism_summary_marks_reduced_not_full():
    summary=mechanism_summary(1.0, 0.5, 1.0)
    assert summary["reduced_training_executed"] is True
    assert summary["training_step_executed"] is False
    assert summary["optimizer_step_executed"] is True
