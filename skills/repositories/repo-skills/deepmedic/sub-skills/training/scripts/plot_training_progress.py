#!/usr/bin/env python3
"""Safely parse and plot DeepMedic training logs.

This is a standalone adaptation of DeepMedic's progress utility. It reads only
known metric sentences and numeric/N/A list tokens; it never executes log text.
Log paths are positional and may be absolute, so the script is independent of
the caller's working directory.
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

NA = "N/A"
SAMPLE_METRICS = ("accuracy", "sensitivity", "precision", "specificity", "dice")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="plot_training_progress",
        description=(
            "Parse DeepMedic text logs and plot overall or class-specific "
            "sample metrics. Full-volume Dice is not smoothed."
        ),
    )
    parser.add_argument("log_files", nargs="+", type=Path, help="DeepMedic text log paths")
    parser.add_argument(
        "-d", "--detailed", dest="detailed", action="store_true",
        help="plot class-specific accuracy, sensitivity, precision, sample Dice, and validation full-volume Dice",
    )
    parser.add_argument(
        "-c", "--classes", nargs="+", type=int, metavar="CLASS",
        help="detailed mode only: class for each log, or one class reused for every log (default: 0)",
    )
    parser.add_argument(
        "-m", "--movingAv", "--moving-average", dest="moving_average", type=int, default=1,
        help="sample-metric moving-average window in subepochs (default: 1)",
    )
    parser.add_argument(
        "-s", "--saveFigure", "--save-figure", dest="save_figure", action="store_true",
        help="save trainingProgress.pdf under --output-dir",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("."),
        help="directory for a saved figure (default: current directory)",
    )
    parser.add_argument("--no-show", action="store_true", help="do not open an interactive plot window")
    return parser


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ValueError("cannot read log {!s}: {}".format(path, exc)) from exc


def _numbers(list_text: str, previous: float = 0.0) -> List[float]:
    """Parse DeepMedic's space-separated bracket list without eval/literal_eval."""
    if not (list_text.startswith("[") and list_text.endswith("]")):
        raise ValueError("malformed metric list: {!r}".format(list_text))
    result: List[float] = []
    for token in list_text[1:-1].split():
        if token == NA:
            value = previous
        else:
            try:
                value = float(token)
            except ValueError as exc:
                raise ValueError("non-numeric metric token {!r}".format(token)) from exc
        result.append(value)
        previous = value
    return result


def _moving_average(values: Sequence[float], window: int) -> List[float]:
    if not values:
        return []
    if window <= 1:
        return list(values)
    output: List[float] = []
    for index in range(len(values)):
        start = max(0, index - window + 1)
        chunk = values[start : index + 1]
        output.append(sum(chunk) / float(len(chunk)))
    return output


def _metadata(text: str) -> Tuple[int, int]:
    subep_match = re.search(r"Number of Subepochs per epoch\s*=\s*(\d+)", text)
    interval_match = re.search(
        r"Perform Full-Inference on Val\. cases every that many epochs\s*=\s*(\d+)", text
    )
    return (
        int(subep_match.group(1)) if subep_match else 20,
        int(interval_match.group(1)) if interval_match else 1,
    )


def _sample_series(text: str, detailed: bool, wanted_class: int) -> Dict[str, Dict[str, List[float]]]:
    """Return {phase: {metric: values}} for known report sentences."""
    phases = {"validation": {}, "training": {}}
    if detailed:
        metric_sentences = {
            "accuracy": "mean accuracy of each subepoch:",
            "sensitivity": "mean sensitivity of each subepoch:",
            "precision": "mean precision of each subepoch:",
            "specificity": "mean specificity of each subepoch:",
            "dice": "mean Dice of each subepoch:",
        }
        class_part = r"Class-{}".format(re.escape(str(wanted_class)))
    else:
        metric_sentences = {"accuracy": "mean accuracy of each subepoch:"}
        class_part = r"Overall"

    for phase_name, phase_word in (("validation", "VALIDATION"), ("training", "TRAINING")):
        for metric, sentence in metric_sentences.items():
            pattern = re.compile(
                re.escape(phase_word) + r"\s*:.*?" + class_part + r"\s*:.*?" +
                re.escape(sentence) + r"\s*(\[[^\]]*\])",
                flags=re.IGNORECASE | re.DOTALL,
            )
            previous = 0.0
            values: List[float] = []
            for match in pattern.finditer(text):
                parsed = _numbers(match.group(1), previous)
                if parsed:
                    values.extend(parsed)
                    previous = parsed[-1]
            phases[phase_name][metric] = values
    return phases


