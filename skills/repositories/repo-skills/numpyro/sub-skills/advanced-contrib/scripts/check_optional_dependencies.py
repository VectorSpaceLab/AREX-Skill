#!/usr/bin/env python3
"""Probe optional NumPyro contrib dependencies and print JSON status.

The script imports core NumPyro/JAX first, then probes optional contrib-related
modules. Missing optional dependencies are reported but do not cause a non-zero
exit unless requested with --require. No network, credentials, datasets, or
training are used.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import sys
from types import ModuleType
from typing import Any


PROBES: dict[str, dict[str, Any]] = {
    "core": {
        "imports": ["jax", "numpyro"],
        "required_for": "all NumPyro workflows",
    },
    "funsor": {
        "imports": ["funsor", "numpyro.contrib.funsor"],
        "required_for": "config_enumerate, infer_discrete, markov, Funsor log-density utilities",
    },
    "hsgp": {
        "imports": [
            "numpyro.contrib.hsgp.approximation",
            "numpyro.contrib.hsgp.laplacian",
            "numpyro.contrib.hsgp.spectral_densities",
        ],
        "required_for": "HSGP approximation and basis helpers",
    },
    "hsgp_tfp": {
        "imports": ["tensorflow_probability.substrates.jax"],
        "required_for": "HSGP periodic and rational-quadratic Bessel helpers",
    },
    "nested_sampling": {
        "imports": [
            "jaxns",
            "tensorflow_probability.substrates.jax",
            "numpyro.contrib.nested_sampling",
        ],
        "required_for": "numpyro.contrib.nested_sampling.NestedSampler",
    },
    "einstein": {
        "imports": ["numpyro.contrib.einstein"],
        "required_for": "SteinVI, SVGD, ASVGD, Stein kernels, MixtureGuidePredictive",
    },
    "module_flax": {
        "imports": ["flax", "numpyro.contrib.module"],
        "required_for": "flax_module and random_flax_module",
    },
    "module_nnx": {
        "imports": ["flax", "flax.nnx", "numpyro.contrib.module"],
        "required_for": "nnx_module and random_nnx_module",
    },
    "module_equinox": {
        "imports": ["equinox", "numpyro.contrib.module"],
        "required_for": "eqx_module and random_eqx_module",
    },
    "tfp": {
        "imports": [
            "tensorflow_probability.substrates.jax",
            "numpyro.contrib.tfp.distributions",
            "numpyro.contrib.tfp.mcmc",
        ],
        "required_for": "TFP JAX distributions, bijectors, and TFP MCMC wrappers",
    },
    "stochastic_support": {
        "imports": [
            "numpyro.contrib.stochastic_support.dcc",
            "numpyro.contrib.stochastic_support.sdvi",
        ],
        "required_for": "DCC and SDVI stochastic-support inference",
    },
    "optax": {
        "imports": ["optax"],
        "required_for": "optional Optax optimizers used by some examples",
    },
    "example_plotting_data": {
        "imports": ["matplotlib", "pandas", "sklearn"],
        "required_for": "example-only plotting, tabular data, and preprocessing",
    },
    "rendering": {
        "imports": ["graphviz"],
        "required_for": "optional rendering side effects",
    },
}


PACKAGE_VERSION_MODULES = {
    "tensorflow_probability.substrates.jax": "tensorflow_probability",
    "sklearn": "sklearn",
}


def _clean_message(message: str) -> str:
    """Remove environment-specific absolute path fragments from an error message."""
    text = str(message).splitlines()[0] if str(message) else ""
    replacements = [
        (os.getcwd(), "<cwd>"),
        (str(Path.home()), "<home>"),
        (sys.prefix, "<sys-prefix>"),
        (sys.executable, "<python>"),
    ]
    for old, new in replacements:
        if old and old not in {"/", "."}:
            text = text.replace(old, new)
    return text


def _module_version(module_name: str, module: ModuleType) -> str | None:
    version = getattr(module, "__version__", None)
    if isinstance(version, str):
        return version
    root_name = PACKAGE_VERSION_MODULES.get(module_name, module_name.split(".")[0])
    try:
        from importlib import metadata

        return metadata.version(root_name)
    except Exception:
        return None


def _import_one(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        return {
            "module": module_name,
            "status": "missing",
            "error_type": exc.__class__.__name__,
            "message": _clean_message(exc),
        }
    except Exception as exc:  # Import-time AttributeError/version conflicts/etc.
        return {
            "module": module_name,
            "status": "error",
            "error_type": exc.__class__.__name__,
            "message": _clean_message(exc),
        }
    return {
        "module": module_name,
        "status": "ok",
        "version": _module_version(module_name, module),
    }


def probe(name: str) -> dict[str, Any]:
    spec = PROBES[name]
    imports = [_import_one(module_name) for module_name in spec["imports"]]
    statuses = {item["status"] for item in imports}
    if "error" in statuses:
        status = "error"
    elif "missing" in statuses:
        status = "missing"
    else:
        status = "ok"
    return {
        "status": status,
        "ok": status == "ok",
        "required_for": spec["required_for"],
        "imports": imports,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe optional NumPyro contrib dependencies without failing on missing optional packages.",
    )
    parser.add_argument(
        "--require",
        nargs="*",
        default=[],
        metavar="KEY",
        help=(
            "Capability keys that must be importable. Use 'all' to require every "
            "probe. Missing required capabilities make the script exit non-zero."
        ),
    )
    parser.add_argument(
        "--only",
        nargs="*",
        default=[],
        metavar="KEY",
        help="Limit JSON output to these capability keys. Use 'all' or omit for every probe.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON with indentation.",
    )
    parser.add_argument(
        "--list-keys",
        action="store_true",
        help="List known capability keys and exit.",
    )
    return parser.parse_args(argv)


def expand_keys(raw_keys: list[str], *, default_all: bool) -> list[str]:
    if not raw_keys:
        return list(PROBES) if default_all else []
    keys: list[str] = []
    for key in raw_keys:
        if key == "all":
            keys.extend(PROBES)
        else:
            keys.append(key)
    unknown = sorted(set(keys) - set(PROBES))
    if unknown:
        known = ", ".join(PROBES)
        raise SystemExit(f"Unknown probe key(s): {', '.join(unknown)}. Known keys: {known}")
    return list(dict.fromkeys(keys))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.list_keys:
        print("\n".join(PROBES))
        return 0

    output_keys = expand_keys(args.only, default_all=True)
    required_keys = expand_keys(args.require, default_all=False)

    results = {key: probe(key) for key in output_keys}
    missing_required = [key for key in required_keys if probe(key)["status"] != "ok"]

    core_status = results.get("core") or probe("core")
    payload = {
        "ok": not missing_required and core_status["status"] == "ok",
        "required": required_keys,
        "missing_required": missing_required,
        "probes": results,
    }
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))

    if core_status["status"] != "ok":
        return 1
    if missing_required:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
