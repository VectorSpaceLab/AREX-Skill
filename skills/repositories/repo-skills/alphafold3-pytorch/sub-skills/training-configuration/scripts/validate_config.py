#!/usr/bin/env python3
"""Read-only YAML/Pydantic configuration validator.

This helper parses one mapping, optionally selects a dotted mapping path, runs
static cross-field checks, and validates with the installed package config
models when they can be imported. It intentionally never calls a factory,
constructs Trainer/Fabric, reads dataset records, creates directories, loads a
checkpoint, downloads data, or starts training.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib
import inspect
import io
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class Finding:
    level: str
    message: str
    location: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class Report:
    def __init__(self) -> None:
        self.findings: list[Finding] = []
        self.package_status = "not-run"
        self.kind: str | None = None
        self.dotpath: str | None = None

    def error(self, message: str, location: str | None = None) -> None:
        self.findings.append(Finding("error", message, location))

    def warning(self, message: str, location: str | None = None) -> None:
        self.findings.append(Finding("warning", message, location))

    @property
    def errors(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.level == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.level == "warning"]


def parse_dotpath(value: str | None, report: Report) -> list[str]:
    if value is None:
        return []
    if not value or value.startswith(".") or value.endswith(".") or ".." in value:
        report.error("dotpath must contain non-empty dot-separated mapping keys", "--dotpath")
        return []
    segments = value.split(".")
    if any(not segment for segment in segments):
        report.error("dotpath contains an empty key", "--dotpath")
        return []
    return segments


def select_mapping(document: Any, segments: list[str], report: Report) -> Any:
    selected = document
    for segment in segments:
        if not isinstance(selected, dict):
            report.error(
                f"cannot resolve '{segment}': current value is not a mapping",
                ".".join(segments),
            )
            return None
        if segment not in selected:
            report.error(f"dotpath key '{segment}' is absent", ".".join(segments))
            return None
        selected = selected[segment]
    if selected is not None and not isinstance(selected, dict):
        report.error("selected YAML value must be a mapping", ".".join(segments) or "<root>")
    return selected


def detect_kind(mapping: dict[str, Any]) -> str:
    if "training" in mapping or "training_order" in mapping:
        return "conductor"
    trainer_markers = {
        "num_train_steps",
        "batch_size",
        "grad_accum_every",
        "valid_every",
        "checkpoint_folder",
        "dataset_config",
    }
    if trainer_markers.intersection(mapping):
        return "trainer"
    return "model"


def scalar_positive(mapping: dict[str, Any], key: str, report: Report, location: str) -> None:
    if key not in mapping:
        return
    value = mapping[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return
    if value <= 0:
        report.error(f"{key} must be greater than zero", f"{location}.{key}")


def validate_trainer_static(
    mapping: dict[str, Any],
    report: Report,
    location: str = "trainer",
    trainer_parameters: set[str] | None = None,
    model_injected: bool = False,
) -> None:
    for key in ("num_train_steps", "batch_size", "grad_accum_every", "valid_every", "checkpoint_every"):
        scalar_positive(mapping, key, report, location)

    if mapping.get("overwrite_checkpoints") is True:
        report.warning(
            "overwrite_checkpoints=true permits periodic checkpoint replacement; use a unique approved namespace or set it false",
            f"{location}.overwrite_checkpoints",
        )

    optimizer_flags = [
        key for key in ("use_adam_atan2", "use_adopt_atan2", "use_lion")
        if mapping.get(key) is True
    ]
    if len(optimizer_flags) > 1:
        report.error(
            "at most one alternate optimizer flag may be true: " + ", ".join(optimizer_flags),
            location,
        )

    fabric_kwargs = mapping.get("fabric_kwargs")
    if isinstance(fabric_kwargs, dict) and mapping.get("fp16") is True and "precision" in fabric_kwargs:
        report.error(
            "fp16=true injects Fabric precision and cannot be combined with fabric_kwargs.precision",
            f"{location}.fabric_kwargs.precision",
        )

    if mapping.get("use_torch_compile") is True:
        report.warning(
            "use_torch_compile requires a separately verified type-checking/runtime setup; keep it off for the first diagnostic",
            f"{location}.use_torch_compile",
        )

    dataset_config = mapping.get("dataset_config")
    if dataset_config is not None:
        if not isinstance(dataset_config, dict):
            report.error("dataset_config must be a mapping", f"{location}.dataset_config")
        else:
            dataset_type = dataset_config.get("dataset_type", "pdb")
            if dataset_type not in ("pdb", "atom"):
                report.error("dataset_type must be 'pdb' or 'atom'", f"{location}.dataset_config.dataset_type")
            if dataset_type == "atom" and dataset_config.get("convert_pdb_to_atom") is True:
                report.error(
                    "convert_pdb_to_atom=true requires dataset_type='pdb'",
                    f"{location}.dataset_config.convert_pdb_to_atom",
                )
            if dataset_config.get("train_weighted_sampler") is not None and dataset_type != "pdb":
                report.error(
                    "train_weighted_sampler is only meaningful with dataset_type='pdb'",
                    f"{location}.dataset_config.train_weighted_sampler",
                )

            for folder_key in ("train_folder", "valid_folder", "test_folder"):
                if folder_key in dataset_config and dataset_config[folder_key] is not None and not isinstance(
                    dataset_config[folder_key], (str, Path)
                ):
                    report.error(
                        f"{folder_key} must be a path string",
                        f"{location}.dataset_config.{folder_key}",
                    )

        for injected_key in ("dataset", "valid_dataset", "test_dataset"):
            if injected_key in mapping:
                report.error(
                    f"{injected_key} is duplicated by dataset_config; choose YAML dataset construction or caller injection",
                    f"{location}.{injected_key}",
                )
    else:
        for injected_key in ("dataset", "valid_dataset", "test_dataset"):
            if injected_key in mapping:
                report.error(
                    f"{injected_key} cannot be a useful serialized YAML dataset object; inject it at the Python call site",
                    f"{location}.{injected_key}",
                )

    if trainer_parameters is not None:
        config_keys = {
            "model",
            "num_train_steps",
            "batch_size",
            "grad_accum_every",
            "valid_every",
            "ema_decay",
            "lr",
            "clip_grad_norm",
            "accelerator",
            "checkpoint_prefix",
            "checkpoint_every",
            "checkpoint_folder",
            "overwrite_checkpoints",
            "dataset_config",
            "use_tensorboard",
            "tensorboard_log_dir",
            "logger_kwargs",
        }
        unsupported = sorted(
            key
            for key in mapping
            if key not in config_keys and key not in trainer_parameters and key not in {"dataset", "valid_dataset", "test_dataset"}
        )
        if unsupported:
            report.error(
                "extra trainer keys are accepted by Pydantic but are not Trainer keywords: " + ", ".join(unsupported),
                location,
            )

    if "model" not in mapping or mapping.get("model") is None:
        if not model_injected:
            report.warning(
                "model is omitted; YAML-only trainer construction requires a caller-injected model",
                f"{location}.model",
            )
    elif not isinstance(mapping.get("model"), dict):
        report.error("model must be a mapping", f"{location}.model")


def validate_conductor_static(
    mapping: dict[str, Any],
    report: Report,
    trainer_parameters: set[str] | None = None,
) -> None:
    model = mapping.get("model")
    if model is None:
        report.error(
            "ConductorConfig.create_instance requires a root model mapping; it cannot construct a conductor phase from YAML without one",
            "conductor.model",
        )
    elif not isinstance(model, dict):
        report.error("model must be a mapping", "conductor.model")

    order = mapping.get("training_order")
    phases = mapping.get("training")
    if not isinstance(order, list):
        report.error("training_order must be a list", "conductor.training_order")
    if not isinstance(phases, dict):
        report.error("training must be a mapping of phase names to trainer mappings", "conductor.training")
        return

    if isinstance(order, list):
        if any(not isinstance(name, str) for name in order):
            report.error("every training_order entry must be a string", "conductor.training_order")
        if len(order) != len(set(order)):
            report.error("training_order contains duplicate phase names", "conductor.training_order")
        order_set = set(order)
        phase_set = set(phases)
        if order_set != phase_set:
            missing = sorted(phase_set - order_set)
            unknown = sorted(order_set - phase_set)
            detail: list[str] = []
            if missing:
                detail.append("missing from order: " + ", ".join(missing))
            if unknown:
                detail.append("not present under training: " + ", ".join(unknown))
            report.error("training_order must match training keys (" + "; ".join(detail) + ")", "conductor.training_order")

    root_folder = mapping.get("checkpoint_folder")
    root_prefix = mapping.get("checkpoint_prefix")
    effective: dict[tuple[str, str], str] = {}
    for name, phase in phases.items():
        phase_location = f"conductor.training.{name}"
        if not isinstance(phase, dict):
            report.error("phase must be a trainer mapping", phase_location)
            continue
        validate_trainer_static(
            phase,
            report,
            phase_location,
            trainer_parameters,
            model_injected=True,
        )
        if "model" in phase and phase.get("model") is not None:
            report.error(
                "a conductor phase model conflicts with the root model injected by ConductorConfig.create_instance",
                f"{phase_location}.model",
            )
        phase_folder = phase.get("checkpoint_folder")
        phase_prefix = phase.get("checkpoint_prefix")
        if isinstance(root_folder, str) and isinstance(phase_folder, str):
            effective_folder = str(Path(root_folder) / phase_folder)
        else:
            effective_folder = "<unknown-folder>"
        if isinstance(root_prefix, str) and isinstance(phase_prefix, str):
            effective_prefix = root_prefix + phase_prefix
        else:
            effective_prefix = "<unknown-prefix>"
        key = (effective_folder, effective_prefix)
        if key in effective:
            report.error(
                f"phase shares effective checkpoint namespace with {effective[key]}: {effective_folder!r} / {effective_prefix!r}",
                phase_location,
            )
        else:
            effective[key] = name


def package_model_validate(cls: Any, mapping: dict[str, Any]) -> Any:
    validator = getattr(cls, "model_validate", None)
    if callable(validator):
        return validator(mapping)
    parser = getattr(cls, "parse_obj", None)
    if callable(parser):
        return parser(mapping)
    raise RuntimeError(f"{cls.__name__} has no Pydantic validation entry point")


def format_pydantic_error(exc: Exception) -> list[tuple[str, str]]:
    errors = getattr(exc, "errors", None)
    if not callable(errors):
        return [("<package-model>", str(exc))]
    output: list[tuple[str, str]] = []
    try:
        for item in errors():
            location = ".".join(str(part) for part in item.get("loc", ())) or "<root>"
            output.append((location, str(item.get("msg", item))))
    except Exception:
        return [("<package-model>", str(exc))]
    return output or [("<package-model>", str(exc))]


def validate_with_package(kind: str, mapping: dict[str, Any], report: Report) -> set[str] | None:
    try:
        # Package import can emit optional-dependency warnings. Keep --json
        # stdout machine-readable while still reporting import failures below.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            configs = importlib.import_module("alphafold3_pytorch.configs")
            trainer_module = importlib.import_module("alphafold3_pytorch.trainer")
            trainer_signature = inspect.signature(trainer_module.Trainer.__init__)
            trainer_parameters = {
                name for name in trainer_signature.parameters if name != "self"
            }
            classes = {
                "model": configs.Alphafold3Config,
                "trainer": configs.TrainerConfig,
                "conductor": configs.ConductorConfig,
            }
    except Exception as exc:  # dependency/import failures should be visible, not fatal tracebacks
        report.package_status = "unavailable"
        report.warning(
            "package-model validation unavailable; raw YAML/static checks ran: "
            f"{type(exc).__name__}: {exc}"
        )
        return None

    report.package_status = "passed"
    cls = classes[kind]
    try:
        # This creates only the Pydantic config object. It deliberately does not
        # call create_instance, Trainer, Fabric, DataLoader, or any model factory.
        package_model_validate(cls, mapping)
    except Exception as exc:
        report.package_status = "failed"
        for location, message in format_pydantic_error(exc):
            report.error(message, location)
    return trainer_parameters


def read_yaml(path: Path, report: Report) -> Any:
    if not path.is_file():
        report.error(f"configuration file does not exist or is not a regular file: {path}", "config")
        return None
    try:
        yaml = importlib.import_module("yaml")
    except Exception as exc:
        report.error(
            "PyYAML is required to parse configuration files: "
            f"{type(exc).__name__}: {exc}",
            "dependency",
        )
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            document = yaml.safe_load(handle)
    except Exception as exc:
        report.error(f"unable to parse YAML: {type(exc).__name__}: {exc}", "config")
        return None
    if document is None:
        report.error("YAML document is empty", "<root>")
    elif not isinstance(document, dict):
        report.error("YAML document must be a mapping", "<root>")
    return document


def render_text(path: Path, report: Report) -> str:
    lines = [
        f"Configuration: {path}",
        f"Selected kind: {report.kind or '<unresolved>'}",
        f"Dotpath: {report.dotpath or '<root>'}",
        f"Package validation: {report.package_status}",
    ]
    if report.findings:
        lines.append("Findings:")
        for finding in report.findings:
            where = f" [{finding.location}]" if finding.location else ""
            lines.append(f"- {finding.level.upper()}{where}: {finding.message}")
    else:
        lines.append("Findings: none")
    result = "INVALID" if report.errors else "VALID"
    if report.package_status == "unavailable":
        result = "PARTIAL" if not report.errors else result
    lines.append(f"Result: {result}")
    return "\n".join(lines)


def render_json(path: Path, report: Report) -> str:
    result = "invalid" if report.errors else "valid"
    if report.package_status == "unavailable" and not report.errors:
        result = "partial"
    payload = {
        "configuration": str(path),
        "kind": report.kind,
        "dotpath": report.dotpath,
        "package_validation": report.package_status,
        "result": result,
        "errors": [finding.as_dict() for finding in report.errors],
        "warnings": [finding.as_dict() for finding in report.warnings],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Parse and validate an AlphaFold 3 model/trainer/conductor YAML "
            "mapping without constructing Trainer or starting training."
        )
    )
    parser.add_argument("config", type=Path, help="YAML configuration file to inspect")
    parser.add_argument(
        "--dotpath",
        help="optional dotted mapping path, such as model or training.main",
    )
    parser.add_argument(
        "--kind",
        choices=("auto", "model", "trainer", "conductor"),
        default="auto",
        help="selected mapping kind (default: auto-detect)",
    )
    parser.add_argument(
        "--no-package-validation",
        action="store_true",
        help="skip import of package config models and run only YAML/static checks",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of the human-readable report",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = Report()
    report.dotpath = args.dotpath
    segments = parse_dotpath(args.dotpath, report)
    document = read_yaml(args.config, report)

    selected: Any = None
    if isinstance(document, dict) and not report.errors:
        selected = select_mapping(document, segments, report)
    if isinstance(selected, dict):
        report.kind = detect_kind(selected) if args.kind == "auto" else args.kind
        trainer_parameters: set[str] | None = None
        if not args.no_package_validation:
            trainer_parameters = validate_with_package(report.kind, selected, report)
        else:
            report.package_status = "skipped"
        if report.kind == "trainer":
            validate_trainer_static(selected, report, trainer_parameters=trainer_parameters)
        elif report.kind == "conductor":
            validate_conductor_static(selected, report, trainer_parameters=trainer_parameters)
    elif not report.errors:
        report.error("selected value is not a mapping", "<selection>")

    output = render_json(args.config, report) if args.json else render_text(args.config, report)
    print(output)
    if report.errors:
        return 1
    if report.package_status == "unavailable" and not args.no_package_validation:
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(1)
