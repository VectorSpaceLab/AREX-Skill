#!/usr/bin/env python3
"""Read-only inspection of a DeepMedic training output directory."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check_training_outputs",
        description="Inspect DeepMedic logs, checkpoint prefixes, prediction folders, and TensorBoard files without mutating them.",
    )
    parser.add_argument("output_dir", type=Path, help="folderForOutput used by the training session")
    parser.add_argument("--session", help="sessionName; if omitted, inspect all session log/model directories")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit a JSON report")
    parser.add_argument(
        "--require-complete", action="store_true",
        help="exit 1 unless every selected session has a completion marker and at least one complete checkpoint",
    )
    return parser


def _files(path: Path) -> List[str]:
    if not path.is_dir():
        return []
    return sorted(item.name for item in path.iterdir() if item.is_file())


def _checkpoint_prefixes(model_dir: Path) -> List[Dict[str, object]]:
    result: List[Dict[str, object]] = []
    if not model_dir.is_dir():
        return result
    for index_file in sorted(model_dir.glob("*.model.ckpt.index")):
        prefix = index_file.with_suffix("")
        data_files = sorted(model_dir.glob(prefix.name + ".data-*") )
        result.append(
            {
                "prefix": str(prefix),
                "index": str(index_file),
                "data_files": [str(path) for path in data_files],
                "complete": bool(data_files),
            }
        )
    return result


def _log_state(log_file: Path) -> Dict[str, object]:
    if not log_file.is_file():
        return {"path": str(log_file), "exists": False, "completed": False, "size": 0}
    try:
        text = log_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = ""
    # The front end prints its session-finished banner even when do_training()
    # catches an exception and returns 1, so an error marker must disqualify a
    # log from the conservative "complete" status.
    has_error = "ERROR:" in text
    completed = (
        "Training session finished" in text
        and "Finished." in text
        and not has_error
    )
    return {
        "path": str(log_file),
        "exists": True,
        "completed": completed,
        "size": log_file.stat().st_size,
        "has_training": "Training the CNN model" in text,
        "has_epoch_save": "Saving CNN model" in text,
        "has_error": has_error,
    }


def inspect(output_dir: Path, session: Optional[str] = None) -> Dict[str, object]:
    output_dir = output_dir.expanduser()
    if not output_dir.exists():
        return {"output_dir": str(output_dir), "exists": False, "sessions": []}

    if session:
        sessions = [session]
    else:
        discovered = set()
        logs_dir = output_dir / "logs"
        if logs_dir.is_dir():
            discovered.update(path.stem for path in logs_dir.glob("*.txt"))
        model_dir = output_dir / "saved_models"
        if model_dir.is_dir():
            discovered.update(path.name for path in model_dir.iterdir() if path.is_dir())
        sessions = sorted(discovered)

    reports = []
    for name in sessions:
        models = output_dir / "saved_models" / name
        predictions = output_dir / "predictions" / name / "predictions"
        features = output_dir / "predictions" / name / "features"
        tensorboard = output_dir / "tensorboard" / name
        reports.append(
            {
                "session": name,
                "log": _log_state(output_dir / "logs" / (name + ".txt")),
                "models_dir": {"path": str(models), "exists": models.is_dir(), "files": _files(models)},
                "checkpoints": _checkpoint_prefixes(models),
                "predictions_dir": {"path": str(predictions), "exists": predictions.is_dir(), "files": _files(predictions)},
                "features_dir": {"path": str(features), "exists": features.is_dir(), "files": _files(features)},
                "tensorboard_dir": {
                    "path": str(tensorboard),
                    "exists": tensorboard.is_dir(),
                    "files": _files(tensorboard),
                    "train_files": _files(tensorboard / "train"),
                    "val_files": _files(tensorboard / "val"),
                },
            }
        )
    return {"output_dir": str(output_dir), "exists": True, "sessions": reports}


def _print_report(report: Dict[str, object]) -> None:
    print("Output: {}".format(report["output_dir"]))
    if not report["exists"]:
        print("  MISSING: output directory")
        return
    sessions = report["sessions"]
    if not sessions:
        print("  No session logs or model directories found.")
        return
    for item in sessions:
        log = item["log"]
        complete = sum(1 for checkpoint in item["checkpoints"] if checkpoint["complete"])
        print("Session: {}".format(item["session"]))
        print("  log: {} (completed={}, bytes={})".format(log["path"], log["completed"], log["size"]))
        print("  checkpoints: {} complete / {} prefixes".format(complete, len(item["checkpoints"])))
        for checkpoint in item["checkpoints"]:
            print("    {} [{}]".format(checkpoint["prefix"], "complete" if checkpoint["complete"] else "missing data shard"))
        print("  predictions: {} ({} files)".format(item["predictions_dir"]["path"], len(item["predictions_dir"]["files"])))
        print("  features: {} ({} files)".format(item["features_dir"]["path"], len(item["features_dir"]["files"])))
        print("  tensorboard: {} train files, {} val files".format(
            len(item["tensorboard_dir"]["train_files"]), len(item["tensorboard_dir"]["val_files"])))


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    report = inspect(args.output_dir, args.session)
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_report(report)
    if args.require_complete:
        sessions = report.get("sessions", [])
        if not sessions or any(
            not item["log"]["completed"] or not any(checkpoint["complete"] for checkpoint in item["checkpoints"])
            for item in sessions
        ):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
