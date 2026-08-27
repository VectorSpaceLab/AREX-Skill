#!/usr/bin/env python3
"""Print the model metrics JSON files produced by the project workflows.

This helper reads the standard `packages/` layout from the scispaCy project
and prints the metrics for the core and NER model families.

Example:
    python scripts/print_out_metrics.py --base-path /path/to/packages
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-path", default="packages", help="Directory containing the metrics JSON files.")
    return parser


def print_metrics(base_path: Path) -> None:
    core_model_names = ["lg", "md", "sm", "scibert"]
    ner_model_names = ["bc5cdr", "bionlp13cg", "craft", "jnlpba"]

    for core_model_name in core_model_names:
        print(f"Printing results for {core_model_name}")
        with open(base_path / f"{core_model_name}_genia_results.json") as genia_results_file:
            genia_results = json.load(genia_results_file)
        with open(base_path / f"{core_model_name}_onto_results.json") as onto_results_file:
            onto_results = json.load(onto_results_file)
        with open(base_path / f"{core_model_name}_mm_results.json") as mm_results_file:
            mm_results = json.load(mm_results_file)

        print(f"Genia tag accuracy: {genia_results['tag_acc']}")
        print(f"Genia uas: {genia_results['dep_uas']}")
        print(f"Genia las: {genia_results['dep_las']}")
        print(f"Ontonotes uas: {onto_results['dep_uas']}")
        print(f"MedMentions F1: {mm_results['f1-measure-untyped']}")
        print()

    for ner_model_name in ner_model_names:
        print(f"Printing results for {ner_model_name}")
        with open(base_path / f"{ner_model_name}_results.json") as ner_results_file:
            ner_results = json.load(ner_results_file)
        f1 = ner_results.get("f1-measure-overall", ner_results.get("f1-measure"))
        if f1 is None:
            raise KeyError("Expected 'f1-measure-overall' or 'f1-measure' in NER metrics JSON")
        print(f"NER F1: {f1}")
        print()


def main() -> None:
    args = build_parser().parse_args()
    print_metrics(Path(args.base_path))


if __name__ == "__main__":
    main()
