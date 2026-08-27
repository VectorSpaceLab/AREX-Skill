#!/usr/bin/env python3
"""Headless Mesa visualization stack probe.

The script imports the installed Mesa visualization API and selected optional
packages, reports JSON, and exits non-zero only when required checks fail.  It
intentionally does not start a Solara server, open a browser, read example
files, or mutate the current project.
"""

from __future__ import annotations

import argparse
import dataclasses
import importlib
import inspect
import json
import platform
import sys
from collections.abc import Iterable
from importlib import metadata
from typing import Any

OPTIONAL_PACKAGES = ("solara", "matplotlib", "altair", "networkx")
VIZ_PACKAGES = ("solara", "matplotlib", "altair")
NETWORK_PACKAGES = ("networkx",)

EXPECTED_SIGNATURES = {
    "SolaraViz": ("model", "renderer", "components", "play_interval", "render_interval", "model_params", "name", "use_threads"),
    "SpaceRenderer": ("model", "backend"),
    "make_space_component": ("agent_portrayal", "property_layer_portrayal", "post_process", "backend"),
    "make_plot_component": ("measure", "post_process", "backend", "page"),
}

EXPECTED_AGENT_FIELDS = (
    "x",
    "y",
    "color",
    "marker",
    "size",
    "zorder",
    "alpha",
    "edgecolors",
    "linewidths",
    "tooltip",
)
EXPECTED_PROPERTY_FIELDS = ("colormap", "color", "alpha", "colorbar", "vmin", "vmax")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Probe an installed Mesa visualization stack and emit JSON without "
            "launching a server or browser."
        )
    )
    parser.add_argument(
        "--imports",
        nargs="*",
        default=[],
        metavar="PACKAGE",
        help=(
            "Optional packages to import-check. Use any of: solara, matplotlib, "
            "altair, networkx, viz, network, all."
        ),
    )
    parser.add_argument(
        "--require-viz",
        action="store_true",
        help="Require Mesa visualization extras: solara, matplotlib, and altair.",
    )
    parser.add_argument(
        "--require-network",
        action="store_true",
        help="Require network visualization readiness, including networkx.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on requested optional import failures or signature mismatches.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args()


def expand_requested_imports(names: Iterable[str]) -> list[str]:
    requested: list[str] = []
    aliases = {
        "viz": VIZ_PACKAGES,
        "network": NETWORK_PACKAGES,
        "all": OPTIONAL_PACKAGES,
    }
    for raw_name in names:
        name = raw_name.strip().lower()
        expanded = aliases.get(name, (name,))
        for package in expanded:
            if package not in OPTIONAL_PACKAGES:
                raise SystemExit(f"Unsupported --imports value: {raw_name!r}")
            if package not in requested:
                requested.append(package)
    return requested


def package_version(distribution: str, module: Any | None = None) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        version = getattr(module, "__version__", None) if module is not None else None
        return str(version) if version is not None else None


def short_error(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


def import_check(module_name: str, distribution: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False, "module": module_name}
    try:
        module = importlib.import_module(module_name)
    except BaseException as exc:  # noqa: BLE001 - report import-time optional dependency failures as data.
        result["error"] = short_error(exc)
        return result

    result["ok"] = True
    result["version"] = package_version(distribution or module_name, module)
    return result


def get_object(module: Any, attr: str) -> tuple[Any | None, dict[str, Any]]:
    try:
        obj = getattr(module, attr)
    except AttributeError as exc:
        return None, {"ok": False, "error": short_error(exc)}
    return obj, {"ok": True, "type": type(obj).__name__}


def signature_check(obj: Any, expected_params: Iterable[str]) -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False}
    try:
        signature = inspect.signature(obj)
    except BaseException as exc:  # noqa: BLE001 - decorated components may fail signature introspection.
        result["error"] = short_error(exc)
        return result

    params = list(signature.parameters)
    missing = [name for name in expected_params if name not in params]
    result.update(
        {
            "ok": not missing,
            "signature": str(signature),
            "parameters": params,
            "missing_parameters": missing,
        }
    )
    return result


def dataclass_fields_check(cls: Any, expected_fields: Iterable[str]) -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False}
    if not dataclasses.is_dataclass(cls):
        result["error"] = "class is not a dataclass"
        return result
    fields = [field.name for field in dataclasses.fields(cls)]
    missing = [field for field in expected_fields if field not in fields]
    result.update({"ok": not missing, "fields": fields, "missing_fields": missing})
    return result


