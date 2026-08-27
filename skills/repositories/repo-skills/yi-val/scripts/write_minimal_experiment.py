#!/usr/bin/env python3
"""Create and optionally run a no-network YiVal mini experiment.

The generated fixture uses a local custom function, a tiny CSV dataset, manual
StringWrapper variations, and the string_expected_result evaluator. It is meant
for installation smoke tests and examples, not for benchmarking.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import yaml

CUSTOM_FUNCTION = '''
from yival.schemas.experiment_config import MultimodalOutput
from yival.states.experiment_state import ExperimentState
from yival.wrappers.string_wrapper import StringWrapper


def answer_question(question: str, state: ExperimentState) -> MultimodalOutput:
    suffix = str(StringWrapper("", name="answer_style", state=state))
    if "2+2" in question:
        answer = "4"
    else:
        answer = "unknown"
    if suffix:
        answer = f"{answer} {suffix}"
    return MultimodalOutput(text_output=answer)
'''


def write_fixture(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "mini_yival_task.py").write_text(CUSTOM_FUNCTION, encoding="utf-8")
    (root / "data.csv").write_text("question,expected_result\nWhat is 2+2?,4\n", encoding="utf-8")
    config = {
        "description": "Offline YiVal smoke experiment",
        "custom_function": "mini_yival_task.answer_question",
        "dataset": {
            "source_type": "dataset",
            "file_path": str(root / "data.csv"),
            "reader": "csv_reader",
            "reader_config": {"expected_result_column": "expected_result", "chunk_size": 10},
        },
        "variations": [
            {
                "name": "answer_style",
                "variations": [
                    {"value_type": "str", "value": "", "instantiated_value": "", "variation_id": None},
                    {"value_type": "str", "value": "final", "instantiated_value": "final", "variation_id": None},
                ],
            }
        ],
        "evaluators": [
            {
                "evaluator_type": "individual",
                "matching_technique": "includes",
                "metric_calculators": [{"method": "AVERAGE"}],
                "name": "string_expected_result",
            }
        ],
        "selection_strategy": {
            "ahp_selection": {
                "criteria": ["string_expected_result: matching", "average_latency"],
                "criteria_weights": {"string_expected_result: matching": 0.9, "average_latency": 0.1},
                "criteria_maximization": {"string_expected_result: matching": True, "average_latency": False},
                "normalize_func": None,
            }
        },
    }
    config_path = root / "config.yml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return config_path


def validate_config(config_path: Path) -> None:
    from yival.configs.config_utils import load_and_validate_config

    load_and_validate_config(str(config_path))


def run_config(config_path: Path, output_path: Path) -> None:
    # Ensure the generated custom function module can be imported by YiVal.
    sys.path.insert(0, str(config_path.parent))
    from yival.experiment.experiment_runner import ExperimentRunner

    runner = ExperimentRunner(str(config_path))
    runner.run(display=False, interactive=False, output_path=str(output_path), experiment_input_path="")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="directory for generated fixture; defaults to a temp directory")
    parser.add_argument("--run", action="store_true", help="run the fixture after writing and validating it")
    args = parser.parse_args()

    root = args.output_dir or Path(tempfile.mkdtemp(prefix="yival-mini-"))
    config_path = write_fixture(root)
    validate_config(config_path)
    result = {"fixture_dir": str(root), "config_path": str(config_path), "validated": True}

    if args.run:
        output_path = root / "result.pkl"
        run_config(config_path, output_path)
        # ExperimentRunner writes <stem>_0.pkl for the first config.
        result["run"] = "ok"
        result["expected_pickle"] = str(root / "result_0.pkl")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
