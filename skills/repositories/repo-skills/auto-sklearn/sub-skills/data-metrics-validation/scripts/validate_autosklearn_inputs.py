#!/usr/bin/env python3
"""No-training input checker for autosklearn data validation workflows.

The default mode generates a tiny pandas fixture and validates it without
starting any AutoML training. Use --csv and --target to inspect a small local CSV.
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from typing import Iterable, List, Optional, Sequence, Tuple


VALID_FEAT_TYPES = {"categorical", "numerical", "string"}


def parse_csv_list(value: Optional[str]) -> List[str]:
    if value is None or value.strip() == "":
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def parse_feat_type(value: Optional[str]) -> Optional[List[str]]:
    labels = parse_csv_list(value)
    if not labels:
        return None
    bad = [label for label in labels if label.lower() not in VALID_FEAT_TYPES]
    if bad:
        raise argparse.ArgumentTypeError(
            "invalid feat_type label(s) {}. Valid labels are: {}".format(
                bad, ", ".join(sorted(VALID_FEAT_TYPES))
            )
        )
    return labels


def add_bool_pair(parser: argparse.ArgumentParser, positive: str, negative: str, dest: str, default: bool, help_text: str) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument(positive, dest=dest, action="store_true", help=help_text)
    group.add_argument(negative, dest=dest, action="store_false", help="Disable: " + help_text)
    parser.set_defaults(**{dest: default})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate autosklearn feature/target inputs without training.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Examples:
              python scripts/validate_autosklearn_inputs.py
              python scripts/validate_autosklearn_inputs.py --csv train.csv --target label
              python scripts/validate_autosklearn_inputs.py --csv train.csv --target label \\
                --categorical-columns state,plan --string-columns review --strict-object
              python scripts/validate_autosklearn_inputs.py --csv train.csv --target label \\
                --as-container numpy --feat-type Numerical,Categorical,Numerical
            """
        ),
    )
    parser.add_argument("--csv", help="Training CSV to inspect. If omitted, use a tiny built-in demo fixture.")
    parser.add_argument("--test-csv", help="Optional test CSV with the same target column for X_test/y_test validation.")
    parser.add_argument("--target", default="target", help="Target column name. Default: target")
    parser.add_argument("--task", choices=("classification", "regression"), default="classification", help="Target validation mode. Default: classification")
    parser.add_argument("--max-rows", type=int, default=1000, help="Maximum rows to read from each CSV. Default: 1000")
    parser.add_argument("--as-container", choices=("pandas", "numpy", "list"), default="pandas", help="Container passed to autosklearn validators. Default: pandas")
    parser.add_argument("--feat-type", type=parse_feat_type, help="Comma-separated feature type labels for NumPy workflows: Categorical,Numerical,String.")
    parser.add_argument("--categorical-columns", default="", help="Comma-separated feature columns to cast to pandas category.")
    parser.add_argument("--string-columns", default="", help="Comma-separated feature columns to cast to pandas string.")
    parser.add_argument("--bool-columns", default="", help="Comma-separated feature columns to cast to pandas bool.")
    parser.add_argument("--numeric-columns", default="", help="Comma-separated feature columns to cast with pandas.to_numeric.")
    parser.add_argument("--datetime-columns", default="", help="Comma-separated feature columns to parse as datetime, useful with --strict-datetime to catch unsupported input.")
    parser.add_argument("--drop-columns", default="", help="Comma-separated non-target columns to drop before validation.")
    parser.add_argument("--strict-object", action="store_true", help="Exit nonzero if any pandas feature column remains object dtype.")
    parser.add_argument("--strict-datetime", action="store_true", help="Exit nonzero if any pandas feature column is datetime/timedelta dtype.")
    parser.add_argument("--infer-datetime", action="store_true", help="Best-effort detection of object/string columns that parse as datetimes; use with --strict-datetime to fail them.")
    parser.add_argument("--fail-on-warning", action="store_true", help="Exit nonzero if autosklearn validators emit warnings.")
    add_bool_pair(
        parser,
        "--allow-string-features",
        "--no-allow-string-features",
        "allow_string_features",
        True,
        "Allow autosklearn string feature handling. Default: enabled.",
    )
    return parser