def style_runtime_checks(agent_cls: Any, property_cls: Any) -> dict[str, Any]:
    checks: dict[str, Any] = {}

    try:
        style = agent_cls(color="tab:blue", size=10)
        style.update(("color", "tab:orange"), ("size", 12))
        checks["agent_style_update"] = {
            "ok": getattr(style, "color", None) == "tab:orange" and getattr(style, "size", None) == 12
        }
    except BaseException as exc:  # noqa: BLE001 - convert validation failures to JSON.
        checks["agent_style_update"] = {"ok": False, "error": short_error(exc)}

    try:
        agent_cls(size=-1)
    except ValueError:
        checks["agent_negative_size_rejected"] = {"ok": True}
    except BaseException as exc:  # noqa: BLE001
        checks["agent_negative_size_rejected"] = {"ok": False, "error": short_error(exc)}
    else:
        checks["agent_negative_size_rejected"] = {"ok": False, "error": "negative size was accepted"}

    try:
        property_cls(color="red")
        property_cls(colormap="viridis")
        checks["property_layer_valid_styles"] = {"ok": True}
    except BaseException as exc:  # noqa: BLE001
        checks["property_layer_valid_styles"] = {"ok": False, "error": short_error(exc)}

    try:
        property_cls(color="red", colormap="viridis")
    except ValueError:
        checks["property_layer_conflict_rejected"] = {"ok": True}
    except BaseException as exc:  # noqa: BLE001
        checks["property_layer_conflict_rejected"] = {"ok": False, "error": short_error(exc)}
    else:
        checks["property_layer_conflict_rejected"] = {"ok": False, "error": "color/colormap conflict was accepted"}

    return checks


def all_nested_ok(value: Any) -> bool:
    if isinstance(value, dict):
        if value.get("ok") is False:
            return False
        return all(all_nested_ok(v) for v in value.values())
    if isinstance(value, list):
        return all(all_nested_ok(v) for v in value)
    return True


def append_unique(items: list[str], message: str) -> None:
    if message not in items:
        items.append(message)


