#!/usr/bin/env python3
"""Tiny CPU-only ART evaluation/certification smoke.

This script uses synthetic data only. It exercises robustness/privacy metrics,
SecurityCurve and GREAT score evaluation objects, tree verification, and import /
signature checks for certification wrappers without downloading datasets.
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import sys
import warnings
from pathlib import Path

import numpy as np

if (Path.cwd() / "art" / "__init__.py").exists():
    sys.path.insert(0, str(Path.cwd()))


def _one_hot(labels: np.ndarray, nb_classes: int) -> np.ndarray:
    encoded = np.zeros((labels.size, nb_classes), dtype=np.float32)
    encoded[np.arange(labels.size), labels] = 1.0
    return encoded


def build_pytorch_classifier():
    import torch

    from art.estimators.classification.pytorch import PyTorchClassifier

    torch.manual_seed(1234)

    model = torch.nn.Linear(2, 2)
    with torch.no_grad():
        model.weight.copy_(torch.tensor([[1.6, -1.1], [-1.2, 1.4]], dtype=torch.float32))
        model.bias.copy_(torch.tensor([0.05, -0.05], dtype=torch.float32))

    loss = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

    return PyTorchClassifier(
        model=model,
        loss=loss,
        optimizer=optimizer,
        input_shape=(2,),
        nb_classes=2,
        clip_values=(0.0, 1.0),
        channels_first=True,
        device_type="cpu",
    )


def build_tree_data():
    x_train = np.array(
        [
            [0.05, 0.10],
            [0.15, 0.20],
            [0.80, 0.85],
            [0.90, 0.70],
        ],
        dtype=np.float32,
    )
    y_train_idx = np.array([0, 0, 1, 1], dtype=np.int64)
    y_train = _one_hot(y_train_idx, 2)

    x_test = np.array(
        [
            [0.20, 0.85],
            [0.85, 0.25],
        ],
        dtype=np.float32,
    )
    y_test_idx = np.array([1, 0], dtype=np.int64)
    y_test = _one_hot(y_test_idx, 2)

    return x_train, y_train_idx, y_train, x_test, y_test


def build_tree_classifiers():
    from sklearn.tree import DecisionTreeClassifier

    from art.estimators.classification.scikitlearn import ScikitlearnDecisionTreeClassifier

    x_train, y_train_idx, y_train, x_test, y_test = build_tree_data()

    tree_model = DecisionTreeClassifier(max_depth=2, random_state=0)
    tree_classifier = ScikitlearnDecisionTreeClassifier(model=tree_model, clip_values=(0.0, 1.0))
    tree_classifier.fit(x_train, y_train)

    extra_tree_model = DecisionTreeClassifier(max_depth=2, random_state=1)
    extra_tree_classifier = ScikitlearnDecisionTreeClassifier(model=extra_tree_model, clip_values=(0.0, 1.0))
    extra_tree_classifier.fit(x_train, y_train)

    return tree_classifier, extra_tree_classifier, x_train, y_train, x_test, y_test


def build_tree_verification_classifier():
    from sklearn.ensemble import RandomForestClassifier

    from art.estimators.classification.scikitlearn import ScikitlearnRandomForestClassifier

    x_train, y_train_idx, _, x_test, y_test = build_tree_data()

    model = RandomForestClassifier(n_estimators=2, max_depth=2, random_state=0)
    model.fit(x_train, y_train_idx)

    classifier = ScikitlearnRandomForestClassifier(model=model, clip_values=(0.0, 1.0))
    return classifier, x_test, y_test


def run_metric_smoke() -> dict[str, object]:
    from art.evaluations.great_score import GreatScorePyTorch
    from art.evaluations.security_curve import SecurityCurve
    from art.metrics import adversarial_accuracy, loss_gradient_check, loss_sensitivity, wasserstein_distance

    classifier = build_pytorch_classifier()
    x = np.array(
        [
            [0.10, 0.90],
            [0.90, 0.10],
            [0.20, 0.20],
            [0.80, 0.80],
        ],
        dtype=np.float32,
    )
    y_idx = np.argmax(classifier.predict(x), axis=1)
    y = _one_hot(y_idx, 2)

    adv_acc = adversarial_accuracy(
        classifier,
        x,
        y,
        attack_name="fgsm",
        attack_params={"eps": 0.05, "eps_step": 0.05, "batch_size": 2},
    )
    assert 0.0 <= adv_acc <= 1.0

    loss_sens = loss_sensitivity(classifier, x, y)
    assert loss_sens >= 0.0

    grad_flags = loss_gradient_check(classifier, x, y, verbose=False)
    assert grad_flags.shape == (x.shape[0], 3)
    assert grad_flags.dtype == bool

    sec = SecurityCurve(eps=[0.05])
    eps_list, adv_list, benign_acc = sec.evaluate(
        classifier=classifier,
        x=x,
        y=y,
        eps_step=0.05,
        max_iter=2,
        batch_size=2,
        num_random_init=0,
        summary_writer=False,
    )
    assert eps_list == [0.05]
    assert len(adv_list) == 1
    assert 0.0 <= benign_acc <= 1.0
    assert isinstance(sec.detected_obfuscating_gradients, bool)

    score, accuracy = GreatScorePyTorch(classifier=classifier).evaluate(x=x, y=y)
    assert np.isfinite(score)
    assert 0.0 <= accuracy <= 1.0

    wd = wasserstein_distance(x[:2], x[:2])
    np.testing.assert_array_equal(wd, np.zeros_like(wd))

    return {
        "adversarial_accuracy": float(adv_acc),
        "loss_sensitivity": float(loss_sens),
        "grad_flags_shape": tuple(int(dim) for dim in grad_flags.shape),
        "security_curve_eps": [float(value) for value in eps_list],
        "security_curve_adv": [float(value) for value in adv_list],
        "security_curve_benign": float(benign_acc),
        "security_curve_obfuscating": bool(sec.detected_obfuscating_gradients),
        "great_score": float(score),
        "great_accuracy": float(accuracy),
        "wasserstein_distance": [float(value) for value in wd.tolist()],
    }


def run_privacy_smoke() -> dict[str, object]:
    from art.metrics import ComparisonType, PDTP, SHAPr

    tree_classifier, extra_tree_classifier, x_train, y_train, x_test, y_test = build_tree_classifiers()

    shapr = SHAPr(tree_classifier, x_train, y_train, x_test, y_test)
    assert shapr.shape == (x_train.shape[0],)
    assert np.isfinite(shapr).all()

    avg, worst, std = PDTP(
        tree_classifier,
        extra_tree_classifier,
        x_train,
        y_train,
        indexes=np.array([0, 2]),
        num_iter=1,
        comparison_type=ComparisonType.DIFFERENCE,
    )
    assert avg.shape == (2,)
    assert worst.shape == (2,)
    assert std.shape == (2,)
    assert np.isfinite(avg).all()
    assert np.isfinite(worst).all()
    assert np.isfinite(std).all()

    return {
        "shapr_shape": tuple(int(dim) for dim in shapr.shape),
        "pdtp_shapes": {
            "avg": tuple(int(dim) for dim in avg.shape),
            "worst": tuple(int(dim) for dim in worst.shape),
            "std": tuple(int(dim) for dim in std.shape),
        },
    }


def run_tree_verification_smoke(mode: str) -> dict[str, object]:
    from art.metrics.verification_decisions_trees import RobustnessVerificationTreeModelsCliqueMethod

    tree_classifier, x_test, y_test = build_tree_verification_classifier()

    verify_signature = inspect.signature(RobustnessVerificationTreeModelsCliqueMethod.verify)
    required = ["x", "y", "eps_init"]
    missing = [name for name in required if name not in verify_signature.parameters]
    assert not missing, f"verify signature missing {missing}: {verify_signature}"

    if mode == "signature":
        return {
            "mode": mode,
            "verify_signature": str(verify_signature),
        }

    verifier = RobustnessVerificationTreeModelsCliqueMethod(classifier=tree_classifier, verbose=False)
    average_bound, verified_error = verifier.verify(
        x=x_test,
        y=y_test,
        eps_init=0.05,
        norm=np.inf,
        nb_search_steps=3,
        max_clique=2,
        max_level=2,
    )
    assert np.isfinite(average_bound)
    assert np.isfinite(verified_error)
    assert 0.0 <= verified_error <= 1.0
    assert 0.0 <= average_bound <= 1.0

    return {
        "mode": mode,
        "average_bound": float(average_bound),
        "verified_error": float(verified_error),
    }


def _require_params(callable_obj, required: list[str], label: str) -> str:
    sig = inspect.signature(callable_obj)
    missing = [name for name in required if name not in sig.parameters]
    assert not missing, f"{label} missing {missing}: {sig}"
    return str(sig)


def check_certification_signatures() -> dict[str, str]:
    from art.evaluations.great_score import GreatScorePyTorch
    from art.evaluations.security_curve import SecurityCurve
    from art.estimators.certification.deep_z import PytorchDeepZ
    from art.estimators.certification.interval import PyTorchIBPClassifier
    from art.estimators.certification.randomized_smoothing.numpy import NumpyRandomizedSmoothing
    from art.estimators.certification.randomized_smoothing.pytorch import PyTorchRandomizedSmoothing
    from art.estimators.certification.derandomized_smoothing.pytorch import PyTorchDeRandomizedSmoothing
    from art.summary_writer import SummaryWriter, SummaryWriterDefault

    signatures: dict[str, str] = {}
    signatures["SecurityCurve.__init__"] = _require_params(SecurityCurve, ["eps"], "SecurityCurve")
    signatures["SecurityCurve.evaluate"] = _require_params(
        SecurityCurve.evaluate,
        ["classifier", "x", "y"],
        "SecurityCurve.evaluate",
    )
    signatures["GreatScorePyTorch.__init__"] = _require_params(
        GreatScorePyTorch,
        ["classifier"],
        "GreatScorePyTorch",
    )
    signatures["GreatScorePyTorch.evaluate"] = _require_params(
        GreatScorePyTorch.evaluate,
        ["x", "y"],
        "GreatScorePyTorch.evaluate",
    )
    signatures["NumpyRandomizedSmoothing"] = _require_params(
        NumpyRandomizedSmoothing,
        ["classifier", "sample_size", "scale", "alpha"],
        "NumpyRandomizedSmoothing",
    )
    signatures["PyTorchRandomizedSmoothing"] = _require_params(
        PyTorchRandomizedSmoothing,
        ["model", "loss", "input_shape", "nb_classes"],
        "PyTorchRandomizedSmoothing",
    )
    signatures["PyTorchDeRandomizedSmoothing"] = _require_params(
        PyTorchDeRandomizedSmoothing,
        ["model", "loss", "input_shape", "nb_classes", "ablation_size"],
        "PyTorchDeRandomizedSmoothing",
    )
    signatures["PytorchDeepZ"] = _require_params(
        PytorchDeepZ,
        ["model", "loss", "input_shape", "nb_classes"],
        "PytorchDeepZ",
    )
    signatures["PyTorchIBPClassifier"] = _require_params(
        PyTorchIBPClassifier,
        ["model", "loss", "input_shape", "nb_classes"],
        "PyTorchIBPClassifier",
    )
    signatures["SummaryWriter"] = _require_params(SummaryWriter, ["summary_writer"], "SummaryWriter")
    signatures["SummaryWriterDefault"] = _require_params(
        SummaryWriterDefault,
        ["summary_writer", "ind_1", "ind_2", "ind_3", "ind_4"],
        "SummaryWriterDefault",
    )

    if importlib.util.find_spec("tensorflow") is not None:
        try:
            from art.estimators.certification.randomized_smoothing.tensorflow import TensorFlowV2RandomizedSmoothing

            signatures["TensorFlowV2RandomizedSmoothing"] = _require_params(
                TensorFlowV2RandomizedSmoothing,
                ["model", "nb_classes", "input_shape"],
                "TensorFlowV2RandomizedSmoothing",
            )
        except Exception as exc:  # pragma: no cover - optional backend path
            signatures["TensorFlowV2RandomizedSmoothing"] = f"unavailable: {exc}"
    else:
        signatures["TensorFlowV2RandomizedSmoothing"] = "skipped (tensorflow not installed)"

    return signatures


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a tiny CPU ART evaluation/certification smoke on synthetic data.")
    parser.add_argument(
        "--tree-mode",
        choices=["verify", "signature"],
        default="verify",
        help="Run actual tiny tree verification or only import/signature checks.",
    )
    args = parser.parse_args()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)

        metric_result = run_metric_smoke()
        privacy_result = run_privacy_smoke()
        tree_result = run_tree_verification_smoke(args.tree_mode)
        cert_signatures = check_certification_signatures()

    print("ART evaluation/certification smoke passed")
    print("metrics:", metric_result)
    print("privacy:", privacy_result)
    print("tree:", tree_result)
    print("certification_signatures:")
    for name, sig in cert_signatures.items():
        print(f"  {name}: {sig}")


if __name__ == "__main__":
    main()
