#!/usr/bin/env python3
"""Suggest focused SMP maintainer commands for explicit changed paths.

The script is read-only: it does not inspect git, import the package, run tests,
or mutate files. Pass changed paths as positional arguments and consume the JSON
suggestions from stdout.
"""

from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import PurePosixPath
from typing import Iterable

MODEL_TESTS = {
    "deeplabv3": "tests/models/test_deeplab.py",
    "dpt": "tests/models/test_dpt.py",
    "fpn": "tests/models/test_fpn.py",
    "linknet": "tests/models/test_linknet.py",
    "manet": "tests/models/test_manet.py",
    "pan": "tests/models/test_pan.py",
    "pspnet": "tests/models/test_psp.py",
    "segformer": "tests/models/test_segformer.py",
    "unet": "tests/models/test_unet.py",
    "unetplusplus": "tests/models/test_unetplusplus.py",
    "upernet": "tests/models/test_upernet.py",
}

ENCODER_TESTS = OrderedDict(
    [
        (
            ("resnet.py", "densenet.py", "mobilenet.py", "vgg.py"),
            "tests/encoders/test_torchvision_encoders.py",
        ),
        (
            (
                "dpn.py",
                "inceptionresnetv2.py",
                "inceptionv4.py",
                "senet.py",
                "xception.py",
            ),
            "tests/encoders/test_pretrainedmodels_encoders.py",
        ),
        (
            ("efficientnet.py", "mix_transformer.py", "mobileone.py"),
            "tests/encoders/test_smp_encoders.py",
        ),
        (
            ("timm_efficientnet.py", "timm_sknet.py"),
            "tests/encoders/test_timm_ported_encoders.py",
        ),
        (("timm_universal.py",), "tests/encoders/test_timm_universal.py"),
        (("timm_vit.py",), "tests/encoders/test_timm_vit_encoders.py"),
    ]
)

MARKER_EXPR = "compile or torch_export or torch_script"


def normalize(path: str) -> str:
    return str(PurePosixPath(path.replace("\\", "/")))


def add_command(commands: OrderedDict[str, dict[str, object]], command: str, reason: str) -> None:
    if command not in commands:
        commands[command] = {"command": command, "reasons": []}
    commands[command]["reasons"].append(reason)


def decoder_family(parts: tuple[str, ...]) -> str | None:
    if len(parts) >= 3 and parts[0] == "segmentation_models_pytorch" and parts[1] == "decoders":
        return parts[2]
    return None


def encoder_test_for(filename: str) -> str | None:
    for filenames, test_path in ENCODER_TESTS.items():
        if filename in filenames:
            return test_path
    return None


