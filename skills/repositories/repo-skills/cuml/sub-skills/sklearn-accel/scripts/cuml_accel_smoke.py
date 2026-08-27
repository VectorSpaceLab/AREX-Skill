#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-test cuml.accel activation, proxying, and fallback signals."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("programmatic", "print-cli-command"),
        default="programmatic",
        help="Run the smoke directly or print the CLI command that would run it.",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Print the full cuml.accel profile report after each smoke case.",
    )
    return parser.parse_args()


def print_cli_command(profile: bool) -> None:
    cmd = [sys.executable, "-m", "cuml.accel"]
    if profile:
        cmd.append("--profile")
    cmd.append(Path(__file__).name)
    print(" ".join(shlex.quote(part) for part in cmd))


def run_case(label: str, model, x_train, x_test, y_train, y_test, profile: bool):
    from cuml.accel import is_proxy, profile as accel_profile
    from sklearn.metrics import accuracy_score

    print(f"=== {label} ===")
    with accel_profile(quiet=True) as results:
        fitted = model.fit(x_train, y_train)
        score = accuracy_score(y_test, fitted.predict(x_test))

    print(f"{label}_proxy={is_proxy(fitted)} score={score:.3f}")
    for name, stats in sorted(results.method_calls.items()):
        reasons = ", ".join(sorted(stats.fallback_reasons)) or "-"
        print(
            f"{label} signal {name} gpu={stats.gpu_calls} cpu={stats.cpu_calls} reasons={reasons}"
        )

    if profile:
        results.print_report()


def run_programmatic(profile: bool) -> int:
    import cuml

    cuml.accel.install(log_level="info")

    from cuml.accel import enabled, is_proxy
    from scipy import sparse
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split

    x, y = make_classification(
        n_samples=400,
        n_features=20,
        n_informative=8,
        n_redundant=0,
        random_state=0,
    )
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.25, random_state=0, stratify=y
    )

    print(f"enabled={enabled()}")
    print(f"class_proxy={is_proxy(RandomForestClassifier)}")

    run_case(
        "supported",
        RandomForestClassifier(n_estimators=20, max_depth=6, random_state=0),
        x_train,
        x_test,
        y_train,
        y_test,
        profile,
    )
    run_case(
        "fallback",
        RandomForestClassifier(n_estimators=20, max_depth=6, random_state=0),
        sparse.csr_matrix(x_train),
        sparse.csr_matrix(x_test),
        y_train,
        y_test,
        profile,
    )
    return 0


def main() -> int:
    args = parse_args()
    if args.mode == "print-cli-command":
        print_cli_command(args.profile)
        return 0
    return run_programmatic(args.profile)


if __name__ == "__main__":
    raise SystemExit(main())
