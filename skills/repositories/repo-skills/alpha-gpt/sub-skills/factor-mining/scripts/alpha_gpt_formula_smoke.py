#!/usr/bin/env python3
"""Deterministic AlphaGPT formula smoke helper.

This script validates a reverse-Polish AlphaGPT formula, builds synthetic raw
OHLCV/liquidity/FDV tensors, computes feature tensors, executes the formula,
and prints a finite-output summary. It never reads databases, calls networks,
loads credentials, touches wallets, or writes trading outputs.

Pass --repo-root to compare against a source tree that contains model_core/.
When that import is unavailable, the script uses the bundled standard-library
vocabulary, feature, and operator fallback.
"""

from __future__ import annotations

import argparse
import importlib
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Sequence, Tuple

FEATURE_NAMES: Tuple[str, ...] = (
    "RET",
    "LIQ_SCORE",
    "PRESSURE",
    "FOMO",
    "DEV",
    "LOG_VOL",
)

OPERATOR_NAMES: Tuple[str, ...] = (
    "ADD",
    "SUB",
    "MUL",
    "DIV",
    "NEG",
    "ABS",
    "SIGN",
    "GATE",
    "JUMP",
    "DECAY",
    "DELAY1",
    "MAX3",
)

OPERATOR_ARITIES: Tuple[int, ...] = (2, 2, 2, 2, 1, 1, 1, 3, 1, 1, 1, 1)
OPERATOR_OFFSET = len(FEATURE_NAMES)
TOKEN_NAMES: Tuple[str, ...] = FEATURE_NAMES + OPERATOR_NAMES
ARITY_MAP: Dict[int, int] = {
    OPERATOR_OFFSET + idx: arity for idx, arity in enumerate(OPERATOR_ARITIES)
}

Matrix = List[List[float]]
Tensor3 = List[List[List[float]]]
RawData = Dict[str, Matrix]


@dataclass(frozen=True)
class Backend:
    name: str
    note: str
    token_names: Tuple[str, ...]
    operator_offset: int
    arity_map: Mapping[int, int]
    compute_features: Callable[[RawData, bool], Any]
    execute_formula: Callable[[Sequence[int], Any], Any]

    @property
    def vocab_size(self) -> int:
        return len(self.token_names)


def positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate an AlphaGPT RPN formula against deterministic synthetic "
            "feature tensors."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="optional source root containing model_core/ for actual-code checks",
    )
    parser.add_argument(
        "--formula",
        default="0,5,6",
        help=(
            "comma- or space-separated formula token IDs or names in RPN; "
            "default: 0,5,6"
        ),
    )
    parser.add_argument(
        "--list-vocab",
        action="store_true",
        help="print the formula vocabulary and exit successfully",
    )
    parser.add_argument(
        "--advanced",
        action="store_true",
        help="compute the advanced feature tensor when the selected backend supports it",
    )
    parser.add_argument(
        "--time-steps",
        type=positive_int,
        default=8,
        help="synthetic time steps per token row; default: 8",
    )
    parser.add_argument(
        "--tokens",
        type=positive_int,
        default=3,
        help="synthetic token rows to generate; default: 3",
    )
    return parser


def fallback_backend(note: str) -> Backend:
    vm = BundledStackVM(operator_offset=OPERATOR_OFFSET, arity_map=ARITY_MAP)
    return Backend(
        name="bundled-fallback",
        note=note,
        token_names=TOKEN_NAMES,
        operator_offset=OPERATOR_OFFSET,
        arity_map=ARITY_MAP,
        compute_features=fallback_compute_features,
        execute_formula=vm.execute,
    )


