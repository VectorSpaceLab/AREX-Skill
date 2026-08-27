#!/usr/bin/env python3
"""Fit the admissions logistic regression example with pandas and statsmodels."""

import argparse
import sys
import warnings
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
BUNDLED_DATA_DIR = SKILL_ROOT / "references" / "data"
DEFAULT_TRAIN = BUNDLED_DATA_DIR / "admissions_train.csv"
DEFAULT_TEST = BUNDLED_DATA_DIR / "admissions_test.csv"

REQUIRED_TRAIN_COLUMNS = ("admit", "gre", "gpa", "prestige")
REQUIRED_TEST_COLUMNS = ("gre", "gpa", "prestige")
BASELINE_CATEGORY = "best"


def import_stack():
    try:
        import numpy as np
        import pandas as pd
        import statsmodels.api as sm
        from statsmodels.tools.sm_exceptions import ConvergenceWarning, PerfectSeparationError
    except ImportError as exc:
        raise SystemExit(
            "This helper needs pandas, numpy, and statsmodels in Python 3."
        ) from exc
    return np, pd, sm, ConvergenceWarning, PerfectSeparationError


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Fit the admissions logistic regression example and write predictions."
    )
    parser.add_argument(
        "--train",
        default=str(DEFAULT_TRAIN),
        help="Path to the admissions train CSV. Defaults to the bundled fixture.",
    )
    parser.add_argument(
        "--test",
        default=str(DEFAULT_TEST),
        help="Path to the admissions test CSV. Defaults to the bundled fixture.",
    )
    parser.add_argument(
        "--output",
        default="admissions_predictions.csv",
        help="Prediction CSV to write.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Probability threshold for the yes/no label.",
    )
    parser.add_argument(
        "--plot-dir",
        default=None,
        help="Optional directory for non-interactive PNG plots.",
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip optional plot generation even if --plot-dir is provided.",
    )
    return parser.parse_args(argv)


def trim_and_check_columns(frame, label):
    frame = frame.copy()
    frame.columns = [str(column).strip() for column in frame.columns]
    duplicated = frame.columns[frame.columns.duplicated()].tolist()
    if duplicated:
        unique_duplicates = []
        for column in duplicated:
            if column not in unique_duplicates:
                unique_duplicates.append(column)
        raise SystemExit(
            "%s has duplicate columns after trimming: %s"
            % (label, ", ".join(unique_duplicates))
        )
    return frame


def load_csv(pd, path, label, required_columns):
    path = Path(path).expanduser()
    if not path.exists():
        raise SystemExit("Could not find the %s." % label)
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        raise SystemExit("Could not read the %s." % label) from exc
    frame = trim_and_check_columns(frame, label)
    missing = [column for column in required_columns if column not in frame.columns]
    if missing:
        raise SystemExit(
            "%s is missing required columns: %s"
            % (label, ", ".join(missing))
        )
    extra = [column for column in frame.columns if column not in required_columns]
    if extra:
        print(
            "Note: ignoring extra %s columns: %s"
            % (label, ", ".join(extra)),
            file=sys.stderr,
        )
    return frame


def coerce_numeric(pd, frame, column, label):
    try:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    except Exception as exc:
        raise SystemExit("%s column %r must be numeric." % (label, column)) from exc
    if frame[column].isna().any():
        raise SystemExit("%s column %r contains missing values." % (label, column))


def clean_prestige_column(frame, label):
    prestige = frame["prestige"].astype("string").str.strip()
    if prestige.isna().any() or (prestige == "").any():
        raise SystemExit("%s column 'prestige' contains missing values." % label)
    frame["prestige"] = prestige.astype(str)


def validate_train_frame(pd, frame):
    coerce_numeric(pd, frame, "admit", "train CSV")
    coerce_numeric(pd, frame, "gre", "train CSV")
    coerce_numeric(pd, frame, "gpa", "train CSV")
    clean_prestige_column(frame, "train CSV")
    if not frame["admit"].isin([0, 1]).all():
        raise SystemExit("train CSV column 'admit' must contain only 0 and 1.")


def validate_test_frame(pd, frame):
    coerce_numeric(pd, frame, "gre", "test CSV")
    coerce_numeric(pd, frame, "gpa", "test CSV")
    clean_prestige_column(frame, "test CSV")


def choose_baseline(series):
    categories = sorted({str(value) for value in series.dropna().unique()})
    if not categories:
        raise SystemExit("prestige column does not contain any categories.")
    if BASELINE_CATEGORY in categories:
        return BASELINE_CATEGORY
    return categories[0]


def build_dummy_columns(series, baseline):
    categories = sorted({str(value) for value in series.dropna().unique()})
    return ["prestige_%s" % category for category in categories if category != baseline]


def build_design_matrix(pd, sm, frame, dummy_columns):
    feature_frame = frame[["gre", "gpa"]].copy()
    dummy_frame = pd.get_dummies(frame["prestige"], prefix="prestige")
    dummy_frame = dummy_frame.reindex(columns=dummy_columns, fill_value=0)
    feature_frame = pd.concat([feature_frame, dummy_frame], axis=1)
    feature_frame = sm.add_constant(feature_frame, has_constant="add")
    return feature_frame.astype(float)


