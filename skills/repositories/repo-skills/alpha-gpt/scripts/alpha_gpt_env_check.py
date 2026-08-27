#!/usr/bin/env python3
"""Offline AlphaGPT environment and artifact preflight.

This helper checks imports, public environment-variable presence, and optional
local artifacts without contacting Birdeye, Postgres, Solana RPC, Jupiter, or
Streamlit servers. It never prints secret values.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Iterable

SCOPES = ("data", "factor", "live", "dashboard", "all")

IMPORTS = {
    "data": [
        "data_pipeline.config",
        "data_pipeline.db_manager",
        "data_pipeline.data_manager",
        "data_pipeline.providers.birdeye",
        "data_pipeline.providers.dexscreener",
    ],
    "factor": [
        "model_core.vocab",
        "model_core.ops",
        "model_core.vm",
        "model_core.factors",
        "model_core.alphagpt",
        "model_core.backtest",
        "model_core.engine",
    ],
    "live": [
        "execution.config",
        "execution.jupiter",
        "execution.rpc_handler",
        "execution.trader",
        "execution.utils",
        "strategy_manager.config",
        "strategy_manager.portfolio",
        "strategy_manager.risk",
        "strategy_manager.runner",
    ],
    "dashboard": [
        "dashboard.data_service",
        "dashboard.visualizer",
    ],
}

ENV_KEYS = {
    "data": ["BIRDEYE_API_KEY", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"],
    "live": ["QUICKNODE_RPC_URL", "SOLANA_PRIVATE_KEY"],
    "dashboard": ["QUICKNODE_RPC_URL", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME"],
}

SECRET_KEYS = {"BIRDEYE_API_KEY", "SOLANA_PRIVATE_KEY", "DB_PASSWORD"}
PLACEHOLDER_VALUES = {"", "填入RPC地址", "YOUR_RPC_URL", "CHANGE_ME", "password"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run offline AlphaGPT import/env/artifact checks without network or DB/RPC access."
    )
    parser.add_argument("--repo-root", help="optional AlphaGPT checkout root to add to sys.path")
    parser.add_argument("--scope", choices=SCOPES, default="all", help="workflow scope to check")
    parser.add_argument("--env-file", help="optional .env-style file to read before process environment")
    parser.add_argument("--strategy-json", help="optional best_meme_strategy.json path to validate")
    parser.add_argument("--portfolio-json", help="optional portfolio_state.json path to validate")
    parser.add_argument("--skip-imports", action="store_true", help="skip Python module import checks")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    return parser


def selected_scopes(scope: str) -> list[str]:
    return ["data", "factor", "live", "dashboard"] if scope == "all" else [scope]


def read_env_file(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        raise FileNotFoundError(str(path))
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def env_value(key: str, file_env: dict[str, str]) -> str | None:
    return os.environ.get(key, file_env.get(key))


def summarize_env(key: str, value: str | None) -> tuple[str, str]:
    if value is None:
        return "missing", "not set"
    if value in PLACEHOLDER_VALUES:
        return "placeholder", "set to a placeholder/default"
    if key in SECRET_KEYS:
        return "present", "set (value hidden)"
    return "present", value


def parse_formula(value: object) -> list[int] | None:
    formula = value.get("formula") if isinstance(value, dict) else value
    if not isinstance(formula, list):
        return None
    if not all(isinstance(item, int) for item in formula):
        return None
    return formula


def validate_strategy(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"strategy JSON cannot be parsed: {exc}"], []
    formula = parse_formula(data)
    if formula is None:
        errors.append("strategy JSON must be a token list or an object with a formula list")
        return errors, warnings
    if len(formula) > 12:
        warnings.append("formula length exceeds default MAX_FORMULA_LEN=12")
    bad = [token for token in formula if token < 0 or token > 17]
    if bad:
        errors.append(f"formula contains token ids outside 0..17: {bad}")
    return errors, warnings


def validate_portfolio(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    required = {"token_address", "symbol", "entry_price", "entry_time", "amount_held", "initial_cost_sol", "highest_price"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"portfolio JSON cannot be parsed: {exc}"], []
    if not isinstance(data, dict):
        return ["portfolio JSON must be an object keyed by token address"], []
    for token, row in data.items():
        if not isinstance(row, dict):
            errors.append(f"portfolio entry {token!r} must be an object")
            continue
        missing = sorted(required - row.keys())
        if missing:
            errors.append(f"portfolio entry {token!r} missing fields: {', '.join(missing)}")
        if row.get("token_address") and row.get("token_address") != token:
            warnings.append(f"portfolio key {token!r} differs from token_address field")
    return errors, warnings


def import_modules(scopes: Iterable[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    ok: list[str] = []
    for scope in scopes:
        for module in IMPORTS.get(scope, []):
            try:
                importlib.import_module(module)
                ok.append(module)
            except Exception as exc:
                errors.append(f"{module}: {type(exc).__name__}: {exc}")
    return errors, ok


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors: list[str] = []
    warnings: list[str] = []

    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()
        if not repo_root.exists():
            errors.append(f"repo root does not exist: {repo_root}")
        else:
            sys.path.insert(0, str(repo_root))
            print(f"[INFO] added repo root for import checks: {repo_root.name}")

    file_env: dict[str, str] = {}
    if args.env_file:
        try:
            file_env = read_env_file(Path(args.env_file))
            print(f"[OK] read env file keys: {len(file_env)}")
        except Exception as exc:
            errors.append(f"cannot read env file: {exc}")

    scopes = selected_scopes(args.scope)
    env_keys = sorted({key for scope in scopes for key in ENV_KEYS.get(scope, [])})
    if env_keys:
        print("[INFO] environment gate summary")
        for key in env_keys:
            status, summary = summarize_env(key, env_value(key, file_env))
            line = f"  - {key}: {status} ({summary})"
            print(line)
            if status in {"missing", "placeholder"} and key in {"BIRDEYE_API_KEY", "QUICKNODE_RPC_URL", "SOLANA_PRIVATE_KEY"}:
                warnings.append(f"{key} is {status}; live workflows needing it are not ready")

    if not args.skip_imports:
        import_errors, imported = import_modules(scopes)
        if imported:
            print(f"[OK] imported {len(imported)} modules")
        for item in import_errors:
            errors.append(f"import failed: {item}")

    if args.strategy_json:
        e, w = validate_strategy(Path(args.strategy_json))
        errors.extend(e)
        warnings.extend(w)
        if not e:
            print("[OK] strategy JSON shape is valid")

    if args.portfolio_json:
        e, w = validate_portfolio(Path(args.portfolio_json))
        errors.extend(e)
        warnings.extend(w)
        if not e:
            print("[OK] portfolio JSON shape is valid")

    for warning in warnings:
        print(f"[WARN] {warning}")
    for error in errors:
        print(f"[ERROR] {error}")

    if errors or (warnings and args.strict):
        return 1
    print("[OK] offline AlphaGPT preflight completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