def load_backend(repo_root: str | None) -> Backend:
    if not repo_root:
        return fallback_backend(
            "repo import failed/skipped: no --repo-root supplied; "
            "using bundled fallback implementation"
        )

    root = Path(repo_root).expanduser().resolve()
    if not (root / "model_core").is_dir():
        return fallback_backend(
            "repo import failed: model_core/ not found; "
            "using bundled fallback implementation"
        )

    sys.path.insert(0, str(root))
    try:
        vocab_mod = importlib.import_module("model_core.vocab")
        factors_mod = importlib.import_module("model_core.factors")
        ops_mod = importlib.import_module("model_core.ops")
        vm_mod = importlib.import_module("model_core.vm")

        vocab = getattr(vocab_mod, "FORMULA_VOCAB")
        token_names = tuple(getattr(vocab, "token_names"))
        operator_offset = int(getattr(vocab, "operator_offset"))
        ops_config = tuple(getattr(ops_mod, "OPS_CONFIG"))
        arity_map = {
            operator_offset + idx: int(cfg[2]) for idx, cfg in enumerate(ops_config)
        }
        feature_engineer = getattr(factors_mod, "FeatureEngineer")
        advanced_engineer = getattr(factors_mod, "AdvancedFactorEngineer", None)
        stack_vm_cls = getattr(vm_mod, "StackVM")
    except Exception as exc:  # pragma: no cover - depends on optional repo deps
        return fallback_backend(
            f"repo import failed ({exc.__class__.__name__}); "
            "using bundled fallback implementation"
        )

    stack_vm = stack_vm_cls()

    def repo_compute_features(raw: RawData, advanced: bool) -> Any:
        torch = importlib.import_module("torch")
        raw_tensors = {
            key: torch.tensor(value, dtype=torch.float32) for key, value in raw.items()
        }
        if advanced:
            if advanced_engineer is None:
                raise RuntimeError("advanced feature engineer unavailable")
            return advanced_engineer().compute_advanced_features(raw_tensors)
        return feature_engineer.compute_features(raw_tensors)

    return Backend(
        name="repo-model-core",
        note="repo import succeeded: using model_core feature and VM modules",
        token_names=token_names,
        operator_offset=operator_offset,
        arity_map=arity_map,
        compute_features=repo_compute_features,
        execute_formula=stack_vm.execute,
    )


def build_synthetic_raw(token_count: int, time_steps: int) -> RawData:
    raw: RawData = {
        "open": [],
        "high": [],
        "low": [],
        "close": [],
        "volume": [],
        "liquidity": [],
        "fdv": [],
    }
    for token_idx in range(token_count):
        open_row: List[float] = []
        high_row: List[float] = []
        low_row: List[float] = []
        close_row: List[float] = []
        volume_row: List[float] = []
        liquidity_row: List[float] = []
        fdv_row: List[float] = []
        base = 10.0 + token_idx * 2.25
        for step in range(time_steps):
            wave = ((step + token_idx) % 5 - 2) * 0.11
            drift = 0.34 * step
            open_value = base + drift + wave
            close_value = open_value + ((step * 2 + token_idx) % 7 - 3) * 0.07
            spread = 0.55 + 0.03 * ((step + 2 * token_idx) % 4)
            high_value = max(open_value, close_value) + spread
            low_value = max(0.01, min(open_value, close_value) - spread * 0.82)
            volume_value = (
                1000.0
                + 135.0 * token_idx
                + 29.0 * step
                + 17.0 * ((step + token_idx) % 4)
            )
            liquidity_value = 510_000.0 + 9_000.0 * token_idx + 1_450.0 * step
            fdv_value = 1_020_000.0 + 15_000.0 * token_idx + 1_750.0 * step

            open_row.append(open_value)
            high_row.append(high_value)
            low_row.append(low_value)
            close_row.append(close_value)
            volume_row.append(volume_value)
            liquidity_row.append(liquidity_value)
            fdv_row.append(fdv_value)

        raw["open"].append(open_row)
        raw["high"].append(high_row)
        raw["low"].append(low_row)
        raw["close"].append(close_row)
        raw["volume"].append(volume_row)
        raw["liquidity"].append(liquidity_row)
        raw["fdv"].append(fdv_row)
    return raw


def clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def median(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def robust_norm(matrix: Matrix) -> Matrix:
    normalized: Matrix = []
    for row in matrix:
        row_median = median(row)
        mad = median([abs(value - row_median) for value in row]) + 1e-6
        normalized.append([clamp((value - row_median) / mad, -5.0, 5.0) for value in row])
    return normalized


def fallback_base_channels(raw: RawData) -> List[Matrix]:
    ret: Matrix = []
    liq_score: Matrix = []
    pressure: Matrix = []
    fomo: Matrix = []
    dev: Matrix = []
    log_vol: Matrix = []

    for row_idx, close_row in enumerate(raw["close"]):
        open_row = raw["open"][row_idx]
        high_row = raw["high"][row_idx]
        low_row = raw["low"][row_idx]
        volume_row = raw["volume"][row_idx]
        liquidity_row = raw["liquidity"][row_idx]
        fdv_row = raw["fdv"][row_idx]

        ret_row: List[float] = []
        liq_row: List[float] = []
        pressure_row: List[float] = []
        fomo_row: List[float] = []
        dev_row: List[float] = []
        log_vol_row: List[float] = []
        previous_volume_change = 0.0
        window = 20

        for step, close_value in enumerate(close_row):
            previous_close = close_row[step - 1] if step > 0 else close_value
            if close_value > 0 and previous_close > 0:
                ret_row.append(math.log(close_value / (previous_close + 1e-9)))
            else:
                ret_row.append(0.0)

            fdv_value = fdv_row[step]
            liq_row.append(clamp((liquidity_row[step] / (fdv_value + 1e-6)) * 4.0, 0.0, 1.0))

            range_hl = high_row[step] - low_row[step] + 1e-9
            body = close_value - open_row[step]
            pressure_row.append(math.tanh((body / range_hl) * 3.0))

            previous_volume = volume_row[step - 1] if step > 0 else volume_row[step]
            volume_change = (volume_row[step] - previous_volume) / (previous_volume + 1.0)
            fomo_row.append(clamp(volume_change - previous_volume_change, -5.0, 5.0))
            previous_volume_change = volume_change

            start = step - window + 1
            zero_pad = max(0, -start)
            close_window = [0.0] * zero_pad + close_row[max(0, start) : step + 1]
            moving_average = sum(close_window) / float(window)
            dev_row.append((close_value - moving_average) / (moving_average + 1e-9))

            log_vol_row.append(math.log1p(max(0.0, volume_row[step])))

        ret.append(ret_row)
        liq_score.append(liq_row)
        pressure.append(pressure_row)
        fomo.append(fomo_row)
        dev.append(dev_row)
        log_vol.append(log_vol_row)

    return [
        robust_norm(ret),
        liq_score,
        pressure,
        robust_norm(fomo),
        robust_norm(dev),
        robust_norm(log_vol),
    ]


def fallback_advanced_channels(raw: RawData, ret_channel: Matrix) -> List[Matrix]:
    vol_cluster: Matrix = []
    momentum_reversal: Matrix = []
    relative_strength: Matrix = []
    high_low_range: Matrix = []
    close_position: Matrix = []
    volume_trend: Matrix = []

    for row_idx, close_row in enumerate(raw["close"]):
        high_row = raw["high"][row_idx]
        low_row = raw["low"][row_idx]
        volume_row = raw["volume"][row_idx]
        ret_row = ret_channel[row_idx]

        vol_cluster_row: List[float] = []
        reversal_row: List[float] = []
        strength_row: List[float] = []
        range_row: List[float] = []
        close_pos_row: List[float] = []
        vol_trend_row: List[float] = []
        window = 5

        for step, close_value in enumerate(close_row):
            start = max(0, step - window + 1)
            returns_window = ret_row[start : step + 1]
            vol_cluster_row.append(
                math.sqrt(sum(value * value for value in returns_window) / len(returns_window) + 1e-9)
            )

            prev_start = max(0, step - window)
            current_momentum = sum(ret_row[start : step + 1])
            previous_momentum = sum(ret_row[prev_start:step]) if step > 0 else 0.0
            reversal_row.append(1.0 if current_momentum * previous_momentum < 0.0 else 0.0)

            gains = []
            losses = []
            for idx in range(start, step + 1):
                previous_close = close_row[idx - 1] if idx > 0 else close_row[idx]
                delta = close_row[idx] - previous_close
                gains.append(max(delta, 0.0))
                losses.append(max(-delta, 0.0))
            avg_gain = sum(gains) / len(gains)
            avg_loss = sum(losses) / len(losses)
            rs = (avg_gain + 1e-9) / (avg_loss + 1e-9)
            rsi = 100.0 - (100.0 / (1.0 + rs))
            strength_row.append((rsi - 50.0) / 50.0)

            range_hl = high_row[step] - low_row[step]
            range_row.append(range_hl / (close_value + 1e-9))
            close_pos_row.append((close_value - low_row[step]) / (range_hl + 1e-9))

            previous_volume = volume_row[step - 1] if step > 0 else volume_row[step]
            vol_trend_row.append((volume_row[step] - previous_volume) / (previous_volume + 1.0))

        vol_cluster.append(vol_cluster_row)
        momentum_reversal.append(reversal_row)
        relative_strength.append(strength_row)
        high_low_range.append(range_row)
        close_position.append(close_pos_row)
        volume_trend.append(vol_trend_row)

    return [
        robust_norm(vol_cluster),
        momentum_reversal,
        robust_norm(relative_strength),
        robust_norm(high_low_range),
        close_position,
        robust_norm(volume_trend),
    ]


def stack_channels(channels: Sequence[Matrix]) -> Tensor3:
    if not channels:
        return []
    token_count = len(channels[0])
    feature_count = len(channels)
    stacked: Tensor3 = []
    for token_idx in range(token_count):
        feature_rows: List[List[float]] = []
        for feature_idx in range(feature_count):
            feature_rows.append(list(channels[feature_idx][token_idx]))
        stacked.append(feature_rows)
    return stacked


def fallback_compute_features(raw: RawData, advanced: bool) -> Tensor3:
    channels = fallback_base_channels(raw)
    if advanced:
        channels.extend(fallback_advanced_channels(raw, channels[0]))
    return stack_channels(channels)


def feature_slice(feat_tensor: Tensor3, feature_idx: int) -> Matrix:
    return [list(token_features[feature_idx]) for token_features in feat_tensor]


def matrix_unary(matrix: Matrix, func: Callable[[float], float]) -> Matrix:
    return [[func(value) for value in row] for row in matrix]


def matrix_binary(left: Matrix, right: Matrix, func: Callable[[float, float], float]) -> Matrix:
    return [
        [func(left_value, right_value) for left_value, right_value in zip(left_row, right_row)]
        for left_row, right_row in zip(left, right)
    ]


def matrix_ternary(
    first: Matrix,
    second: Matrix,
    third: Matrix,
    func: Callable[[float, float, float], float],
) -> Matrix:
    return [
        [
            func(first_value, second_value, third_value)
            for first_value, second_value, third_value in zip(first_row, second_row, third_row)
        ]
        for first_row, second_row, third_row in zip(first, second, third)
    ]


def delay(matrix: Matrix, steps: int) -> Matrix:
    if steps <= 0:
        return [list(row) for row in matrix]
    delayed: Matrix = []
    for row in matrix:
        if not row:
            delayed.append([])
        elif steps >= len(row):
            delayed.append([0.0] * len(row))
        else:
            delayed.append([0.0] * steps + row[:-steps])
    return delayed


def matrix_jump(matrix: Matrix) -> Matrix:
    jumped: Matrix = []
    for row in matrix:
        if not row:
            jumped.append([])
            continue
        mean_value = sum(row) / len(row)
        variance = sum((value - mean_value) ** 2 for value in row) / len(row)
        std_value = math.sqrt(variance) + 1e-6
        jumped.append([max(((value - mean_value) / std_value) - 3.0, 0.0) for value in row])
    return jumped


def sanitize_value(value: float) -> float:
    if math.isnan(value):
        return 0.0
    if math.isinf(value):
        return 1.0 if value > 0.0 else -1.0
    return value


def sanitize_matrix(matrix: Matrix) -> Matrix:
    return [[sanitize_value(float(value)) for value in row] for row in matrix]


class BundledStackVM:
    def __init__(self, operator_offset: int, arity_map: Mapping[int, int]):
        self.operator_offset = operator_offset
        self.arity_map = dict(arity_map)

    def execute(self, formula_tokens: Sequence[int], feat_tensor: Tensor3) -> Matrix | None:
        stack: List[Matrix] = []
        try:
            feature_count = len(feat_tensor[0]) if feat_tensor else 0
            for token in formula_tokens:
                token = int(token)
                if token < self.operator_offset:
                    if token < 0 or token >= feature_count:
                        return None
                    stack.append(feature_slice(feat_tensor, token))
                    continue

                arity = self.arity_map.get(token)
                if arity is None or len(stack) < arity:
                    return None
                args = stack[-arity:]
                del stack[-arity:]
                stack.append(sanitize_matrix(self.apply_operator(token, args)))
            return stack[0] if len(stack) == 1 else None
        except Exception:
            return None

    def apply_operator(self, token: int, args: Sequence[Matrix]) -> Matrix:
        name = OPERATOR_NAMES[token - self.operator_offset]
        if name == "ADD":
            return matrix_binary(args[0], args[1], lambda x, y: x + y)
        if name == "SUB":
            return matrix_binary(args[0], args[1], lambda x, y: x - y)
        if name == "MUL":
            return matrix_binary(args[0], args[1], lambda x, y: x * y)
        if name == "DIV":
            return matrix_binary(args[0], args[1], lambda x, y: x / (y + 1e-6))
        if name == "NEG":
            return matrix_unary(args[0], lambda x: -x)
        if name == "ABS":
            return matrix_unary(args[0], abs)
        if name == "SIGN":
            return matrix_unary(args[0], lambda x: 1.0 if x > 0.0 else (-1.0 if x < 0.0 else 0.0))
        if name == "GATE":
            return matrix_ternary(args[0], args[1], args[2], lambda c, x, y: x if c > 0.0 else y)
        if name == "JUMP":
            return matrix_jump(args[0])
        if name == "DECAY":
            d1 = delay(args[0], 1)
            d2 = delay(args[0], 2)
            return matrix_ternary(args[0], d1, d2, lambda x, y, z: x + 0.8 * y + 0.6 * z)
        if name == "DELAY1":
            return delay(args[0], 1)
        if name == "MAX3":
            d1 = delay(args[0], 1)
            d2 = delay(args[0], 2)
            return matrix_ternary(args[0], d1, d2, max)
        raise ValueError(f"unsupported operator token {token}")


def parse_formula(spec: str, token_names: Sequence[str]) -> List[int]:
    name_to_id = {name.upper(): idx for idx, name in enumerate(token_names)}
    parts = [part for part in spec.replace(",", " ").split() if part]
    if not parts:
        raise ValueError("formula is empty")

    parsed: List[int] = []
    for part in parts:
        if part.lstrip("+-").isdigit():
            parsed.append(int(part, 10))
            continue
        token_id = name_to_id.get(part.upper())
        if token_id is None:
            raise ValueError(f"unknown token name {part!r}")
        parsed.append(token_id)
    return parsed


def validate_formula(
    formula: Sequence[int],
    vocab_size: int,
    operator_offset: int,
    arity_map: Mapping[int, int],
    feature_shape: Sequence[int],
) -> str | None:
    if not formula:
        return "formula is empty"
    feature_count = int(feature_shape[1]) if len(feature_shape) >= 2 else 0
    stack_depth = 0
    for position, token in enumerate(formula):
        if token < 0 or token >= vocab_size:
            return f"token {token} at position {position} is outside valid IDs 0..{vocab_size - 1}"
        if token < operator_offset:
            if token >= feature_count:
                return (
                    f"feature token {token} at position {position} is outside "
                    f"the feature tensor width {feature_count}"
                )
            stack_depth += 1
            continue
        arity = arity_map.get(token)
        if arity is None:
            return f"token {token} at position {position} has no registered operator"
        if stack_depth < arity:
            return (
                f"stack underflow at position {position}: token {token} needs "
                f"{arity} operands, stack has {stack_depth}"
            )
        stack_depth = stack_depth - arity + 1
    if stack_depth != 1:
        return f"formula leaves {stack_depth} stack values; expected exactly 1"
    return None


def shape_of(value: Any) -> Tuple[int, ...]:
    shape = getattr(value, "shape", None)
    if shape is not None:
        return tuple(int(dim) for dim in shape)
    dims: List[int] = []
    current = value
    while isinstance(current, list):
        dims.append(len(current))
        current = current[0] if current else []
        if not current:
            break
    return tuple(dims)


def flatten_numeric(value: Any) -> List[float]:
    if hasattr(value, "detach") and hasattr(value, "reshape"):
        return [float(item) for item in value.detach().cpu().reshape(-1).tolist()]
    flattened: List[float] = []

    def walk(item: Any) -> None:
        if isinstance(item, list):
            for child in item:
                walk(child)
        else:
            flattened.append(float(item))

    walk(value)
    return flattened


def finite_summary(value: Any) -> str:
    values = flatten_numeric(value)
    total = len(values)
    finite_values = [item for item in values if math.isfinite(item)]
    finite_count = len(finite_values)
    if not finite_values:
        return f"finite={finite_count}/{total}; min=n/a; max=n/a; mean=n/a"
    mean_value = sum(finite_values) / finite_count
    return (
        f"finite={finite_count}/{total}; "
        f"min={min(finite_values):.6g}; "
        f"max={max(finite_values):.6g}; "
        f"mean={mean_value:.6g}"
    )


def format_vocab(backend: Backend) -> str:
    lines = ["vocab:"]
    for token_id, token_name in enumerate(backend.token_names):
        if token_id < backend.operator_offset:
            lines.append(f"  {token_id:2d}  {token_name:<10} feature")
        else:
            arity = backend.arity_map.get(token_id, "?")
            lines.append(f"  {token_id:2d}  {token_name:<10} op arity={arity}")
    return "\n".join(lines)


def format_formula(formula: Sequence[int], token_names: Sequence[str]) -> str:
    names = [token_names[token] if 0 <= token < len(token_names) else f"?{token}" for token in formula]
    return f"{list(formula)} -> {' '.join(names)}"


def run(args: argparse.Namespace) -> int:
    backend = load_backend(args.repo_root)
    print(f"mode: {backend.name}")
    print(f"note: {backend.note}")
    print(format_vocab(backend))

    if args.list_vocab:
        return 0

    raw = build_synthetic_raw(token_count=args.tokens, time_steps=args.time_steps)
    try:
        features = backend.compute_features(raw, args.advanced)
    except Exception as exc:  # pragma: no cover - depends on optional repo deps
        print(
            f"feature computation failed in {backend.name} mode ({exc.__class__.__name__})",
            file=sys.stderr,
        )
        return 1

    feature_shape = shape_of(features)
    try:
        formula = parse_formula(args.formula, backend.token_names)
    except ValueError as exc:
        print(f"invalid formula: {exc}", file=sys.stderr)
        return 1

    validation_error = validate_formula(
        formula,
        vocab_size=backend.vocab_size,
        operator_offset=backend.operator_offset,
        arity_map=backend.arity_map,
        feature_shape=feature_shape,
    )
    print(f"feature_shape: {feature_shape}")
    if args.advanced:
        print("advanced_features: enabled")
    print(f"formula: {format_formula(formula, backend.token_names)}")

    if validation_error:
        print(f"invalid formula: {validation_error}", file=sys.stderr)
        return 1

    try:
        output = backend.execute_formula(formula, features)
    except Exception as exc:  # pragma: no cover - defensive around repo VM
        print(
            f"formula execution failed in {backend.name} mode ({exc.__class__.__name__})",
            file=sys.stderr,
        )
        return 1

    if output is None:
        print("invalid formula: StackVM returned no output", file=sys.stderr)
        return 1

    print(f"output_shape: {shape_of(output)}")
    print(f"finite_output: {finite_summary(output)}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