def _full_volume_dice(text: str, class_index: int) -> List[float]:
    pattern = re.compile(
        r"ACCURACY:\s*\([^\n]*\).*?The Per-Class average DICE Coefficients over all subjects are:.*?DICE2\s*=\s*(\[[^\]]*\])",
        flags=re.IGNORECASE | re.DOTALL,
    )
    values: List[float] = []
    previous = 0.0
    for match in pattern.finditer(text):
        parsed = _numbers(match.group(1), previous)
        if class_index >= len(parsed):
            continue
        value = parsed[class_index]
        values.append(value)
        previous = value
    return values


def parse_log(path: Path, detailed: bool, wanted_class: int, moving_average: int) -> Dict[str, object]:
    text = _read(path)
    subepochs, interval = _metadata(text)
    sample = _sample_series(text, detailed, wanted_class)
    for phase in sample.values():
        for metric, values in phase.items():
            phase[metric] = _moving_average(values, moving_average)
    full = _full_volume_dice(text, wanted_class) if detailed else []
    if not any(values for phase in sample.values() for values in phase.values()) and not full:
        raise ValueError("no recognized DeepMedic metric reports found in {!s}".format(path))
    return {
        "name": path.stem,
        "subepochs": subepochs,
        "full_interval": interval,
        "sample": sample,
        "full_dice": full,
    }


def _x_for(values: Sequence[float], subepochs: int) -> List[float]:
    return [index / float(subepochs) for index in range(len(values))]


def _plot(logs: Sequence[Dict[str, object]], detailed: bool, save: bool, output_dir: Path, show: bool) -> None:
    import matplotlib
    if not show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if detailed:
        titles = ["Mean accuracy", "Sensitivity", "Precision", "Sample Dice", "Full-volume Dice2"]
        figure, axes = plt.subplots(2, 5, figsize=(15, 8), squeeze=False)
        for log_index, record in enumerate(logs):
            color = "C{}".format(log_index % 10)
            label = "{}-Class{}".format(record["name"], record["class"])
            sample = record["sample"]
            for row, phase in enumerate(("validation", "training")):
                for col, metric in enumerate(SAMPLE_METRICS):
                    values = sample[phase].get(metric, [])
                    if values:
                        axes[row][col].plot(_x_for(values, record["subepochs"]), values, color=color, label=label)
                if phase == "validation" and record["full_dice"]:
                    full = record["full_dice"]
                    xs = [index * record["full_interval"] for index in range(len(full))]
                    axes[row][4].plot(xs, full, color=color, label=label)
        for row, phase in enumerate(("validation", "training")):
            axes[row][0].set_ylabel(phase.title())
            for col, title in enumerate(titles):
                axes[row][col].set_title(title)
                axes[row][col].set_ylim(0.0, 1.0)
                axes[row][col].set_xlabel("Epoch")
                axes[row][col].grid(True, alpha=0.3)
        axes[1][0].legend(loc="upper left", bbox_to_anchor=(0.0, -0.25), ncol=2)
    else:
        figure, axes = plt.subplots(2, 1, figsize=(10, 7), squeeze=False)
        for log_index, record in enumerate(logs):
            color = "C{}".format(log_index % 10)
            for row, phase in enumerate(("validation", "training")):
                values = record["sample"][phase].get("accuracy", [])
                if values:
                    axes[row][0].plot(_x_for(values, record["subepochs"]), values, color=color, label=record["name"])
                axes[row][0].set_ylabel(phase.title())
                axes[row][0].set_ylim(0.0, 1.0)
                axes[row][0].set_xlabel("Epoch")
                axes[row][0].grid(True, alpha=0.3)
        axes[1][0].legend(loc="upper left", bbox_to_anchor=(0.0, -0.25), ncol=2)
        axes[0][0].set_title("Overall mean accuracy")
    figure.tight_layout()
    if save:
        output_dir.mkdir(parents=True, exist_ok=True)
        destination = output_dir / "trainingProgress.pdf"
        figure.savefig(destination, dpi=figure.dpi)
        print("saved {}".format(destination))
    if show:
        plt.show()
    else:
        plt.close(figure)


def _classes_for_logs(requested: Optional[Sequence[int]], count: int) -> List[int]:
    if not requested:
        return [0] * count
    if len(requested) == 1:
        return [requested[0]] * count
    if len(requested) == count:
        return list(requested)
    raise ValueError("--classes must contain one class or exactly one class per log")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.moving_average < 1:
        print("error: --moving-average must be at least 1", file=sys.stderr)
        return 2
    if args.classes and not args.detailed:
        print("error: --classes is valid only with --detailed", file=sys.stderr)
        return 2
    try:
        classes = _classes_for_logs(args.classes, len(args.log_files))
        records = []
        for path, class_index in zip(args.log_files, classes):
            record = parse_log(path, args.detailed, class_index, args.moving_average)
            record["class"] = class_index
            records.append(record)
        _plot(records, args.detailed, args.save_figure, args.output_dir, not args.no_show)
    except (OSError, ValueError) as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
