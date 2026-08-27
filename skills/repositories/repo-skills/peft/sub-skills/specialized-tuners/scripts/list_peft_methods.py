#!/usr/bin/env python3
"""List PEFT method enum values and public Config classes.

This helper intentionally depends only on the installed `peft` package. It is
useful for checking whether a specialized tuner is available in the active
Python environment and how its public config class is spelled.
"""

import argparse
import inspect
from typing import Any, Iterable


def _matches_filter(values: Iterable[str], filter_text: str | None) -> bool:
    if not filter_text:
        return True
    needle = filter_text.lower()
    return any(needle in value.lower() for value in values)


def load_peft() -> tuple[Any, type[Any], type[Any]]:
    try:
        import peft
        from peft import PeftConfig
        from peft.utils import PeftType
    except ModuleNotFoundError as exc:
        missing = exc.name or "a PEFT dependency"
        raise SystemExit(
            f"Cannot import PEFT because {missing!r} is not installed. Install PEFT in this Python environment first."
        ) from exc

    return peft, PeftConfig, PeftType


def collect_config_classes(peft_module: Any, peft_config_cls: type[Any]) -> list[tuple[str, type[Any]]]:
    classes: list[tuple[str, type[Any]]] = []
    for name in dir(peft_module):
        obj = getattr(peft_module, name)
        if not inspect.isclass(obj):
            continue
        if not name.endswith("Config"):
            continue
        try:
            is_peft_config = issubclass(obj, peft_config_cls)
        except TypeError:
            continue
        if is_peft_config and obj is not peft_config_cls:
            classes.append((name, obj))
    return sorted(classes, key=lambda item: item[0].lower())


def config_peft_type(config_cls: type[Any]) -> str:
    try:
        signature = inspect.signature(config_cls)
    except (TypeError, ValueError):
        return "unknown"

    kwargs = {}
    for parameter_name, parameter in signature.parameters.items():
        if parameter_name == "self":
            continue
        if parameter.default is inspect.Parameter.empty:
            return "requires-arguments"

    try:
        instance = config_cls(**kwargs)
    except Exception as exc:  # noqa: BLE001 - this is a diagnostic helper
        return f"unavailable: {exc.__class__.__name__}"

    peft_type = getattr(instance, "peft_type", None)
    return getattr(peft_type, "value", str(peft_type))


def main() -> int:
    parser = argparse.ArgumentParser(description="List installed PEFT method enum values and public Config classes.")
    parser.add_argument("--filter", help="Case-insensitive method or class substring to show.")
    parser.add_argument("--configs-only", action="store_true", help="Only print public PEFT Config classes.")
    parser.add_argument("--types-only", action="store_true", help="Only print PeftType enum values.")
    args = parser.parse_args()

    if args.configs_only and args.types_only:
        parser.error("--configs-only and --types-only are mutually exclusive")

    peft_module, peft_config_cls, peft_type_cls = load_peft()

    if not args.configs_only:
        print("PeftType values:")
        for peft_type in peft_type_cls:
            if _matches_filter((peft_type.name, peft_type.value), args.filter):
                print(f"  {peft_type.name:18s} {peft_type.value}")

    if not args.types_only:
        if not args.configs_only:
            print()
        print("Public Config classes:")
        for class_name, config_cls in collect_config_classes(peft_module, peft_config_cls):
            peft_type = config_peft_type(config_cls)
            if _matches_filter((class_name, peft_type), args.filter):
                print(f"  {class_name:28s} peft_type={peft_type}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
