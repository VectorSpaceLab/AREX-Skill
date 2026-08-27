#!/usr/bin/env python3
"""Validate that a Python object exposes MTEB-like model protocol methods.

This helper is intentionally lightweight: it imports a local object and inspects
method signatures without downloading datasets, loading remote models, or running
an MTEB evaluation.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import sys
from dataclasses import dataclass
from types import ModuleType
from typing import Any


@dataclass
class CheckResult:
    label: str
    ok: bool
    detail: str


def _load_target(spec: str) -> Any:
    if ":" in spec:
        module_name, object_path = spec.split(":", 1)
    else:
        module_name, object_path = spec, ""

    module = importlib.import_module(module_name)
    target: Any = module
    if object_path:
        for part in object_path.split("."):
            target = getattr(target, part)
    return target


def _callable_attr(target: Any, name: str) -> Any | None:
    attr = getattr(target, name, None)
    return attr if callable(attr) else None


def _signature(callable_obj: Any) -> inspect.Signature | None:
    try:
        return inspect.signature(callable_obj)
    except (TypeError, ValueError):
        return None


def _has_parameter(sig: inspect.Signature | None, name: str) -> bool:
    if sig is None:
        return False
    return name in sig.parameters


def _has_var_keyword(sig: inspect.Signature | None) -> bool:
    if sig is None:
        return False
    return any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())


def _required_keyword_report(sig: inspect.Signature | None, names: list[str]) -> tuple[bool, str]:
    if sig is None:
        return False, "signature unavailable"
    missing = [name for name in names if name not in sig.parameters]
    has_kwargs = _has_var_keyword(sig)
    if not missing:
        return True, "required parameters present"
    if has_kwargs:
        return True, f"explicit parameters missing {missing}, but **kwargs can accept them"
    return False, f"missing parameters {missing} and no **kwargs"


def _constructor_report(target: Any) -> CheckResult:
    constructor = target if inspect.isclass(target) else getattr(target, "__init__", None)
    sig = _signature(constructor)
    if sig is None:
        return CheckResult("constructor", False, "constructor signature unavailable")
    expected = ["model_name", "revision", "device"]
    present = [name for name in expected if name in sig.parameters]
    if len(present) == len(expected) or _has_var_keyword(sig):
        return CheckResult(
            "constructor",
            True,
            "compatible with model_name/revision/device or accepts **kwargs",
        )
    return CheckResult(
        "constructor",
        False,
        f"not CLI/ModelMeta-loader shaped; present={present}, expected={expected} or **kwargs",
    )


def _check_encoder(target: Any) -> list[CheckResult]:
    encode = _callable_attr(target, "encode")
    if encode is None:
        return [CheckResult("encoder.encode", False, "missing callable encode")]
    sig = _signature(encode)
    ok, detail = _required_keyword_report(
        sig, ["task_metadata", "hf_split", "hf_subset", "prompt_type"]
    )
    results = [CheckResult("encoder.encode", ok, detail)]
    for method in ["similarity", "similarity_pairwise"]:
        exists = _callable_attr(target, method) is not None
        results.append(
            CheckResult(
                f"encoder.{method}",
                exists,
                "present" if exists else "missing; MTEB search wrappers may require this",
            )
        )
    return results


def _check_cross_encoder(target: Any) -> list[CheckResult]:
    predict = _callable_attr(target, "predict")
    if predict is None:
        return [CheckResult("cross_encoder.predict", False, "missing callable predict")]
    sig = _signature(predict)
    ok, detail = _required_keyword_report(
        sig, ["inputs1", "inputs2", "task_metadata", "hf_split", "hf_subset", "prompt_type"]
    )
    return [CheckResult("cross_encoder.predict", ok, detail)]


def _check_search(target: Any) -> list[CheckResult]:
    results: list[CheckResult] = []
    index = _callable_attr(target, "index")
    search = _callable_attr(target, "search")
    if index is None:
        results.append(CheckResult("search.index", False, "missing callable index"))
    else:
        ok, detail = _required_keyword_report(
            _signature(index), ["corpus", "task_metadata", "hf_split", "hf_subset", "encode_kwargs", "num_proc"]
        )
        results.append(CheckResult("search.index", ok, detail))
    if search is None:
        results.append(CheckResult("search.search", False, "missing callable search"))
    else:
        ok, detail = _required_keyword_report(
            _signature(search),
            [
                "queries",
                "task_metadata",
                "hf_split",
                "hf_subset",
                "top_k",
                "encode_kwargs",
                "top_ranked",
                "num_proc",
            ],
        )
        results.append(CheckResult("search.search", ok, detail))
    return results


def _format_signature(target: Any, method: str) -> str:
    func = _callable_attr(target, method)
    if func is None:
        return f"{method}: <missing>"
    sig = _signature(func)
    return f"{method}{sig if sig is not None else '(<signature unavailable>)'}"


def _is_module(target: Any) -> bool:
    return isinstance(target, ModuleType)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a Python object for MTEB Encoder/CrossEncoder/Search protocol compatibility."
    )
    parser.add_argument(
        "target",
        help="Import target as module or module:object.path, for example my_pkg.my_mod:MyEncoder",
    )
    parser.add_argument(
        "--skip-constructor",
        action="store_true",
        help="Do not warn about constructor compatibility with ModelMeta/CLI loading.",
    )
    args = parser.parse_args(argv)

    try:
        target = _load_target(args.target)
    except Exception as exc:  # noqa: BLE001
        print(f"IMPORT FAILED: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 2

    print(f"Loaded target: {args.target}")
    print(f"Target type: {type(target).__name__}")
    if _is_module(target):
        print("NOTE: target is a module; pass module:object_name to validate a class or instance.")

    print("\nSignatures:")
    for method in ["__init__", "encode", "predict", "index", "search", "similarity", "similarity_pairwise"]:
        if method == "__init__":
            sig = _signature(target if inspect.isclass(target) else getattr(target, "__init__", None))
            print(f"__init__{sig if sig is not None else '(<signature unavailable>)'}")
        else:
            print(_format_signature(target, method))

    results: list[CheckResult] = []
    if not args.skip_constructor and not _is_module(target):
        results.append(_constructor_report(target))
    results.extend(_check_encoder(target))
    results.extend(_check_cross_encoder(target))
    results.extend(_check_search(target))

    print("\nChecks:")
    for result in results:
        status = "OK" if result.ok else "WARN"
        print(f"[{status}] {result.label}: {result.detail}")

    encoder_ok = any(r.label == "encoder.encode" and r.ok for r in results)
    cross_ok = any(r.label == "cross_encoder.predict" and r.ok for r in results)
    search_ok = all(
        any(r.label == label and r.ok for r in results)
        for label in ["search.index", "search.search"]
    )

    compatible = []
    if encoder_ok:
        compatible.append("encoder-like")
    if cross_ok:
        compatible.append("cross-encoder-like")
    if search_ok:
        compatible.append("search-like")

    print("\nProtocol summary:")
    if compatible:
        print("Compatible signals: " + ", ".join(compatible))
        print("Next step: run a tiny public MTEB task to verify output shapes and numeric behavior.")
        return 0

    print("No complete MTEB protocol detected. Fix method names/signatures before evaluation.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