def require_columns(frame, columns: Sequence[str], role: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Unknown {role} column(s): {missing}. Available columns: {list(frame.columns)}")


def make_demo_frame(task: str):
    import pandas as pd

    X = pd.DataFrame(
        {
            "numeric_feature": pd.Series([0.1, 0.4, 0.8, 1.2, 1.5, 2.0], dtype="float64"),
            "category_feature": pd.Series(["red", "blue", "red", "green", "blue", "red"], dtype="category"),
            "bool_feature": pd.Series([True, False, True, False, True, False], dtype="bool"),
            "text_feature": pd.Series(["short note", "long note", "short", "none", "useful", "brief"], dtype="string"),
        }
    )
    if task == "classification":
        y = pd.Series(["no", "yes", "no", "yes", "yes", "no"], name="target", dtype="category")
    else:
        y = pd.Series([1.0, 1.5, 1.2, 2.2, 2.7, 3.1], name="target", dtype="float64")
    frame = X.copy()
    frame["target"] = y
    return frame


def read_frame(args):
    import pandas as pd

    if args.max_rows <= 0:
        raise ValueError("--max-rows must be positive")
    if args.csv:
        frame = pd.read_csv(args.csv, nrows=args.max_rows)
        source = args.csv
    else:
        frame = make_demo_frame(args.task)
        source = "built-in demo fixture"
    if args.target not in frame.columns:
        raise ValueError(f"Target column {args.target!r} not found in {source}. Available columns: {list(frame.columns)}")
    return frame, source


def apply_column_options(frame, args, frame_label: str):
    import pandas as pd

    drop_columns = parse_csv_list(args.drop_columns)
    if drop_columns:
        require_columns(frame, drop_columns, f"{frame_label} drop")
        frame = frame.drop(columns=drop_columns)

    target = args.target
    if target not in frame.columns:
        raise ValueError(f"Target column {target!r} is missing after dropping columns")

    X = frame.drop(columns=[target]).copy()
    y = frame[target].copy()

    casts = {
        "categorical": parse_csv_list(args.categorical_columns),
        "string": parse_csv_list(args.string_columns),
        "bool": parse_csv_list(args.bool_columns),
        "numeric": parse_csv_list(args.numeric_columns),
        "datetime": parse_csv_list(args.datetime_columns),
    }
    for role, columns in casts.items():
        require_columns(X, columns, f"{frame_label} {role}")

    for column in casts["categorical"]:
        X[column] = X[column].astype("category")
    for column in casts["string"]:
        X[column] = X[column].astype("string")
    for column in casts["bool"]:
        X[column] = X[column].astype("bool")
    for column in casts["numeric"]:
        X[column] = pd.to_numeric(X[column], errors="raise")
    for column in casts["datetime"]:
        X[column] = pd.to_datetime(X[column], errors="raise")

    return X, y


def datetime_like_columns(X) -> List[str]:
    import pandas as pd
    from pandas.api.types import is_datetime64_any_dtype, is_timedelta64_dtype, is_object_dtype, is_string_dtype

    found: List[str] = []
    for column in X.columns:
        dtype = X[column].dtype
        if is_datetime64_any_dtype(dtype) or is_timedelta64_dtype(dtype):
            found.append(column)
        elif is_object_dtype(dtype) or is_string_dtype(dtype):
            non_null = X[column].dropna()
            if len(non_null) == 0:
                continue
            sample = non_null.astype(str).head(20)
            parsed = pd.to_datetime(sample, errors="coerce", utc=False)
            if parsed.notna().mean() >= 0.8:
                found.append(column)
    return found


def object_columns(X) -> List[str]:
    from pandas.api.types import is_object_dtype

    return [column for column in X.columns if is_object_dtype(X[column].dtype)]


def print_section(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


def format_mapping(mapping) -> str:
    if mapping is None:
        return "None"
    return ", ".join(f"{key}={value}" for key, value in mapping.items())


def report_basic(X, y, source: str, args) -> None:
    from sklearn.utils.multiclass import type_of_target

    print_section("Input summary")
    print(f"source: {source}")
    print(f"container requested: {args.as_container}")
    print(f"task: {args.task}")
    print(f"X shape: {getattr(X, 'shape', None)}")
    print(f"y shape: {getattr(y, 'shape', None)}")
    print(f"target type_of_target: {type_of_target(y)}")
    if hasattr(X, "dtypes"):
        print("pandas dtypes:")
        for column, dtype in X.dtypes.items():
            print(f"  {column}: {dtype}")
    if hasattr(y, "isna"):
        print(f"target missing values: {int(y.isna().sum())}")


def infer_feature_types(X, args):
    import warnings
    import numpy as np
    from pandas.api.types import is_numeric_dtype
    from autosklearn.data.feature_validator import FeatureValidator

    print_section("Feature type inference")
    warnings_seen: List[str] = []

    if args.as_container == "numpy":
        labels = args.feat_type or ["Numerical"] * X.shape[1]
        print("NumPy mode uses explicit --feat-type or defaults all columns to Numerical.")
        print("feat_type: " + ", ".join(labels))
        array = X.to_numpy()
        print(f"numpy dtype: {array.dtype}")
        if not np.issubdtype(array.dtype, np.number):
            raise ValueError(
                "NumPy mode produced a non-numeric dtype. autosklearn rejects string/object NumPy feature arrays; "
                "use pandas dtypes or encode to numeric and provide feat_type."
            )
        return {i: labels[i].lower() for i in range(len(labels))}, warnings_seen

    if args.as_container == "list":
        if args.feat_type is not None:
            raise ValueError(
                "The current autosklearn FeatureValidator converts Python list input to a pandas DataFrame before "
                "dtype inference, so passing feat_type with --as-container list is unsafe. Use --as-container numpy "
                "for explicit feat_type labels, or use pandas dtypes."
            )
        print("List mode: autosklearn converts lists to a pandas DataFrame and infers dtypes.")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        validator = FeatureValidator(allow_string_features=args.allow_string_features)
        mapping = validator.get_feat_type_from_columns(X.copy())
    for warning in caught:
        warnings_seen.append(str(warning.message))
    print("inferred autosklearn feature types: " + format_mapping(mapping))
    if warnings_seen:
        print("warnings:")
        for message in warnings_seen:
            print(f"  - {message}")
    return mapping, warnings_seen


def validate_feat_type_length(labels: Optional[List[str]], n_features: int, container: str) -> None:
    print_section("feat_type checks")
    if labels is None:
        print("no --feat-type provided")
        if container == "numpy":
            print("NumPy autosklearn default: all columns are treated as numerical.")
        return
    print("provided feat_type: " + ", ".join(labels))
    if len(labels) != n_features:
        raise ValueError(f"feat_type length mismatch: got {len(labels)} labels for {n_features} feature columns")
    bad = [label for label in labels if label.lower() not in VALID_FEAT_TYPES]
    if bad:
        raise ValueError(f"invalid feat_type label(s): {bad}")
    if container == "pandas":
        raise ValueError("Do not pass feat_type with pandas DataFrames; set pandas dtypes instead.")
    print("feat_type length and labels are valid")


def to_requested_container(X, y, X_test, y_test, args):
    if args.as_container == "pandas":
        return X, y, X_test, y_test
    if args.as_container == "numpy":
        X_out = X.to_numpy()
        y_out = y.to_numpy() if hasattr(y, "to_numpy") else y
        X_test_out = X_test.to_numpy() if X_test is not None else None
        y_test_out = y_test.to_numpy() if hasattr(y_test, "to_numpy") else y_test
        return X_out, y_out, X_test_out, y_test_out
    if args.as_container == "list":
        X_out = X.values.tolist()
        y_out = y.tolist() if hasattr(y, "tolist") else list(y)
        X_test_out = X_test.values.tolist() if X_test is not None else None
        y_test_out = y_test.tolist() if hasattr(y_test, "tolist") else None
        return X_out, y_out, X_test_out, y_test_out
    raise ValueError(args.as_container)


def run_autosklearn_validation(X, y, X_test, y_test, args) -> List[str]:
    import warnings
    from autosklearn.data.validation import InputValidator

    print_section("autosklearn InputValidator")
    X_input, y_input, X_test_input, y_test_input = to_requested_container(X, y, X_test, y_test, args)
    feat_type = args.feat_type if args.as_container == "numpy" else None
    validator = InputValidator(
        feat_type=feat_type,
        is_classification=args.task == "classification",
        allow_string_features=args.allow_string_features,
    )
    warnings_seen: List[str] = []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        validator.fit(X_input, y_input, X_test=X_test_input, y_test=y_test_input)
        X_checked, y_checked = validator.transform(X_input, y_input)
    for warning in caught:
        warnings_seen.append(str(warning.message))
    print("validator fit/transform: OK")
    print(f"transformed X type: {type(X_checked).__name__}, shape: {getattr(X_checked, 'shape', None)}")
    print(f"transformed y type: {type(y_checked).__name__}, shape: {getattr(y_checked, 'shape', None)}")
    if hasattr(validator.feature_validator, "feat_type"):
        print("validator feature types: " + format_mapping(validator.feature_validator.feat_type))
    if args.task == "classification":
        classes = getattr(validator.target_validator, "classes_", [])
        try:
            classes_list = list(classes)
        except TypeError:
            classes_list = classes
        print(f"target classes_: {classes_list}")
    if warnings_seen:
        print("validator warnings:")
        for message in warnings_seen:
            print(f"  - {message}")
    return warnings_seen


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        import pandas as pd  # noqa: F401  # imported here so --help has no third-party dependency
        import numpy as np  # noqa: F401
        import sklearn  # noqa: F401
        import autosklearn  # noqa: F401

        frame, source = read_frame(args)
        X, y = apply_column_options(frame, args, "train")

        X_test = None
        y_test = None
        if args.test_csv:
            import pandas as pd

            test_frame = pd.read_csv(args.test_csv, nrows=args.max_rows)
            X_test, y_test = apply_column_options(test_frame, args, "test")

        report_basic(X, y, source, args)

        if args.strict_object:
            bad_object = object_columns(X)
            if bad_object:
                raise ValueError(
                    "--strict-object: pandas object feature columns remain: {}. "
                    "Cast them to category, string, numeric, or drop them.".format(bad_object)
                )

        dt_columns = datetime_like_columns(X) if args.infer_datetime else []
        from pandas.api.types import is_datetime64_any_dtype, is_timedelta64_dtype

        direct_dt_columns = [
            column
            for column in X.columns
            if is_datetime64_any_dtype(X[column].dtype) or is_timedelta64_dtype(X[column].dtype)
        ]
        dt_columns = sorted(set(dt_columns + direct_dt_columns))
        if args.strict_datetime and dt_columns:
            raise ValueError(
                "--strict-datetime: datetime-like feature columns are unsupported by autosklearn: {}. "
                "Convert to numeric/calendar features first.".format(dt_columns)
            )

        validate_feat_type_length(args.feat_type, X.shape[1], args.as_container)
        _, inference_warnings = infer_feature_types(X, args)
        validation_warnings = run_autosklearn_validation(X, y, X_test, y_test, args)

        if args.fail_on_warning and (inference_warnings or validation_warnings):
            raise ValueError("--fail-on-warning: validator emitted warnings")

        print_section("Result")
        print("OK: input validation completed without training an autosklearn model")
        return 0
    except SystemExit:
        raise
    except Exception as exc:  # Keep CLI-friendly diagnostics for future agents.
        print_section("Result")
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
