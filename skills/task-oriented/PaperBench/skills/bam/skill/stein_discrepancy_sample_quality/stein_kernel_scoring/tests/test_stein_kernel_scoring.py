import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "stein_kernel.py"
spec = importlib.util.spec_from_file_location("stein_kernel", SCRIPT)
stein_kernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stein_kernel)


def test_matrix_is_symmetric_and_finite():
    samples = [[-1.0], [0.0], [1.0], [2.0]]
    scores = [[1.0], [0.0], [-1.0], [-2.0]]
    matrix = stein_kernel.rbf_stein_kernel_matrix(samples, scores, bandwidth=1.2)
    assert len(matrix) == 4
    assert len(matrix[0]) == 4
    for i in range(4):
        for j in range(4):
            assert abs(matrix[i][j] - matrix[j][i]) < 1e-12


def test_u_statistic_excludes_diagonal():
    matrix = [[10.0, 1.0, 2.0], [3.0, 10.0, 4.0], [5.0, 6.0, 10.0]]
    assert abs(stein_kernel.ksd_u_statistic(matrix) - 3.5) < 1e-12
    assert abs(stein_kernel.ksd_v_statistic(matrix) - (51.0 / 9.0)) < 1e-12


def test_shifted_score_has_larger_ksd_than_matching_score():
    samples = [[-2.0 + i * 0.1] for i in range(41)]
    true_scores = [[-row[0]] for row in samples]
    shifted_model_scores = [[-(row[0] - 1.5)] for row in samples]
    null_matrix = stein_kernel.rbf_stein_kernel_matrix(samples, true_scores, bandwidth=1.0)
    alt_matrix = stein_kernel.rbf_stein_kernel_matrix(samples, shifted_model_scores, bandwidth=1.0)
    assert stein_kernel.ksd_v_statistic(alt_matrix) > stein_kernel.ksd_v_statistic(null_matrix) + 0.2