def main() -> int:
    args = parse_args()
    requested_imports = expand_requested_imports(args.imports)
    for package in VIZ_PACKAGES if args.require_viz else ():
        if package not in requested_imports:
            requested_imports.append(package)
    for package in NETWORK_PACKAGES if args.require_network else ():
        if package not in requested_imports:
            requested_imports.append(package)

    report: dict[str, Any] = {
        "status": "ok",
        "python": {"version": platform.python_version()},
        "mesa": {},
        "core": {},
        "optional_imports": {},
        "network": {},
        "actions": [],
        "notes": ["No Solara server or browser was launched."],
    }

    required_failures: list[str] = []
    strict_failures: list[str] = []

    mesa_check = import_check("mesa")
    report["mesa"].update(mesa_check)
    if not mesa_check["ok"]:
        append_unique(report["actions"], "Install Mesa in this Python environment, then rerun the visualization stack probe.")
        required_failures.append("mesa import failed")

    for package in requested_imports:
        check = import_check(package)
        report["optional_imports"][package] = check
        if not check["ok"]:
            if package in VIZ_PACKAGES:
                append_unique(
                    report["actions"],
                    "Install visualization extras in the active environment: python -m pip install 'mesa[viz]'.",
                )
                if args.require_viz:
                    required_failures.append(f"required visualization package missing: {package}")
            elif package == "networkx":
                append_unique(
                    report["actions"],
                    "Install network extras in the active environment: python -m pip install 'mesa[network]' (or 'mesa[rec]' for network plus visualization extras).",
                )
                if args.require_network:
                    required_failures.append("required network package missing: networkx")
            if args.strict:
                strict_failures.append(f"requested optional package missing: {package}")

    viz_module = None
    if mesa_check["ok"]:
        try:
            viz_module = importlib.import_module("mesa.visualization")
            report["core"]["mesa_visualization"] = {"ok": True}
        except BaseException as exc:  # noqa: BLE001
            report["core"]["mesa_visualization"] = {"ok": False, "error": short_error(exc)}
            append_unique(
                report["actions"],
                "Install visualization extras in the active environment: python -m pip install 'mesa[viz]'.",
            )
            if args.require_viz or args.require_network:
                required_failures.append("mesa.visualization import failed")
            if args.strict:
                strict_failures.append("mesa.visualization import failed")

    imported_objects: dict[str, Any] = {}
    if viz_module is not None:
        report["core"]["imports"] = {}
        for attr in ("SolaraViz", "SpaceRenderer", "make_space_component", "make_plot_component"):
            obj, check = get_object(viz_module, attr)
            report["core"]["imports"][attr] = check
            if obj is not None:
                imported_objects[attr] = obj

        try:
            components_module = importlib.import_module("mesa.visualization.components")
            report["core"].setdefault("imports", {})["mesa.visualization.components"] = {"ok": True}
            for attr in ("AgentPortrayalStyle", "PropertyLayerStyle"):
                obj, check = get_object(components_module, attr)
                report["core"]["imports"][attr] = check
                if obj is not None:
                    imported_objects[attr] = obj
        except BaseException as exc:  # noqa: BLE001
            report["core"].setdefault("imports", {})["mesa.visualization.components"] = {
                "ok": False,
                "error": short_error(exc),
            }

        report["core"]["signatures"] = {}
        for attr, expected in EXPECTED_SIGNATURES.items():
            if attr in imported_objects:
                report["core"]["signatures"][attr] = signature_check(imported_objects[attr], expected)
            else:
                report["core"]["signatures"][attr] = {"ok": False, "error": "object was not imported"}

        report["core"]["portrayal_styles"] = {}
        if "AgentPortrayalStyle" in imported_objects:
            report["core"]["portrayal_styles"]["AgentPortrayalStyle"] = dataclass_fields_check(
                imported_objects["AgentPortrayalStyle"], EXPECTED_AGENT_FIELDS
            )
        else:
            report["core"]["portrayal_styles"]["AgentPortrayalStyle"] = {"ok": False, "error": "class was not imported"}
        if "PropertyLayerStyle" in imported_objects:
            report["core"]["portrayal_styles"]["PropertyLayerStyle"] = dataclass_fields_check(
                imported_objects["PropertyLayerStyle"], EXPECTED_PROPERTY_FIELDS
            )
        else:
            report["core"]["portrayal_styles"]["PropertyLayerStyle"] = {"ok": False, "error": "class was not imported"}

        if "AgentPortrayalStyle" in imported_objects and "PropertyLayerStyle" in imported_objects:
            report["core"]["style_runtime_checks"] = style_runtime_checks(
                imported_objects["AgentPortrayalStyle"], imported_objects["PropertyLayerStyle"]
            )

    core_ok = all_nested_ok(report["core"])
    if not core_ok:
        append_unique(
            report["actions"],
            "Use a Mesa version with the current visualization API and install missing extras before debugging dashboard code.",
        )
        if args.require_viz:
            required_failures.append("visualization API import/signature check failed")
        if args.strict:
            strict_failures.append("visualization API import/signature check failed")

    if args.require_network and mesa_check["ok"]:
        try:
            discrete_space = importlib.import_module("mesa.discrete_space")
            network_cls = getattr(discrete_space, "Network")
            report["network"]["mesa_discrete_space_network"] = {"ok": True, "type": type(network_cls).__name__}
        except BaseException as exc:  # noqa: BLE001
            report["network"]["mesa_discrete_space_network"] = {"ok": False, "error": short_error(exc)}
            required_failures.append("Mesa Network space import failed")

        if viz_module is not None:
            try:
                drawers = importlib.import_module("mesa.visualization.space_drawers")
                network_drawer = getattr(drawers, "NetworkSpaceDrawer")
                report["network"]["network_space_drawer"] = {"ok": True, "type": type(network_drawer).__name__}
            except BaseException as exc:  # noqa: BLE001
                report["network"]["network_space_drawer"] = {"ok": False, "error": short_error(exc)}
                required_failures.append("Mesa NetworkSpaceDrawer import failed")
        else:
            report["network"]["network_space_drawer"] = {
                "ok": False,
                "error": "mesa.visualization was not imported",
            }
            required_failures.append("network visualization drawer could not be checked")

    if required_failures or strict_failures:
        report["status"] = "failed"
    elif not mesa_check["ok"] or not core_ok or any(not item.get("ok", False) for item in report["optional_imports"].values()):
        report["status"] = "degraded"
    else:
        report["status"] = "ok"

    if required_failures:
        report["required_failures"] = sorted(set(required_failures))
    if strict_failures:
        report["strict_failures"] = sorted(set(strict_failures))

    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 1 if required_failures or strict_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
