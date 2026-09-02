from posterior_two_sample_metrics import compute_metrics


def test_identical_samples_are_near_chance():
    reference = [[float(i)] for i in range(12)]
    metrics = compute_metrics(reference, [row[:] for row in reference])
    assert metrics["c2st_accuracy"] <= 0.6
    assert "closer to chance-level 0.5 is better" in metrics["interpretation"]


def test_shifted_samples_are_easier_to_classify():
    reference = [[float(i) / 10.0] for i in range(20)]
    shifted = [[row[0] + 2.0] for row in reference]
    same = compute_metrics(reference, [row[:] for row in reference])
    different = compute_metrics(reference, shifted)
    assert different["c2st_accuracy"] > same["c2st_accuracy"]
    assert different["c2st_distance_to_ideal"] > same["c2st_distance_to_ideal"]
    assert different["mmd2"] > 0.0
