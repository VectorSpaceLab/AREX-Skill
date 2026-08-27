#!/usr/bin/env python3
"""Safe PyFlux environment check for the generated DisCo repo skill.

This helper imports the installed PyFlux package, verifies the public model
entry points used by the skill, and optionally checks plotting/data-reader
support packages. It performs no network calls and does not require the original
repository checkout.

Examples:
  python check_pyflux_env.py
  python check_pyflux_env.py --with-optional
  python check_pyflux_env.py --repo-root /path/to/pyflux
"""

from __future__ import print_function

import argparse
import importlib
import inspect
import json
import os
import sys

REQUIRED_MODULES = ["numpy", "pandas", "scipy", "patsy", "numdifftools"]
OPTIONAL_MODULES = ["matplotlib", "seaborn", "pandas_datareader", "Cython"]
PUBLIC_NAMES = [
    "ARIMA", "ARIMAX", "NNAR",
    "GARCH", "EGARCH", "EGARCHM", "EGARCHMReg", "LMEGARCH", "SEGARCH", "SEGARCHM",
    "GAS", "GASX", "GASReg", "GASRank", "GASLLEV", "GASLLT",
    "LLEV", "LLT", "NLLEV", "NLLT", "DAR", "DynReg", "NDynReg", "DynamicGLM", "LocalLevel", "LocalTrend",
    "VAR", "GPNARX",
    "Normal", "Poisson", "t", "Skewt", "Laplace", "Cauchy", "Exponential", "Flat", "TruncatedNormal",
    "SquaredExponential", "OrnsteinUhlenbeck", "ARD", "RationalQuadratic", "Periodic",
    "Aggregate",
]


def import_module(name):
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # pragma: no cover - human-facing diagnostic
        return None, "%s: %s" % (exc.__class__.__name__, exc)


def add_repo_root(repo_root):
    if not repo_root:
        return None
    root = os.path.abspath(repo_root)
    if not os.path.isdir(root):
        raise SystemExit("--repo-root does not exist or is not a directory: %s" % root)
    sys.path.insert(0, root)
    return root


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check importability of a PyFlux environment without network access.")
    parser.add_argument("--repo-root", help="Optional local PyFlux checkout to put on sys.path before import.")
    parser.add_argument("--with-optional", action="store_true", help="Also check plotting/data-reader/source-build helper imports.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    args = parser.parse_args(argv)

    add_repo_root(args.repo_root)

    report = {
        "ok": True,
        "python": "%s.%s.%s" % sys.version_info[:3],
        "required_imports": {},
        "optional_imports": {},
        "pyflux_version": None,
        "missing_public_names": [],
        "signatures": {},
        "messages": [],
    }

    for name in REQUIRED_MODULES:
        module, error = import_module(name)
        report["required_imports"][name] = "ok" if error is None else error
        if error is not None:
            report["ok"] = False

    if args.with_optional:
        for name in OPTIONAL_MODULES:
            module, error = import_module(name)
            report["optional_imports"][name] = "ok" if error is None else error

    pf, error = import_module("pyflux")
    if error is not None:
        report["ok"] = False
        report["messages"].append(
            "pyflux import failed. For source checkouts, ensure Cython extensions are built or install from a compatible wheel/source distribution. Error: %s" % error
        )
    else:
        report["pyflux_version"] = getattr(pf, "__version__", None)
        for name in PUBLIC_NAMES:
            obj = getattr(pf, name, None)
            if obj is None:
                report["missing_public_names"].append(name)
                report["ok"] = False
            else:
                if name in {"ARIMA", "ARIMAX", "GARCH", "GAS", "GASRank", "LLEV", "VAR", "GPNARX", "Aggregate"}:
                    try:
                        report["signatures"][name] = str(inspect.signature(obj))
                    except Exception as exc:
                        report["signatures"][name] = "signature unavailable: %s" % exc

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("PyFlux environment check")
        print("python: %s" % report["python"])
        print("pyflux version: %s" % (report["pyflux_version"] or "unavailable"))
        print("required imports:")
        for name, status in sorted(report["required_imports"].items()):
            print("  - %s: %s" % (name, status))
        if args.with_optional:
            print("optional imports:")
            for name, status in sorted(report["optional_imports"].items()):
                print("  - %s: %s" % (name, status))
        if report["missing_public_names"]:
            print("missing public names: %s" % ", ".join(report["missing_public_names"]))
        if report["signatures"]:
            print("selected signatures:")
            for name, sig in sorted(report["signatures"].items()):
                print("  - %s%s" % (name, sig))
        for message in report["messages"]:
            print("note: %s" % message)
        print("status: %s" % ("ok" if report["ok"] else "failed"))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
