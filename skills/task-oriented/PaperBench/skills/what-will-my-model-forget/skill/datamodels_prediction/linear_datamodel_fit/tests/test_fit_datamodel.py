import importlib.util
from pathlib import Path

script_path = Path(__file__).resolve().parents[1] / "scripts" / "fit_datamodel.py"
spec = importlib.util.spec_from_file_location("fit_datamodel", script_path)
fit_datamodel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fit_datamodel)


def test_fit_linear_datamodel_recovers_synthetic_outputs():
    true_weights = [0.5, -0.3, 0.8]
    x_matrix = [[1, 0, 1], [1, 1, 0], [0, 1, 1], [1, 1, 1], [0, 0, 1], [1, 0, 0]]
    y_values = [0.2 + sum(value * weight for value, weight in zip(row, true_weights)) for row in x_matrix]
    result = fit_datamodel.fit_linear_datamodel(x_matrix, y_values, ridge=1e-6)
    assert result["diagnostics"]["pearson"] > 0.999
    assert result["diagnostics"]["mse"] < 1e-8
    heldout = [[0, 1, 0], [1, 0, 1]]
    predictions = fit_datamodel.predict(heldout, result["weights"], result["intercept"])
    expected = [0.2 - 0.3, 0.2 + 0.5 + 0.8]
    assert fit_datamodel.mse(predictions, expected) < 1e-6


def test_non_binary_matrix_rejected():
    try:
        fit_datamodel.fit_linear_datamodel([[0.5, 1]], [1.0])
    except ValueError:
        return
    raise AssertionError("non-binary matrix should fail")


if __name__ == "__main__":
    test_fit_linear_datamodel_recovers_synthetic_outputs()
    test_non_binary_matrix_rejected()
