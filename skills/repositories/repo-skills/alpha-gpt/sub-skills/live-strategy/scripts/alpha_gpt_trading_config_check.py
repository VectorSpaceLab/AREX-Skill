#!/usr/bin/env python3
"""Offline AlphaGPT live-strategy preflight.

This script validates local strategy/portfolio/STOP/threshold configuration and
checks Solana env-var presence without printing secret values. It never imports
AlphaGPT, Solana, aiohttp, database clients, or transaction-capable modules and
never contacts RPC, Jupiter, Postgres, or external services.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

FEATURE_TOKENS = {
    0: "RET",
    1: "LIQ_SCORE",
    2: "PRESSURE",
    3: "FOMO",
    4: "DEV",
    5: "LOG_VOL",
}

OP_TOKENS = {
    6: ("ADD", 2),
    7: ("SUB", 2),
    8: ("MUL", 2),
    9: ("DIV", 2),
    10: ("NEG", 1),
    11: ("ABS", 1),
    12: ("SIGN", 1),
    13: ("GATE", 3),
    14: ("JUMP", 1),
    15: ("DECAY", 1),
    16: ("DELAY1", 1),
    17: ("MAX3", 1),
}

STOP_ACTIVE_VALUES = {"", "STOP", "STOPPED"}
REQUIRED_LIVE_ENV = ("QUICKNODE_RPC_URL", "SOLANA_PRIVATE_KEY")
RPC_PLACEHOLDERS = {"填入RPC地址", "", "YOUR_RPC_URL", "CHANGE_ME"}
POSITION_REQUIRED_FIELDS = {
    "token_address",
    "symbol",
    "entry_price",
    "entry_time",
    "amount_held",
    "initial_cost_sol",
    "highest_price",
}


class Result:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)
        print(f"[ERROR] {message}")

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        print(f"[WARN] {message}")

    def ok(self, message: str) -> None:
        self.notes.append(message)
        print(f"[OK] {message}")

    def info(self, message: str) -> None:
        self.notes.append(message)
        print(f"[INFO] {message}")


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse simple KEY=VALUE lines without expanding variables."""
    parsed: dict[str, str] = {}
    if not path.exists():
        return parsed
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return parsed
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        parsed[key] = value
    return parsed


def build_env(args: argparse.Namespace) -> dict[str, str]:
    env: dict[str, str] = {}
    if not args.no_env_file:
        env.update(parse_env_file(args.env_file))
    # Match python-dotenv's normal precedence: real environment wins.
    env.update(os.environ)
    return env


def present(value: str | None) -> bool:
    return value is not None and value.strip() != ""


def check_live_env(env: dict[str, str], args: argparse.Namespace, result: Result) -> None:
    for name in REQUIRED_LIVE_ENV:
        value = env.get(name)
        if present(value):
            result.ok(f"{name} is present (value suppressed).")
        else:
            message = f"{name} is missing."
            if args.live:
                result.error(message)
            else:
                result.warn(message + " Dry-run/offline checks can continue; live trading cannot.")

    rpc_value = env.get("QUICKNODE_RPC_URL")
    if present(rpc_value) and rpc_value.strip() in RPC_PLACEHOLDERS:
        message = "QUICKNODE_RPC_URL is set to a placeholder-like value (value suppressed)."
        if args.live:
            result.error(message)
        else:
            result.warn(message)


def load_strategy(path: Path, result: Result) -> list[int] | None:
    if not path.exists():
        result.error(f"Strategy JSON not found: {path}")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.error(f"Strategy JSON is not valid JSON: line {exc.lineno}, column {exc.colno}")
        return None
    except OSError as exc:
        result.error(f"Could not read strategy JSON: {exc}")
        return None

    if isinstance(data, list):
        formula = data
        shape = "top-level list"
    elif isinstance(data, dict):
        formula = data.get("formula")
        shape = "object.formula"
        if not isinstance(formula, list):
            result.error("Strategy JSON object must contain a list field named 'formula'.")
            return None
    else:
        result.error("Strategy JSON must be either a formula list or an object with a formula list.")
        return None

    tokens = normalize_formula_tokens(formula, result)
    if tokens is None:
        return None
    rpn_errors = validate_rpn(tokens)
    if rpn_errors:
        for err in rpn_errors:
            result.error(err)
        return None
    result.ok(f"Strategy JSON valid ({shape}, {len(tokens)} tokens).")
    return tokens


