#!/usr/bin/env python3
"""Validate importable AiZynthFinder extension modules without running searches."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class CheckResult:
    ok: bool
    mode: str
    target: str
    symbol: str | None = None
    checks: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def add_check(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            self.ok = False


def import_module(module_name: str, result: CheckResult) -> Any | None:
    try:
        return importlib.import_module(module_name)
    except Exception as err:  # noqa: BLE001 - report import diagnostics, do not mask
        result.errors.append(f"Could not import module '{module_name}': {err.__class__.__name__}: {err}")
        result.ok = False
        return None


def split_target(target: str) -> tuple[str, str | None]:
    if ":" in target:
        module_name, symbol = target.split(":", 1)
        return module_name, symbol or None
    if "." not in target:
        return target, None
    module_name, symbol = target.rsplit(".", 1)
    return module_name, symbol


def load_symbol(target: str, args: argparse.Namespace, result: CheckResult) -> tuple[Any | None, str | None, Any | None]:
    module_name: str
    symbol_name: str | None

    if args.module:
        module_name = args.module
        symbol_name = args.class_name or args.function
    elif args.mode not in MODE_SYMBOL_REQUIRED and not (args.class_name or args.function) and ":" not in target:
        module_name = target
        symbol_name = None
    else:
        module_name, symbol_name = split_target(target)
        if args.class_name or args.function:
            symbol_name = args.class_name or args.function

    module = import_module(module_name, result)
    if module is None:
        return None, symbol_name, None

    if symbol_name is None:
        result.symbol = None
        return module, None, module

    result.symbol = symbol_name
    if not hasattr(module, symbol_name):
        result.errors.append(f"Module '{module_name}' does not expose '{symbol_name}'")
        result.ok = False
        return module, symbol_name, None
    return module, symbol_name, getattr(module, symbol_name)


def signature_of(obj: Any) -> inspect.Signature | None:
    try:
        return inspect.signature(obj)
    except (TypeError, ValueError):
        return None


def positional_bounds(sig: inspect.Signature) -> tuple[int, int | None]:
    required = 0
    positional = 0
    has_varargs = False
    for param in sig.parameters.values():
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            has_varargs = True
            continue
        if param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            positional += 1
            if param.default is inspect.Parameter.empty:
                required += 1
    return required, None if has_varargs else positional


def can_accept_positional(sig: inspect.Signature, count: int) -> bool:
    required, maximum = positional_bounds(sig)
    if count < required:
        return False
    if maximum is None:
        return True
    return count <= maximum


def check_callable(result: CheckResult, obj: Any, name: str, positional_count: int | None = None) -> inspect.Signature | None:
    is_callable = callable(obj)
    result.add_check(f"{name} is callable", is_callable, type(obj).__name__)
    if not is_callable:
        return None
    sig = signature_of(obj)
    if sig is None:
        result.warnings.append(f"Could not inspect signature for {name}")
        return None
    result.add_check(f"{name} signature inspectable", True, str(sig))
    if positional_count is not None:
        result.add_check(
            f"{name} accepts {positional_count} positional args",
            can_accept_positional(sig, positional_count),
            str(sig),
        )
    return sig


def check_module_function(module: Any, function_name: str, positional_count: int, result: CheckResult) -> None:
    if not hasattr(module, function_name):
        result.add_check(f"module exposes {function_name}", False)
        return
    result.add_check(f"module exposes {function_name}", True)
    check_callable(result, getattr(module, function_name), function_name, positional_count)


def try_import(name: str) -> Any | None:
    try:
        module_name, attr = name.rsplit(".", 1)
        module = importlib.import_module(module_name)
        return getattr(module, attr)
    except Exception:  # noqa: BLE001 - optional package may be unavailable
        return None


def safe_issubclass(obj: Any, base: Any) -> bool | None:
    if base is None:
        return None
    if not inspect.isclass(obj):
        return False
    try:
        return issubclass(obj, base)
    except TypeError:
        return False


def check_class_method(result: CheckResult, cls: type, method_name: str, positional_count: int | None = None) -> None:
    has_method = hasattr(cls, method_name)
    result.add_check(f"class defines {method_name}", has_method)
    if not has_method:
        return
    method = getattr(cls, method_name)
    sig = signature_of(method)
    if sig is None:
        result.warnings.append(f"Could not inspect signature for {method_name}")
        return
    result.add_check(f"{method_name} signature inspectable", True, str(sig))
    if positional_count is not None:
        result.add_check(
            f"{method_name} accepts {positional_count} positional args including self",
            can_accept_positional(sig, positional_count),
            str(sig),
        )


def validate_pre_processing(module: Any, _symbol: Any, result: CheckResult) -> None:
    check_module_function(module, "pre_processing", 2, result)
    if hasattr(module, "post_processing") and not hasattr(module, "pre_processing"):
        result.notes.append("Module has post_processing but no pre_processing; use the CLI --post_processing flag for this module.")


def validate_post_processing(module: Any, _symbol: Any, result: CheckResult) -> None:
    check_module_function(module, "post_processing", 1, result)
    if hasattr(module, "pre_processing") and not hasattr(module, "post_processing"):
        result.notes.append("Module has pre_processing but no post_processing; use the CLI --pre_processing flag for this module.")


def validate_smiles_extractor(module: Any, _symbol: Any, result: CheckResult) -> None:
    if not hasattr(module, "extract_smiles"):
        result.add_check("module exposes extract_smiles", False)
        return
    result.add_check("module exposes extract_smiles", True)
    func = getattr(module, "extract_smiles")
    sig = check_callable(result, func, "extract_smiles")
    if sig is None:
        return
    accepts_zero = can_accept_positional(sig, 0)
    accepts_one = can_accept_positional(sig, 1)
    result.add_check("extract_smiles accepts zero or one filename arg", accepts_zero or accepts_one, str(sig))
    if accepts_zero and not accepts_one:
        result.warnings.append("extract_smiles accepts no filename; this can work for static sources but is less useful for file-based stock building.")


def validate_scorer_class(_module: Any, symbol: Any, result: CheckResult) -> None:
    cls = symbol
    result.add_check("symbol is a class", inspect.isclass(cls), type(cls).__name__)
    if not inspect.isclass(cls):
        return
    base = try_import("aizynthfinder.context.scoring.scorers_base.Scorer")
    subclass = safe_issubclass(cls, base)
    if subclass is None:
        result.warnings.append("Could not import AiZynthFinder Scorer base; only structural checks were run.")
    else:
        result.add_check("inherits Scorer", bool(subclass), cls.__mro__[1].__name__ if len(cls.__mro__) > 1 else "")
    check_class_method(result, cls, "_score_node", 2)
    check_class_method(result, cls, "_score_reaction_tree", 2)
    has_repr_or_name = "__repr__" in cls.__dict__ or hasattr(cls, "scorer_name")
    result.add_check("has stable scorer name", has_repr_or_name, "__repr__ or scorer_name")


def validate_stock_object(_module: Any, symbol: Any, result: CheckResult) -> None:
    obj = symbol
    cls = obj if inspect.isclass(obj) else obj.__class__
    result.add_check("symbol is class or object", inspect.isclass(obj) or obj is not None, type(obj).__name__)
    base = try_import("aizynthfinder.context.stock.queries.StockQueryMixin")
    subclass = safe_issubclass(cls, base)
    if subclass is None:
        result.warnings.append("Could not import StockQueryMixin; only structural checks were run.")
    else:
        result.add_check("inherits StockQueryMixin", bool(subclass), cls.__name__)
    check_class_method(result, cls, "__contains__", 2)
    for optional in ("price", "amount", "availability_string", "cached_search", "clear_cache"):
        if hasattr(cls, optional):
            result.add_check(f"optional method {optional} present", True)
        else:
            result.warnings.append(f"Optional stock method '{optional}' is absent; related reporting or stop criteria may not work.")


def validate_expansion_class(_module: Any, symbol: Any, result: CheckResult) -> None:
    cls = symbol
    result.add_check("symbol is a class", inspect.isclass(cls), type(cls).__name__)
    if not inspect.isclass(cls):
        return
    base = try_import("aizynthfinder.context.policy.expansion_strategies.ExpansionStrategy")
    subclass = safe_issubclass(cls, base)
    if subclass is None:
        result.warnings.append("Could not import ExpansionStrategy; only structural checks were run.")
    else:
        result.add_check("inherits ExpansionStrategy", bool(subclass), cls.__name__)
    check_class_method(result, cls, "get_actions", 2)
    if hasattr(cls, "reset_cache"):
        result.add_check("reset_cache available", True)
    else:
        result.warnings.append("reset_cache is absent; use only if no prediction cache is maintained.")
    required = getattr(cls, "_required_kwargs", [])
    result.notes.append(f"Required config kwargs declared by class: {list(required)}")


def validate_search_tree_class(_module: Any, symbol: Any, result: CheckResult) -> None:
    cls = symbol
    result.add_check("symbol is a class", inspect.isclass(cls), type(cls).__name__)
    if not inspect.isclass(cls):
        return
    init_sig = signature_of(cls)
    if init_sig is None:
        result.warnings.append("Could not inspect constructor signature")
    else:
        params = init_sig.parameters
        accepts_config = "config" in params or can_accept_positional(init_sig, 1)
        accepts_root_smiles = "root_smiles" in params or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
        result.add_check("constructor accepts config", accepts_config, str(init_sig))
        result.add_check("constructor accepts root_smiles keyword or kwargs", accepts_root_smiles, str(init_sig))
    check_class_method(result, cls, "one_iteration", 1)
    if hasattr(cls, "routes"):
        result.add_check("routes method available", True)
    else:
        result.warnings.append("No routes method found; ensure TreeAnalysis can extract routes from this tree.")


def validate_retrostar_cost_class(_module: Any, symbol: Any, result: CheckResult) -> None:
    cls = symbol
    result.add_check("symbol is a class", inspect.isclass(cls), type(cls).__name__)
    if not inspect.isclass(cls):
        return
    check_class_method(result, cls, "calculate", 2)


def validate_class(_module: Any, symbol: Any, result: CheckResult) -> None:
    result.add_check("symbol is a class", inspect.isclass(symbol), type(symbol).__name__)


VALIDATORS: dict[str, Callable[[Any, Any, CheckResult], None]] = {
    "class": validate_class,
    "pre-processing": validate_pre_processing,
    "post-processing": validate_post_processing,
    "smiles-extractor": validate_smiles_extractor,
    "scorer-class": validate_scorer_class,
    "stock-object": validate_stock_object,
    "expansion-class": validate_expansion_class,
    "search-tree-class": validate_search_tree_class,
    "retrostar-cost-class": validate_retrostar_cost_class,
}


MODE_SYMBOL_REQUIRED = {
    "class",
    "scorer-class",
    "stock-object",
    "expansion-class",
    "search-tree-class",
    "retrostar-cost-class",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import and inspect custom AiZynthFinder extension modules/classes/functions without running searches or starting services."
    )
    parser.add_argument(
        "--mode",
        choices=sorted(VALIDATORS),
        required=True,
        help="Extension interface to validate.",
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Module, module.ClassName, or module:symbol target to import.",
    )
    parser.add_argument("--module", help="Explicit module name; overrides module parsed from --target.")
    parser.add_argument("--class-name", help="Class symbol to fetch from the module.")
    parser.add_argument("--function", help="Function symbol to fetch from the module for generic class checks.")
    parser.add_argument(
        "--add-path",
        action="append",
        default=[],
        help="Directory to prepend to Python import path before importing the target; repeatable.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser


def human_report(result: CheckResult) -> str:
    lines = [f"mode: {result.mode}", f"target: {result.target}", f"ok: {result.ok}"]
    if result.symbol:
        lines.append(f"symbol: {result.symbol}")
    if result.checks:
        lines.append("checks:")
        for check in result.checks:
            mark = "PASS" if check["ok"] else "FAIL"
            detail = f" - {check['detail']}" if check.get("detail") else ""
            lines.append(f"  [{mark}] {check['name']}{detail}")
    if result.warnings:
        lines.append("warnings:")
        lines.extend(f"  - {warning}" for warning in result.warnings)
    if result.errors:
        lines.append("errors:")
        lines.extend(f"  - {error}" for error in result.errors)
    if result.notes:
        lines.append("notes:")
        lines.extend(f"  - {note}" for note in result.notes)
    return "\n".join(lines)


def apply_add_paths(paths: list[str], result: CheckResult) -> None:
    for raw_path in paths:
        path = Path(raw_path).expanduser().resolve()
        if not path.exists():
            result.warnings.append(f"Import path does not exist and was not added: {raw_path}")
            continue
        sys.path.insert(0, str(path))
        result.notes.append(f"Added import path: {path}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = CheckResult(ok=True, mode=args.mode, target=args.target)
    apply_add_paths(args.add_path or [], result)

    module, symbol_name, symbol = load_symbol(args.target, args, result)
    if module is not None and args.mode in MODE_SYMBOL_REQUIRED and symbol is module and symbol_name is None:
        result.errors.append(f"Mode '{args.mode}' requires a class/object symbol; pass --target module.ClassName or --class-name.")
        result.ok = False
    if result.ok or module is not None:
        validator = VALIDATORS[args.mode]
        try:
            validator(module, symbol, result)
        except Exception as err:  # noqa: BLE001 - report checker bug/inspection issue clearly
            result.errors.append(f"Validation failed unexpectedly: {err.__class__.__name__}: {err}")
            result.ok = False

    payload = {
        "ok": result.ok,
        "mode": result.mode,
        "target": result.target,
        "symbol": result.symbol,
        "checks": result.checks,
        "warnings": result.warnings,
        "errors": result.errors,
        "notes": result.notes,
    }
    if args.json:
        print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=bool(args.pretty)))
    else:
        print(human_report(result))
        print("\nJSON:")
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
