#!/usr/bin/env python3
"""Preflight common MatterGen Hydra overrides without launching a job.

This utility deliberately does not import MatterGen, Hydra, Lightning, or torch.
It validates the shape of common overrides and, when --config-root is supplied,
checks that selected config groups and property-embedding YAML files exist.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


_OVERRIDE_RE = re.compile(
    r"^(?P<prefix>\+\+|\+|~)?"
    r"(?P<key>[A-Za-z_][A-Za-z0-9_.@/\-]*(?:\.[A-Za-z_][A-Za-z0-9_\-]*)*)"
    r"(?P<assignment>=.*)?$"
)
_PROPERTY_EMBEDDING_RE = re.compile(
    r"property_embeddings(?:_adapt)?@[^=]*\.([A-Za-z_][A-Za-z0-9_\-]*)$"
)


@dataclass
class Finding:
    level: str
    message: str


@dataclass
class ParsedOverride:
    raw: str
    key: str
    prefix: str
    value: str | None


def _strip_prefix(key: str) -> str:
    return key.lstrip("+")


def parse_override(raw: str) -> ParsedOverride | None:
    """Parse the small, intentionally conservative subset used by the README."""
    match = _OVERRIDE_RE.match(raw)
    if not match:
        return None
    return ParsedOverride(
        raw=raw,
        key=match.group("key"),
        prefix=match.group("prefix") or "",
        value=match.group("assignment")[1:] if match.group("assignment") else None,
    )


def _literal(value: str) -> Any:
    """Parse a scalar/list value without evaluating arbitrary Python code."""
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value.strip()


def _property_names(value: str) -> list[str]:
    parsed = _literal(value)
    if isinstance(parsed, str):
        return [parsed]
    if isinstance(parsed, (list, tuple)):
        return [str(item) for item in parsed]
    return []


def _check_config_root(
    config_root: Path,
    config_name: str | None,
    data_modules: list[str],
    properties: list[str],
    findings: list[Finding],
) -> None:
    if not config_root.is_dir():
        findings.append(Finding("error", f"config root does not exist or is not a directory: {config_root}"))
        return

    if config_name:
        candidates = [config_root / f"{config_name}.yaml", config_root / config_name / "config.yaml"]
        if not any(path.is_file() for path in candidates):
            findings.append(
                Finding(
                    "error",
                    f"config-name={config_name!r} was not found below {config_root} "
                    f"(looked for {candidates[0].name!r} and a config group)",
                )
            )
        else:
            findings.append(Finding("ok", f"config-name={config_name} exists under {config_root}"))

    for name in data_modules:
        path = config_root / "data_module" / f"{name}.yaml"
        if path.is_file():
            findings.append(Finding("ok", f"data_module={name} -> {path.name}"))
        else:
            findings.append(Finding("error", f"data module config is missing: {path}"))

    property_dir = config_root / "lightning_module" / "diffusion_module" / "model" / "property_embeddings"
    for name in properties:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_\-]*", name):
            findings.append(Finding("error", f"property name is not a simple config-group name: {name!r}"))
            continue
        path = property_dir / f"{name}.yaml"
        if path.is_file():
            findings.append(Finding("ok", f"property embedding={name} -> {path.name}"))
        else:
            findings.append(
                Finding(
                    "error",
                    f"property embedding config is missing: {path}; add a config and source id before training",
                )
            )


def validate(argv: list[str]) -> tuple[list[Finding], dict[str, Any]]:
    parser = argparse.ArgumentParser(
        description="Check common MatterGen Hydra overrides; never launches training."
    )
    parser.add_argument("--config-root", type=Path, help="Optional MatterGen conf directory to inspect")
    parser.add_argument("--config-name", help="Hydra config name, for example csp")
    parser.add_argument("--json", action="store_true", help="Print a JSON report")
    parser.add_argument("overrides", nargs="*", help="Hydra overrides such as data_module=mp_20")
    args = parser.parse_args(argv)

    findings: list[Finding] = []
    parsed: list[ParsedOverride] = []
    for raw in args.overrides:
        item = parse_override(raw)
        if item is None:
            findings.append(
                Finding(
                    "error",
                    f"invalid override {raw!r}; use key=value, +key=value, ++key=value, or ~key",
                )
            )
        else:
            parsed.append(item)

    data_modules: list[str] = []
    properties: list[str] = []
    embedding_properties: list[str] = []
    listed_properties: list[str] = []
    scalar_values: dict[str, str] = {}
    deleted_keys: set[str] = set()
    for item in parsed:
        key = _strip_prefix(item.key)
        if item.value is None:
            if item.prefix != "~":
                findings.append(Finding("error", f"override needs a value: {item.raw!r}"))
            else:
                deleted_keys.add(key)
            continue
        if key == "data_module":
            data_modules.append(str(_literal(item.value)))
        elif key == "data_module.properties":
            listed_properties.extend(_property_names(item.value))
        else:
            property_match = _PROPERTY_EMBEDDING_RE.search(key)
            if property_match:
                embedding_properties.append(str(_literal(item.value)))
            if key in {"trainer.devices", "trainer.accumulate_grad_batches", "trainer.accelerator"}:
                scalar_values[key] = str(_literal(item.value))

    # The README intentionally names each fine-tuned property twice: once in
    # the adapter config-group destination and once in data_module.properties.
    # Treat that as valid, but catch duplicate entries within either side.
    properties = list(dict.fromkeys(embedding_properties + listed_properties))
    embedding_set = set(embedding_properties)
    listed_set = set(listed_properties)
    if embedding_set != listed_set and (embedding_set or listed_set):
        missing_embedding = sorted(listed_set - embedding_set)
        missing_data = sorted(embedding_set - listed_set)
        details: list[str] = []
        if missing_embedding:
            details.append(f"missing adapter embedding override for {missing_embedding}")
        if missing_data:
            details.append(f"missing data_module.properties entry for {missing_data}")
        findings.append(Finding("error", "property wiring mismatch: " + "; ".join(details)))
    for source_name, names in (
        ("adapter property embedding", embedding_properties),
        ("data_module.properties", listed_properties),
    ):
        for name in sorted({p for p in names if names.count(p) > 1}):
            findings.append(Finding("warning", f"{source_name} requests {name!r} more than once"))

    # Base configs default to one device and accumulation one. The README
    # specifically warns that Alex-MP-20's nominal batch is usually too large
    # for one GPU, so provide a recommendation without pretending to know VRAM.
    devices = scalar_values.get("trainer.devices", "1")
    accumulation = scalar_values.get("trainer.accumulate_grad_batches", "1")
    if "alex_mp_20" in data_modules and devices in {"1", "1.0"}:
        try:
            accumulation_value = int(accumulation)
        except ValueError:
            accumulation_value = 1
        if accumulation_value < 4:
            findings.append(
                Finding(
                    "warning",
                    "Alex-MP-20 on one device with accumulation < 4 may OOM; "
                    "consider trainer.accumulate_grad_batches=4 or higher and review before launch",
                )
            )

    if "trainer.accelerator" in scalar_values and scalar_values["trainer.accelerator"] == "mps" and "trainer.strategy" not in deleted_keys:
        findings.append(
            Finding(
                "warning",
                "MPS selected without ~trainer.strategy; README uses both overrides to remove default DDP",
            )
        )

    # A direct --config-name is equivalent to --config-name=<name>.
    config_name = args.config_name
    if config_name and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_\-]*", config_name):
        findings.append(Finding("error", f"invalid config name: {config_name!r}"))

    if not args.overrides and not config_name:
        findings.append(Finding("warning", "no overrides supplied; this is a no-launch check only"))

    if args.config_root:
        _check_config_root(
            args.config_root.expanduser().resolve(), config_name, data_modules, properties, findings
        )
    elif config_name or data_modules or properties:
        findings.append(
            Finding(
                "warning",
                "config-root was not supplied; syntax was checked but config files and property embeddings were not verified",
            )
        )

    if not any(f.level == "error" for f in findings):
        findings.append(Finding("ok", "preflight passed; no training, fine-tuning, or subprocess was launched"))

    report = {
        "config_name": config_name,
        "data_modules": data_modules,
        "properties": properties,
        "overrides": [asdict(item) for item in parsed],
        "findings": [asdict(finding) for finding in findings],
        "launched_training": False,
    }
    return findings, report


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    findings, report = validate(arguments)
    if "--json" in arguments:
        print(json.dumps(report, indent=2))
    else:
        for finding in findings:
            print(f"[{finding.level}] {finding.message}")
    return 2 if any(finding.level == "error" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