def normalize_formula_tokens(raw_tokens: list[Any], result: Result) -> list[int] | None:
    if not raw_tokens:
        result.error("Formula token list is empty.")
        return None
    normalized: list[int] = []
    for idx, raw in enumerate(raw_tokens):
        if isinstance(raw, bool):
            result.error(f"Formula token at index {idx} is boolean, not an integer token id.")
            return None
        if isinstance(raw, int):
            token = raw
        elif isinstance(raw, str):
            text = raw.strip()
            if not text or not text.lstrip("-").isdigit():
                result.error(f"Formula token at index {idx} is not an integer token id.")
                return None
            token = int(text)
        else:
            result.error(f"Formula token at index {idx} is not an integer token id.")
            return None
        if token not in FEATURE_TOKENS and token not in OP_TOKENS:
            result.error(f"Formula token id {token} at index {idx} is outside the known AlphaGPT token range 0..17.")
            return None
        normalized.append(token)
    return normalized


def validate_rpn(tokens: list[int]) -> list[str]:
    errors: list[str] = []
    stack_depth = 0
    for idx, token in enumerate(tokens):
        if token in FEATURE_TOKENS:
            stack_depth += 1
            continue
        name, arity = OP_TOKENS[token]
        if stack_depth < arity:
            errors.append(
                f"Formula RPN underflow at index {idx}: operator {name} needs {arity} inputs, stack has {stack_depth}."
            )
            return errors
        stack_depth = stack_depth - arity + 1
    if stack_depth != 1:
        errors.append(f"Formula RPN must leave exactly one stack item; final depth is {stack_depth}.")
    return errors


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_portfolio(path: Path | None, explicit: bool, result: Result) -> None:
    if path is None:
        default = Path("portfolio_state.json")
        if not default.exists():
            result.info("No portfolio JSON supplied and default portfolio_state.json is absent; fresh local state is acceptable.")
            return
        path = default
        explicit = False

    if not path.exists():
        if explicit:
            result.error(f"Portfolio JSON not found: {path}")
        else:
            result.info("Default portfolio_state.json is absent; fresh local state is acceptable.")
        return

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.error(f"Portfolio JSON is not valid JSON: line {exc.lineno}, column {exc.colno}")
        return
    except OSError as exc:
        result.error(f"Could not read portfolio JSON: {exc}")
        return

    if not isinstance(data, dict):
        result.error("Portfolio JSON must be an object keyed by token address.")
        return

    errors_before = len(result.errors)
    for idx, (token_key, position) in enumerate(data.items()):
        if not isinstance(token_key, str) or not token_key:
            result.error(f"Portfolio entry {idx} has a non-string or empty token key.")
            continue
        if not isinstance(position, dict):
            result.error(f"Portfolio entry {idx} must be an object.")
            continue
        missing = sorted(POSITION_REQUIRED_FIELDS - set(position))
        if missing:
            result.error(f"Portfolio entry {idx} is missing fields: {', '.join(missing)}")
            continue
        if not isinstance(position.get("token_address"), str) or not position.get("token_address"):
            result.error(f"Portfolio entry {idx} has invalid token_address.")
        if position.get("token_address") != token_key:
            result.warn(f"Portfolio entry {idx} token key and token_address differ; reconcile before live use.")
        if not isinstance(position.get("symbol"), str):
            result.error(f"Portfolio entry {idx} has invalid symbol.")
        for field in ("entry_price", "entry_time", "amount_held", "initial_cost_sol", "highest_price"):
            if not is_number(position.get(field)):
                result.error(f"Portfolio entry {idx} field {field} must be numeric.")
        for field in ("entry_price", "amount_held", "initial_cost_sol", "highest_price"):
            value = position.get(field)
            if is_number(value) and value < 0:
                result.error(f"Portfolio entry {idx} field {field} must not be negative.")
        if "is_moonbag" in position and not isinstance(position.get("is_moonbag"), bool):
            result.error(f"Portfolio entry {idx} field is_moonbag must be boolean when present.")
    if len(result.errors) == errors_before:
        result.ok(f"Portfolio JSON valid ({len(data)} open positions recorded).")


def check_stop_signal(path: Path, args: argparse.Namespace, result: Result) -> None:
    if not path.exists():
        result.ok("STOP signal file is absent; the runner will not stop immediately from this file.")
        return
    if not path.is_file():
        result.warn("STOP signal path exists but is not a regular file; the runner may treat read errors as a stop request.")
        return
    try:
        signal = path.read_text(encoding="utf-8").strip().upper()
    except OSError:
        result.warn("STOP signal file cannot be read; the runner treats read errors as a stop request.")
        return
    if signal in STOP_ACTIVE_VALUES:
        message = "STOP signal is active; delete or rename the file before starting a live loop."
        if args.fail_on_active_stop:
            result.error(message)
        else:
            result.warn(message)
    else:
        result.ok("STOP signal file exists but its content is not one of the runner's active stop values.")