def classify_path(path: str, commands: OrderedDict[str, dict[str, object]], notes: list[str]) -> None:
    normalized = normalize(path)
    parts = PurePosixPath(normalized).parts
    if not parts:
        return

    family = decoder_family(parts)
    if family:
        test_path = MODEL_TESTS.get(family)
        if test_path:
            add_command(
                commands,
                f"pytest -q {test_path} --non-marked-only",
                f"decoder/model change under {family}",
            )
            add_command(
                commands,
                f"pytest -q {test_path} -m \"{MARKER_EXPR}\"",
                "optional compatibility markers if compile/export/script behavior changed",
            )
        else:
            add_command(
                commands,
                "pytest -q tests/models --non-marked-only",
                f"decoder family {family} has no exact helper mapping",
            )
        return

    if normalized.startswith("segmentation_models_pytorch/base/"):
        add_command(
            commands,
            "pytest -q tests/base tests/test_base.py tests/models --non-marked-only",
            "shared base model behavior changed",
        )
        add_command(
            commands,
            f"pytest -q tests/models -m \"{MARKER_EXPR}\"",
            "optional model compatibility markers for shared forward/export changes",
        )
        return

    if normalized.startswith("segmentation_models_pytorch/encoders/"):
        filename = parts[-1]
        test_path = encoder_test_for(filename)
        if test_path:
            add_command(
                commands,
                f"pytest -q {test_path} --non-marked-only",
                f"encoder implementation change in {filename}",
            )
        elif filename in {"__init__.py", "_preprocessing.py", "_legacy_pretrained_settings.py"}:
            add_command(
                commands,
                "pytest -q tests/test_preprocessing.py tests/encoders --non-marked-only",
                "encoder registry or preprocessing metadata changed",
            )
            add_command(commands, "make table", "encoder table may need regeneration")
        else:
            add_command(
                commands,
                "pytest -q tests/encoders --non-marked-only",
                "encoder support file changed",
            )
        add_command(
            commands,
            f"pytest -q tests/encoders -m \"{MARKER_EXPR}\"",
            "optional encoder compatibility markers if feature/script/export behavior changed",
        )
        return

    if normalized.startswith("segmentation_models_pytorch/losses/"):
        add_command(commands, "pytest -q tests/test_losses.py --non-marked-only", "loss implementation changed")
        return

    if normalized.startswith("segmentation_models_pytorch/metrics/"):
        add_command(commands, "pytest -q tests/test_losses.py --non-marked-only", "shared metric/loss functional math may be affected")
        notes.append("Add or run metric-specific tests if this checkout has them for the changed metric.")
        return

    if normalized in {"segmentation_models_pytorch/__init__.py", "segmentation_models_pytorch/__version__.py"}:
        add_command(commands, "pytest -q tests/test_base.py tests/models --non-marked-only", "public package entry point changed")
        return

    if normalized.startswith("tests/models/"):
        add_command(commands, f"pytest -q {normalized} --non-marked-only", "model test changed")
        return

    if normalized.startswith("tests/encoders/"):
        add_command(commands, f"pytest -q {normalized} --non-marked-only", "encoder test changed")
        return

    if normalized.startswith("tests/base/") or normalized == "tests/test_base.py":
        add_command(commands, f"pytest -q {normalized} --non-marked-only", "base test changed")
        return

    if normalized == "tests/test_losses.py":
        add_command(commands, "pytest -q tests/test_losses.py --non-marked-only", "loss test changed")
        return

    if normalized == "tests/test_preprocessing.py":
        add_command(commands, "pytest -q tests/test_preprocessing.py --non-marked-only", "preprocessing test changed")
        return

    if normalized.startswith("docs/") and normalized.endswith(".rst"):
        add_command(commands, "cd docs && make html", "Sphinx documentation changed")
        return

    if normalized == "README.md":
        add_command(commands, "make test", "contributor or public documentation changed")
        return

    if normalized == "Makefile":
        add_command(commands, "make test", "Makefile test workflow changed")
        add_command(commands, "make fixup", "Makefile lint workflow may be affected")
        return

    if normalized == "pyproject.toml":
        add_command(commands, "make test", "project metadata or pytest configuration changed")
        add_command(commands, "make fixup", "Ruff configuration may be affected")
        return

    if normalized == "misc/generate_table.py":
        add_command(commands, "make table", "ported encoder table generator changed")
        return

    if normalized == "misc/generate_table_timm.py":
        add_command(commands, "make table_timm", "timm encoder table generator changed")
        notes.append("make table_timm can be slow because it probes many timm models.")
        return

    if normalized == "misc/generate_test_models.py":
        notes.append(
            "misc/generate_test_models.py is Hugging Face upload-oriented and credentialed; do not run it unless explicitly requested."
        )
        return

    add_command(commands, "make test", "fallback for unclassified repository change")


def suggest(paths: Iterable[str]) -> dict[str, object]:
    commands: OrderedDict[str, dict[str, object]] = OrderedDict()
    notes: list[str] = []
    normalized_paths = [normalize(path) for path in paths]

    for path in normalized_paths:
        classify_path(path, commands, notes)

    if any(path.startswith("segmentation_models_pytorch/encoders/") for path in normalized_paths):
        notes.append("Use RUN_ALL_ENCODERS=1 only for explicit broad encoder matrix validation.")
    if any(path.startswith("segmentation_models_pytorch/") for path in normalized_paths):
        add_command(commands, "make fixup", "format and lint after source changes")
    if any(path.startswith("segmentation_models_pytorch/encoders/") for path in normalized_paths):
        notes.append("Run make table when encoder registry, pretrained settings, or script/compile/export table values change.")
    if any(path.startswith("docs/") for path in normalized_paths):
        notes.append("Docs builds require the docs optional dependencies.")

    return {
        "changed_paths": normalized_paths,
        "commands": list(commands.values()),
        "notes": list(OrderedDict.fromkeys(notes)),
        "safety": {
            "inspects_git": False,
            "mutates_files": False,
            "runs_commands": False,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Suggest focused pytest, docs, and formatting commands for explicit SMP changed paths."
    )
    parser.add_argument("paths", nargs="+", help="Changed file or directory paths relative to the repository root.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    indent = 2 if args.pretty else None
    print(json.dumps(suggest(args.paths), indent=indent, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