def warn_unseen_categories(test_frame, train_series):
    train_categories = {str(value) for value in train_series.dropna().unique()}
    test_categories = {str(value) for value in test_frame["prestige"].dropna().unique()}
    unseen = sorted(test_categories - train_categories)
    if unseen:
        print(
            "Warning: unseen prestige categories in the test CSV will be treated as the baseline: %s"
            % ", ".join(unseen),
            file=sys.stderr,
        )


def fit_logit(sm, ConvergenceWarning, PerfectSeparationError, y_train, x_train):
    model = sm.Logit(y_train, x_train)
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always", ConvergenceWarning)
        try:
            result = model.fit(disp=False)
        except PerfectSeparationError as exc:
            raise SystemExit(
                "Logit fitting failed because the training data appear to be perfectly separated."
            ) from exc
    seen_messages = set()
    for warning in caught_warnings:
        message = str(warning.message)
        if message in seen_messages:
            continue
        seen_messages.add(message)
        print("statsmodels warning: %s" % message, file=sys.stderr)
    converged = getattr(result, "mle_retvals", {}).get("converged", True)
    if not converged:
        print(
            "Warning: statsmodels did not report convergence.",
            file=sys.stderr,
        )
    return result


def build_predictions(pd, np, result, test_frame, x_test, threshold):
    predicted_prob = pd.Series(
        result.predict(x_test),
        index=test_frame.index,
        name="admit_pred",
    )
    predicted_label = pd.Series(
        np.where(predicted_prob >= threshold, "yes", "no"),
        index=test_frame.index,
        name="admit_yn",
    )
    output_frame = test_frame.copy()
    output_frame["admit_pred"] = predicted_prob
    output_frame["admit_yn"] = predicted_label
    return output_frame


def write_output(output_frame, output_path):
    output_path = Path(output_path).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_frame.to_csv(output_path, index=False)
    return output_path


def maybe_write_plots(train_frame, predictions, plot_dir):
    if plot_dir is None:
        return
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:
        print(
            "Skipping plot output because matplotlib is unavailable: %s" % exc,
            file=sys.stderr,
        )
        return

    plot_dir = Path(plot_dir).expanduser()
    try:
        plot_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        print(
            "Skipping plot output because the plot directory could not be created: %s" % exc,
            file=sys.stderr,
        )
        return

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(train_frame["gpa"].astype(float), bins=12, color="#4472C4", alpha=0.85)
    ax.set_title("GPA distribution")
    ax.set_xlabel("GPA")
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(plot_dir / "gpa_histogram.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    not_admitted = train_frame.loc[train_frame["admit"] == 0, "gre"].astype(float)
    admitted = train_frame.loc[train_frame["admit"] == 1, "gre"].astype(float)
    ax.boxplot([not_admitted, admitted])
    ax.set_xticks([1, 2])
    ax.set_xticklabels(["no", "yes"])
    ax.set_title("GRE by admission status")
    ax.set_xlabel("Admit")
    ax.set_ylabel("GRE")
    fig.tight_layout()
    fig.savefig(plot_dir / "gre_by_admit.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(
        predictions["admit_pred"].astype(float),
        bins=12,
        color="#70AD47",
        alpha=0.85,
    )
    ax.set_title("Predicted admission probability")
    ax.set_xlabel("Probability")
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(plot_dir / "predicted_probability_hist.png", dpi=150)
    plt.close(fig)


def main(argv=None):
    args = parse_args(argv)
    if args.threshold < 0.0 or args.threshold > 1.0:
        raise SystemExit("--threshold must be between 0 and 1.")

    np, pd, sm, ConvergenceWarning, PerfectSeparationError = import_stack()

    train_frame = load_csv(pd, args.train, "train CSV", REQUIRED_TRAIN_COLUMNS)
    test_frame = load_csv(pd, args.test, "test CSV", REQUIRED_TEST_COLUMNS)
    validate_train_frame(pd, train_frame)
    validate_test_frame(pd, test_frame)

    baseline = choose_baseline(train_frame["prestige"])
    dummy_columns = build_dummy_columns(train_frame["prestige"], baseline)
    print("Using prestige baseline category: %s" % baseline, file=sys.stderr)
    warn_unseen_categories(test_frame, train_frame["prestige"])

    x_train = build_design_matrix(pd, sm, train_frame, dummy_columns)
    y_train = train_frame["admit"].astype(float)
    result = fit_logit(sm, ConvergenceWarning, PerfectSeparationError, y_train, x_train)

    print(result.summary())

    x_test = build_design_matrix(pd, sm, test_frame, dummy_columns)
    predictions = build_predictions(pd, np, result, test_frame, x_test, args.threshold)
    output_path = write_output(predictions, args.output)
    print("Wrote predictions to %s" % output_path, file=sys.stderr)

    if args.no_plots:
        if args.plot_dir is not None:
            print("Skipping plots because --no-plots was supplied.", file=sys.stderr)
        return 0

    maybe_write_plots(train_frame, predictions, args.plot_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
