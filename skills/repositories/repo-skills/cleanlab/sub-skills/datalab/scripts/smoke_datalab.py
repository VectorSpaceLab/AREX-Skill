#!/usr/bin/env python3
"""Deterministic smoke helper for the Datalab sub-skill.

This script exercises:
- the public Datalab constructor and getters
- classification, regression, and multilabel task variants
- custom IssueManager registration
- optional image/CleanVision + spurious-correlation handling
- the internal Task enum values used by the router
"""

from __future__ import annotations

import argparse
import contextlib
import io
from typing import List, Tuple

import numpy as np
import pandas as pd

from cleanlab import Datalab, IssueManager
from cleanlab.datalab.internal.issue_manager_factory import REGISTRY, register
from cleanlab.datalab.internal.task import Task


def capture_report(lab: Datalab, **kwargs) -> str:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        lab.report(**kwargs)
    return buffer.getvalue()


def assert_task_enum() -> None:
    assert [task.value for task in Task] == ["classification", "regression", "multilabel"]


def make_classification_case() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    X = np.array(
        [
            [0.00, 0.00],
            [0.00, 0.00],
            [0.05, 0.04],
            [0.07, 0.02],
            [0.09, 0.03],
            [1.00, 1.00],
            [1.02, 0.99],
            [1.04, 1.01],
            [1.05, 1.00],
            [1.06, 1.02],
            [2.00, 2.00],
            [2.05, 2.02],
            [2.10, 2.00],
            [2.15, 2.05],
            [5.00, -3.00],
        ],
        dtype=float,
    )
    y = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2], dtype=int)
    pred_probs = np.full((len(y), 3), 0.02, dtype=float)
    pred_probs[np.arange(len(y)), y] = 0.96
    # Deliberately make the middle cluster underperform.
    pred_probs[5:10] = np.array([0.02, 0.02, 0.96], dtype=float)
    cluster_ids = np.array([0] * 5 + [1] * 5 + [2] * 5, dtype=int)
    return X, y, pred_probs, cluster_ids


def make_regression_case() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    X = np.array(
        [
            [0.00, 0.00],
            [0.00, 0.00],
            [0.10, 0.05],
            [0.12, 0.04],
            [1.00, 1.00],
            [1.02, 0.98],
            [1.03, 1.01],
            [1.05, 1.00],
            [2.00, 2.00],
            [2.01, 1.99],
            [2.02, 2.03],
            [4.50, -3.00],
        ],
        dtype=float,
    )
    y_true = 1.5 * X[:, 0] - 0.75 * X[:, 1]
    y = y_true.copy()
    y[10] += 1.0
    return X, y, y_true


def make_multilabel_case() -> Tuple[np.ndarray, List[List[int]], np.ndarray]:
    X = np.array(
        [
            [0.00, 0.00],
            [0.00, 0.00],
            [0.05, 0.03],
            [0.06, 0.04],
            [1.00, 1.00],
            [1.02, 0.99],
            [1.05, 1.01],
            [1.06, 1.00],
            [2.00, 2.00],
            [2.02, 2.01],
            [2.05, 2.00],
            [4.00, -2.50],
        ],
        dtype=float,
    )
    labels: List[List[int]] = [
        [0],
        [0],
        [0, 1],
        [0, 1],
        [1],
        [1],
        [1, 2],
        [1, 2],
        [2],
        [2],
        [0, 2],
        [0, 1, 2],
    ]
    pred_probs = np.full((len(labels), 3), 0.1, dtype=float)
    for idx, label_set in enumerate(labels):
        for label in label_set:
            pred_probs[idx, label] = 0.9
    # Deliberately make the last example disagree with the provided label set.
    pred_probs[11] = np.array([0.9, 0.9, 0.1], dtype=float)
    return X, labels, pred_probs


def assert_contains(text: str, expected: List[str]) -> None:
    missing = [item for item in expected if item not in text]
    assert not missing, f"Missing expected substrings: {missing}"


def run_classification_smoke() -> None:
    X, y, pred_probs, cluster_ids = make_classification_case()
    lab = Datalab({"features": X, "label": y}, label_name="label", verbosity=0)

    issue_types = {
        "label": {},
        "outlier": {"k": 3},
        "near_duplicate": {"k": 3},
        "class_imbalance": {},
        "data_valuation": {"k": 3},
    }
    lab.find_issues(features=X, pred_probs=pred_probs, issue_types=issue_types)
    lab.find_issues(
        pred_probs=pred_probs,
        issue_types={"underperforming_group": {"cluster_ids": cluster_ids}},
    )

    summary = lab.get_issue_summary()
    expected_issue_types = {
        "label",
        "outlier",
        "near_duplicate",
        "class_imbalance",
        "data_valuation",
        "underperforming_group",
    }
    assert expected_issue_types.issubset(set(summary["issue_type"]))
    assert not lab.get_issues("label").empty
    assert "given_label" in lab.get_issues("label").columns
    assert "near_duplicate_sets" in lab.get_issues("near_duplicate").columns

    report_text = capture_report(
        lab,
        num_examples=3,
        verbosity=0,
        show_summary_score=True,
        show_all_issues=True,
    )
    assert_contains(report_text, ["label", "outlier", "near_duplicate", "underperforming_group"])
    print("[classification] ok", sorted(summary["issue_type"].tolist()))


