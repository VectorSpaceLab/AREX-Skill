#!/usr/bin/env python3
"""Check that an environment can use the mlxtend repo skill workflows.

The quick check imports the package and representative public APIs. With
`--run-subskill-smokes`, this script runs the bundled sub-skill smoke helpers
using the current Python interpreter. It uses only installed packages and files
inside this generated skill directory.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path


PUBLIC_IMPORTS = [
    ("mlxtend", None),
    ("mlxtend.classifier", "EnsembleVoteClassifier"),
    ("mlxtend.regressor", "StackingRegressor"),
    ("mlxtend.cluster", "Kmeans"),
    ("mlxtend.evaluate", "accuracy_score"),
    ("mlxtend.feature_selection", "SequentialFeatureSelector"),
    ("mlxtend.feature_extraction", "PrincipalComponentAnalysis"),
    ("mlxtend.preprocessing", "TransactionEncoder"),
    ("mlxtend.frequent_patterns", "apriori"),
    ("mlxtend.plotting", "plot_confusion_matrix"),
    ("mlxtend.data", "iris_data"),
    ("mlxtend.file_io", "find_files"),
    ("mlxtend.text", "tokenizer_words_and_emoticons"),
    ("mlxtend.math", "num_combinations"),
    ("mlxtend.utils", "check_Xy"),
]


SUBSKILL_SMOKES = [
    ("estimators-and-ensembles", "scripts/estimator_ensemble_smoke.py", ["--task", "all"]),
    ("evaluation-and-validation", "scripts/evaluation_smoke.py", ["--task", "all"]),
    ("feature-workflows", "scripts/feature_workflows_smoke.py", ["--task", "all"]),
    ("frequent-patterns", "scripts/frequent_patterns_smoke.py", ["--algorithm", "all"]),
    ("plotting-and-utilities", "scripts/plotting_utilities_smoke.py", ["--task", "all"]),
]


def quick_import_check() -> dict:
    import mlxtend

    result = {"mlxtend_version": getattr(mlxtend, "__version__", "unknown"), "imports": []}
    for module_name, attr in PUBLIC_IMPORTS:
        module = importlib.import_module(module_name)
        entry = {"module": module_name, "status": "ok"}
        if attr is not None:
            getattr(module, attr)
            entry["attribute"] = attr
        result["imports"].append(entry)
    return result


def run_subskill_smokes(skill_root: Path) -> list[dict]:
    env = os.environ.copy()
    env.setdefault("MPLBACKEND", "Agg")
    results = []
    for subskill, rel_script, args in SUBSKILL_SMOKES:
        script = skill_root / "sub-skills" / subskill / rel_script
        if not script.exists():
            raise FileNotFoundError(f"missing smoke script: {script}")
        cmd = [sys.executable, str(script), *args]
        proc = subprocess.run(cmd, text=True, capture_output=True, env=env, timeout=240)
        results.append(
            {
                "subskill": subskill,
                "exit_code": proc.returncode,
                "stdout_tail": proc.stdout[-1200:],
                "stderr_tail": proc.stderr[-1200:],
            }
        )
        if proc.returncode != 0:
            raise RuntimeError(f"{subskill} smoke failed with exit code {proc.returncode}: {proc.stderr[-800:]}")
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-subskill-smokes",
        action="store_true",
        help="Run all bundled sub-skill smoke scripts after the quick import check.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    skill_root = Path(__file__).resolve().parents[1]
    result = {"status": "ok", "quick": quick_import_check()}
    if args.run_subskill_smokes:
        result["subskill_smokes"] = run_subskill_smokes(skill_root)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"mlxtend {result['quick']['mlxtend_version']}: quick import check ok")
        if args.run_subskill_smokes:
            for row in result["subskill_smokes"]:
                print(f"{row['subskill']}: smoke ok")


if __name__ == "__main__":
    main()