def validate_thresholds(args: argparse.Namespace, result: Result) -> None:
    errors_before = len(result.errors)
    if args.max_open_positions < 1:
        result.error("max-open-positions must be at least 1.")
    if args.entry_amount_sol <= 0:
        result.error("entry-amount-sol must be positive.")
    if not -1.0 < args.stop_loss_pct < 0.0:
        result.error("stop-loss-pct should be negative and greater than -1.0.")
    if args.take_profit_target1 <= 0:
        result.error("take-profit-target1 must be positive.")
    if not 0.0 < args.tp_target1_ratio <= 1.0:
        result.error("tp-target1-ratio must be in (0, 1].")
    if args.trailing_activation <= 0:
        result.error("trailing-activation must be positive.")
    if args.trailing_drop <= 0:
        result.error("trailing-drop must be positive.")
    if not 0.0 <= args.sell_threshold <= 1.0:
        result.error("sell-threshold must be between 0 and 1.")
    if not 0.0 <= args.buy_threshold <= 1.0:
        result.error("buy-threshold must be between 0 and 1.")
    if args.buy_threshold <= args.sell_threshold:
        result.warn("buy-threshold is not greater than sell-threshold; entries/exits may conflict.")
    if args.min_liquidity_usd < 0:
        result.error("min-liquidity-usd must not be negative.")
    if len(result.errors) == errors_before:
        result.ok("Threshold values are internally consistent for offline preflight.")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Offline AlphaGPT live-strategy config checker. No network, RPC, Jupiter, DB, or private-key printing.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--strategy-json", type=Path, default=Path("best_meme_strategy.json"), help="Strategy JSON path to validate.")
    parser.add_argument("--portfolio-json", type=Path, default=None, help="Optional portfolio_state.json path to validate. If omitted, validate default only when it exists.")
    parser.add_argument("--stop-signal-path", type=Path, default=None, help="STOP signal path. Defaults to STOP_SIGNAL_PATH env or STOP_SIGNAL after parsing.")
    parser.add_argument("--env-file", type=Path, default=Path(".env"), help="Optional .env file to read for env presence checks.")
    parser.add_argument("--no-env-file", action="store_true", help="Ignore .env and check process environment only.")
    parser.add_argument("--live", action="store_true", help="Require QUICKNODE_RPC_URL and SOLANA_PRIVATE_KEY presence for authorized live readiness.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument("--fail-on-active-stop", action="store_true", help="Fail if the STOP signal is currently active.")

    parser.add_argument("--max-open-positions", type=int, default=3, help="StrategyConfig.MAX_OPEN_POSITIONS.")
    parser.add_argument("--entry-amount-sol", type=float, default=2.0, help="StrategyConfig.ENTRY_AMOUNT_SOL.")
    parser.add_argument("--stop-loss-pct", type=float, default=-0.05, help="StrategyConfig.STOP_LOSS_PCT.")
    parser.add_argument("--take-profit-target1", type=float, default=0.10, help="StrategyConfig.TAKE_PROFIT_Target1.")
    parser.add_argument("--tp-target1-ratio", type=float, default=0.5, help="StrategyConfig.TP_Target1_Ratio.")
    parser.add_argument("--trailing-activation", type=float, default=0.05, help="StrategyConfig.TRAILING_ACTIVATION.")
    parser.add_argument("--trailing-drop", type=float, default=0.03, help="StrategyConfig.TRAILING_DROP.")
    parser.add_argument("--buy-threshold", type=float, default=0.85, help="StrategyConfig.BUY_THRESHOLD.")
    parser.add_argument("--sell-threshold", type=float, default=0.45, help="StrategyConfig.SELL_THRESHOLD.")
    parser.add_argument("--min-liquidity-usd", type=float, default=5000.0, help="RiskEngine liquidity floor used by check_safety.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    if args.stop_signal_path is None:
        args.stop_signal_path = Path(os.environ.get("STOP_SIGNAL_PATH", "STOP_SIGNAL"))

    result = Result()
    print("AlphaGPT live-strategy offline preflight")
    print("Network/RPC/Jupiter/DB calls: disabled")
    print("Secret values: suppressed")

    env = build_env(args)
    check_live_env(env, args, result)
    load_strategy(args.strategy_json, result)
    validate_portfolio(args.portfolio_json, explicit=args.portfolio_json is not None, result=result)
    check_stop_signal(args.stop_signal_path, args, result)
    validate_thresholds(args, result)

    print(f"Summary: {len(result.errors)} error(s), {len(result.warnings)} warning(s).")
    if result.errors or (args.strict and result.warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