def run_regression_smoke() -> None:
    X, y, y_pred = make_regression_case()
    lab = Datalab({"features": X, "y": y}, label_name="y", task="regression", verbosity=0)

    lab.find_issues(
        features=X,
        pred_probs=y_pred,
        issue_types={
            "label": {},
            "outlier": {"k": 3},
            "near_duplicate": {"k": 3},
            "data_valuation": {"k": 3},
        },
    )

    summary = lab.get_issue_summary()
    expected_issue_types = {"label", "outlier", "near_duplicate", "data_valuation"}
    assert expected_issue_types.issubset(set(summary["issue_type"]))
    assert not lab.get_issues("label").empty
    assert "given_label" in lab.get_issues("label").columns

    report_text = capture_report(
        lab,
        num_examples=3,
        verbosity=0,
        show_summary_score=True,
        show_all_issues=True,
    )
    assert_contains(report_text, ["label", "outlier", "near_duplicate", "data_valuation"])
    print("[regression] ok", sorted(summary["issue_type"].tolist()))


def run_multilabel_smoke() -> None:
    X, labels, pred_probs = make_multilabel_case()
    lab = Datalab({"features": X, "labels": labels}, label_name="labels", task="multilabel", verbosity=0)

    lab.find_issues(
        features=X,
        pred_probs=pred_probs,
        issue_types={
            "label": {},
            "outlier": {"k": 3},
            "near_duplicate": {"k": 3},
        },
    )

    summary = lab.get_issue_summary()
    expected_issue_types = {"label", "outlier", "near_duplicate"}
    assert expected_issue_types.issubset(set(summary["issue_type"]))
    assert not lab.get_issues("label").empty
    assert "given_label" in lab.get_issues("label").columns

    report_text = capture_report(
        lab,
        num_examples=3,
        verbosity=0,
        show_summary_score=True,
        show_all_issues=True,
    )
    assert_contains(report_text, ["label", "outlier", "near_duplicate"])
    print("[multilabel] ok", sorted(summary["issue_type"].tolist()))


def run_custom_issue_manager_smoke() -> None:
    class ToyIssueManager(IssueManager):
        issue_name = "toy_issue"
        description = "Toy issue used to validate custom registration."
        verbosity_levels = {0: [], 1: ["example_count"]}

        def find_issues(self, **kwargs):
            n = len(self.datalab.data)
            scores = np.linspace(1.0, 0.2, n)
            self.issues = pd.DataFrame(
                {
                    "is_toy_issue_issue": scores < 0.5,
                    "toy_issue_score": scores,
                }
            )
            self.summary = self.make_summary(score=float(scores.mean()))
            self.info = {"example_count": n}

    if "toy_issue" in REGISTRY[Task.CLASSIFICATION]:
        REGISTRY[Task.CLASSIFICATION].pop("toy_issue", None)

    register(ToyIssueManager, task="classification")
    try:
        lab = Datalab({"x": [0, 1, 2, 3], "label": [0, 0, 1, 1]}, label_name="label", verbosity=0)
        lab.find_issues(issue_types={"toy_issue": {}})
        summary = lab.get_issue_summary("toy_issue")
        assert summary["issue_type"].tolist() == ["toy_issue"]
        assert not lab.get_issues("toy_issue").empty
        report_text = capture_report(
            lab,
            num_examples=2,
            verbosity=1,
            show_summary_score=True,
            show_all_issues=True,
        )
        assert_contains(report_text, ["Toy issue used to validate custom registration.", "example_count"])
        print("[custom-issue-manager] ok", summary["num_issues"].tolist())
    finally:
        REGISTRY[Task.CLASSIFICATION].pop("toy_issue", None)


def run_image_smoke() -> None:
    try:
        from datasets import Dataset
        from PIL import Image, ImageDraw, ImageFilter
    except ImportError:
        print("[image] skipped (datasets/Pillow/CleanVision optional deps unavailable)")
        return

    images = []
    labels = []
    for idx in range(20):
        label = 0 if idx < 10 else 1
        labels.append(label)
        background = (18, 18, 18) if label == 0 else (238, 238, 238)
        img = Image.new("RGB", (32, 32), background)
        draw = ImageDraw.Draw(img)
        draw.ellipse((8, 8, 24, 24), fill=(255, 0, 0) if label == 0 else (0, 0, 255))
        if idx % 2 == 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=1))
        images.append(img)

    dataset = Dataset.from_dict({"image": images, "label": labels})
    lab = Datalab(dataset, label_name="label", image_key="image", verbosity=0)

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        lab.find_issues(
            issue_types={
                "image_issue_types": {"dark": {}, "blurry": {}},
                "spurious_correlations": {"threshold": 0.25},
            }
        )

    info = lab.get_info("spurious_correlations")
    correlations_df = info["correlations_df"]
    assert info["threshold"] == 0.25
    assert not correlations_df.empty
    assert set(correlations_df.columns) >= {"property", "score"}

    report_text = capture_report(lab, num_examples=2, verbosity=0, show_all_issues=True)
    assert_contains(report_text, ["dark", "blurry", "spurious"])
    print("[image] ok", correlations_df["property"].tolist())


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Datalab smoke checks.")
    parser.add_argument(
        "--image",
        action="store_true",
        help="Also run the optional Hugging Face image + CleanVision smoke case.",
    )
    args = parser.parse_args(argv)

    assert_task_enum()
    run_classification_smoke()
    run_regression_smoke()
    run_multilabel_smoke()
    run_custom_issue_manager_smoke()
    if args.image:
        run_image_smoke()
    else:
        print("[image] skipped (pass --image to run the optional CleanVision smoke)")

    print("All Datalab smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
