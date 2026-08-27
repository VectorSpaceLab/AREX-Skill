#!/usr/bin/env python3
"""Bundle the Pyraformer preprocessing entry points into one helper.

This script adapts the source preprocessing logic for:
- electricity long-range / single-step preparation
- app-flow long-range preparation
- wind long-range preparation
- synthetic sinusoid generation

Relative paths are resolved against the nearest LTSF-Linear checkout root when
possible, so the helper can be launched from the repo root or this skill tree.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import zipfile

import numpy as np
import pandas as pd
from scipy import stats


REPO_MARKER = Path("Pyraformer") / "long_range_main.py"


@dataclass
class Plan:
    kind: str
    inputs: list[Path]
    outputs: list[Path]


def discover_repo_root(explicit: str | None = None) -> Path:
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not root.is_dir():
            raise SystemExit(f"Repo root does not exist: {root}")
        return root

    candidates: list[Path] = []
    cwd = Path.cwd().resolve()
    candidates.append(cwd)
    candidates.extend(cwd.parents)
    script_dir = Path(__file__).resolve().parent
    candidates.append(script_dir)
    candidates.extend(script_dir.parents)

    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / REPO_MARKER).is_file():
            return candidate

    raise SystemExit(
        "Could not find the LTSF-Linear checkout root. Pass --repo-root to "
        "point at the repository."
    )


def resolve_path(root: Path, raw: str | Path) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_array(path: Path, array: np.ndarray) -> None:
    ensure_parent(path)
    np.save(path, array)


def print_plan(plan: Plan) -> None:
    print(f"[pyraformer-data] {plan.kind}")
    for source in plan.inputs:
        print(f"  input:  {source}")
    for target in plan.outputs:
        print(f"  output: {target}")


def gen_elect_covariates(times: Iterable[pd.Timestamp], num_covariates: int = 4) -> np.ndarray:
    covariates = np.zeros((len(times), num_covariates), dtype=np.float32)
    for i, input_time in enumerate(times):
        covariates[i, 0] = input_time.weekday() / 7
        covariates[i, 1] = input_time.hour / 24
        covariates[i, 2] = input_time.month / 12
    return covariates


def prep_elect_windows(
    data: np.ndarray,
    covariates: np.ndarray,
    data_start: np.ndarray,
    *,
    train: bool,
    window_size: int,
    stride_size: int,
    total_time: int,
    num_series: int,
    output_dir: Path,
    save_name: str,
) -> Plan:
    num_covariates = covariates.shape[1]
    time_len = data.shape[0]
    input_size = window_size - stride_size
    windows_per_series = np.full((num_series,), (time_len - input_size) // stride_size)
    if train:
        windows_per_series -= (data_start + stride_size - 1) // stride_size

    total_windows = int(np.sum(windows_per_series))
    x_input = np.zeros((total_windows, window_size, 1 + num_covariates + 1), dtype=np.float32)
    label = np.zeros((total_windows, window_size), dtype=np.float32)
    v_input = np.zeros((total_windows, 2), dtype=np.float32)

    count = 0
    covariates_view = covariates.copy()
    if not train:
        covariates_view = covariates_view[-time_len:]

    for series in range(num_series):
        cov_age = stats.zscore(np.arange(total_time - data_start[series]))
        if train:
            covariates_view[data_start[series] : time_len, 0] = cov_age[: time_len - data_start[series]]
        else:
            covariates_view[:, 0] = cov_age[-time_len:]

        for i in range(int(windows_per_series[series])):
            if train:
                window_start = stride_size * i + data_start[series]
            else:
                window_start = stride_size * i
            window_end = window_start + window_size

            x_input[count, 1:, 0] = data[window_start : window_end - 1, series]
            x_input[count, :, 1 : 1 + num_covariates] = covariates_view[window_start:window_end, :]
            x_input[count, :, -1] = series
            label[count, :] = data[window_start:window_end, series]

            nonzero_sum = (x_input[count, 1:input_size, 0] != 0).sum()
            if nonzero_sum == 0:
                v_input[count, 0] = 0
            else:
                v_input[count, 0] = np.true_divide(
                    x_input[count, 1:input_size, 0].sum(), nonzero_sum
                ) + 1
                x_input[count, :, 0] = x_input[count, :, 0] / v_input[count, 0]
                if train:
                    label[count, :] = label[count, :] / v_input[count, 0]
            count += 1

    prefix = output_dir / ("train_" if train else "test_")
    data_out = prefix.with_name(prefix.name + f"data_{save_name}.npy")
    v_out = prefix.with_name(prefix.name + f"v_{save_name}.npy")
    label_out = prefix.with_name(prefix.name + f"label_{save_name}.npy")
    save_array(data_out, x_input)
    save_array(v_out, v_input)
    save_array(label_out, label)
    return Plan(
        kind=f"elect {'train' if train else 'test'} preprocessing",
        inputs=[],
        outputs=[data_out, v_out, label_out],
    )


def preprocess_elect(
    csv_path: Path,
    output_dir: Path,
    *,
    window_size: int = 192,
    stride_size: int = 24,
    train_start: str = "2011-01-01 00:00:00",
    train_end: str = "2014-08-31 23:00:00",
    test_start: str = "2014-08-25 00:00:00",
    test_end: str = "2014-09-07 23:00:00",
) -> list[Plan]:
    data_frame = pd.read_csv(csv_path, sep=";", index_col=0, parse_dates=True, decimal=",")
    data_frame = data_frame.resample("1H", label="left", closed="right").sum()[train_start:test_end]
    data_frame.fillna(0, inplace=True)

    covariates = gen_elect_covariates(data_frame[train_start:test_end].index, 4)
    train_data = data_frame[train_start:train_end].values
    test_data = data_frame[test_start:test_end].values
    data_start = (train_data != 0).argmax(axis=0)
    keep_mask = data_start < 10000
    train_data = train_data[:, keep_mask]
    test_data = test_data[:, keep_mask]
    data_start = data_start[keep_mask]
    total_time = data_frame.shape[0]
    num_series = train_data.shape[1]

    train_plan = prep_elect_windows(
        train_data,
        covariates,
        data_start,
        train=True,
        window_size=window_size,
        stride_size=stride_size,
        total_time=total_time,
        num_series=num_series,
        output_dir=output_dir,
        save_name="elect",
    )
    test_plan = prep_elect_windows(
        test_data,
        covariates,
        data_start,
        train=False,
        window_size=window_size,
        stride_size=stride_size,
        total_time=total_time,
        num_series=num_series,
        output_dir=output_dir,
        save_name="elect",
    )
    return [
        Plan("electricity source", [csv_path], train_plan.outputs + test_plan.outputs),
        train_plan,
        test_plan,
    ]


def load_flow_dataframe(csv_path: Path) -> pd.DataFrame:
    if csv_path.suffix.lower() != ".zip":
        data_frame = pd.read_csv(csv_path, header=0)
        if len(data_frame.columns) > 0 and data_frame.columns[0].startswith("Unnamed"):
            data_frame = data_frame.drop(data_frame.columns[0], axis=1)
        return data_frame

    with zipfile.ZipFile(csv_path) as zf:
        members = [name for name in zf.namelist() if name.lower().endswith(".csv")]
        if not members:
            raise SystemExit(f"No CSV file found inside archive: {csv_path}")
        with zf.open(members[0]) as handle:
            data_frame = pd.read_csv(handle, header=0)
    if len(data_frame.columns) > 0 and data_frame.columns[0].startswith("Unnamed"):
        data_frame = data_frame.drop(data_frame.columns[0], axis=1)
    return data_frame


def normalize_windows(inputs: np.ndarray, seq_length: int) -> tuple[np.ndarray, np.ndarray]:
    base_seq = inputs[:, :seq_length, 0]
    nonzeros = (base_seq > 0).sum(1)
    inputs = inputs[nonzeros > 0]
    base_seq = inputs[:, :seq_length, 0]
    nonzeros = nonzeros[nonzeros > 0]
    v = base_seq.sum(1) / nonzeros
    v[v == 0] = 1
    inputs[:, :, 0] = inputs[:, :, 0] / v[:, None]
    return inputs, v


def save_flow_windows(sequences: list[np.ndarray], seq_length: int, slide_step: int, predict_length: int, save_dir: Path) -> list[Path]:
    train_data: list[np.ndarray] = []
    test_data: list[np.ndarray] = []
    for seq_id in range(len(sequences)):
        split_start = 0
        single_seq = sequences[seq_id][:, 0]
        single_covariate = sequences[seq_id][:, 1:]
        windows = (len(single_seq) - seq_length + slide_step) // slide_step
        count = 0
        train_count = int(0.97 * windows)
        while len(single_seq[split_start:]) > (seq_length + predict_length):
            seq_data = single_seq[split_start : (split_start + seq_length + predict_length - 1)]
            single_data = np.zeros((seq_length + predict_length - 1, 5), dtype=np.float32)
            single_data[:, 0] = seq_data.copy()
            single_data[:, 1:4] = single_covariate[split_start : (split_start + seq_length + predict_length - 1)]
            single_data[:, -1] = seq_id

            count += 1
            if count < train_count:
                train_data.append(single_data)
            else:
                test_data.append(single_data)
            split_start += slide_step

    save_dir.mkdir(parents=True, exist_ok=True)
    train_data_arr = np.array(train_data, dtype=np.float32)
    train_data_arr, train_v = normalize_windows(train_data_arr, seq_length)
    test_data_arr = np.array(test_data, dtype=np.float32)
    test_data_arr, test_v = normalize_windows(test_data_arr, seq_length)

    train_data_out = save_dir / "train_data_flow.npy"
    train_v_out = save_dir / "train_v_flow.npy"
    test_data_out = save_dir / "test_data_flow.npy"
    test_v_out = save_dir / "test_v_flow.npy"
    save_array(train_data_out, train_data_arr)
    save_array(train_v_out, train_v)
    save_array(test_data_out, test_data_arr)
    save_array(test_v_out, test_v)
    return [train_data_out, train_v_out, test_data_out, test_v_out]


def preprocess_flow(
    csv_path: Path,
    output_dir: Path,
    *,
    seq_length: int = 192,
    slide_step: int = 24,
    predict_length: int = 24,
) -> Plan:
    data_frame = load_flow_dataframe(csv_path)
    grouped_data = list(data_frame.groupby(["app_name", "zone"]))
    all_data: list[np.ndarray] = []
    min_length = 10000

    for _, grouped_df in grouped_data:
        single_df = grouped_df.drop(labels=["app_name", "zone"], axis=1).sort_values(by="time", ascending=True)
        times = pd.to_datetime(single_df.time)
        single_df["weekday"] = times.dt.dayofweek / 7
        single_df["hour"] = times.dt.hour / 24
        single_df["month"] = times.dt.month / 12
        temp_data = single_df.values[:, 1:]
        if (temp_data[:, 0] == 0).sum() / len(temp_data) > 0.2 or len(temp_data) < 3000:
            continue
        if len(temp_data) < min_length:
            min_length = len(temp_data)
        all_data.append(temp_data)

    if not all_data:
        raise SystemExit("No flow sequences survived sparsity and length filtering.")

    all_data_arr = np.array([data[len(data) - min_length :] for data in all_data]).transpose(1, 0, 2).astype(np.float32)
    train_end = min(int(0.8 * min_length), min_length - 1000)
    covariates = all_data_arr.copy()
    covariates[:, :, :-1] = covariates[:, :, 1:]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = save_flow_windows(all_data_arr.transpose(1, 0, 2), seq_length, slide_step, predict_length, output_dir)
    return Plan("flow preprocessing", [csv_path], output_files)


def load_wind_data(csv_path: Path) -> np.ndarray:
    df = pd.read_csv(csv_path)
    return df.values.transpose(1, 0)


def get_wind_covariates(data_len: int, start_day: str) -> np.ndarray:
    from datetime import datetime

    start_timestamp = datetime.timestamp(datetime.strptime(start_day, "%Y-%m-%d %H:%M:%S"))
    timestamps = np.arange(data_len) * 3600 + start_timestamp
    timestamps = [datetime.fromtimestamp(i) for i in timestamps]
    weekdays = stats.zscore(np.array([i.weekday() for i in timestamps]))
    hours = stats.zscore(np.array([i.hour for i in timestamps]))
    months = stats.zscore(np.array([i.month for i in timestamps]))
    return np.stack([weekdays, hours, months], axis=1)


def normalize_wind(inputs: np.ndarray, seq_length: int) -> tuple[np.ndarray, np.ndarray]:
    base_seq = inputs[:, :seq_length, 0]
    nonzeros = (base_seq > 0).sum(1)
    inputs = inputs[nonzeros > 0]
    base_seq = inputs[:, :seq_length, 0]
    nonzeros = nonzeros[nonzeros > 0]
    v = base_seq.sum(1) / nonzeros
    v[v == 0] = 1
    inputs[:, :, 0] = inputs[:, :, 0] / v[:, None]
    return inputs, v


def save_wind_windows(sequences: np.ndarray, covariates: np.ndarray, seq_length: int, slide_step: int, predict_length: int, save_dir: Path) -> list[Path]:
    data_length = len(sequences[0])
    windows = (data_length - seq_length + slide_step) // slide_step
    train_windows = int(0.97 * windows)
    test_windows = windows - train_windows
    train_data = np.zeros((train_windows * len(sequences), seq_length + predict_length - 1, 5), dtype=np.float32)
    test_data = np.zeros((test_windows * len(sequences), seq_length + predict_length - 1, 5), dtype=np.float32)

    count = 0
    split_start = 0
    seq_ids = np.arange(len(sequences))[:, None]
    end = split_start + seq_length + predict_length - 1
    while end <= data_length:
        if count < train_windows:
            train_data[count * len(sequences) : (count + 1) * len(sequences), :, 0] = sequences[:, split_start:end]
            train_data[count * len(sequences) : (count + 1) * len(sequences), :, 1:4] = covariates[split_start:end, :]
            train_data[count * len(sequences) : (count + 1) * len(sequences), :, -1] = seq_ids
        else:
            test_data[(count - train_windows) * len(sequences) : (count - train_windows + 1) * len(sequences), :, 0] = sequences[:, split_start:end]
            test_data[(count - train_windows) * len(sequences) : (count - train_windows + 1) * len(sequences), :, 1:4] = covariates[split_start:end, :]
            test_data[(count - train_windows) * len(sequences) : (count - train_windows + 1) * len(sequences), :, -1] = seq_ids

        count += 1
        split_start += slide_step
        end = split_start + seq_length + predict_length - 1

    save_dir.mkdir(parents=True, exist_ok=True)
    train_data, train_v = normalize_wind(train_data, seq_length)
    test_data, test_v = normalize_wind(test_data, seq_length)
    train_data_out = save_dir / "train_data_wind.npy"
    train_v_out = save_dir / "train_v_wind.npy"
    test_data_out = save_dir / "test_data_wind.npy"
    test_v_out = save_dir / "test_v_wind.npy"
    save_array(train_data_out, train_data)
    save_array(train_v_out, train_v)
    save_array(test_data_out, test_data)
    save_array(test_v_out, test_v)
    return [train_data_out, train_v_out, test_data_out, test_v_out]


def preprocess_wind(
    csv_path: Path,
    output_dir: Path,
    *,
    seq_length: int = 192,
    slide_step: int = 24,
    predict_length: int = 24,
    start_day: str = "1986-01-01 00:00:00",
) -> Plan:
    all_data = load_wind_data(csv_path)
    covariates = get_wind_covariates(len(all_data[0]), start_day)
    output_files = save_wind_windows(all_data, covariates, seq_length, slide_step, predict_length, output_dir)
    return Plan("wind preprocessing", [csv_path], output_files)


def generate_sin(x: np.ndarray, periods: list[int], amplitudes: np.ndarray) -> np.ndarray:
    y = np.zeros(len(x))
    for i, period in enumerate(periods):
        y += amplitudes[i] * np.sin(2 * np.pi / period * x)
    return y


def gen_sin_covariates(x: np.ndarray, index: int) -> np.ndarray:
    covariates = np.zeros((x.shape[0], 4))
    covariates[:, 0] = (x // 24) % 7
    covariates[:, 1] = x % 24
    covariates[:, 2] = (x // (24 * 30)) % 12
    covariates[:, 0] = covariates[:, 0] / 6
    covariates[:, 1] = covariates[:, 1] / 23
    covariates[:, 2] = covariates[:, 2] / 11
    covariates[:, -1] = np.zeros(x.shape[0]) + index
    return covariates


def polynomial_decay_cov(length: int) -> tuple[np.ndarray, np.ndarray]:
    mean = np.zeros(length)
    x_axis = np.arange(length)
    distance = np.abs(x_axis[:, None] - x_axis[None, :])
    cov = 1 / (distance + 1)
    return mean, cov


def multivariate_normal(mean: np.ndarray, cov: np.ndarray, seq_num: int) -> np.ndarray:
    return np.random.multivariate_normal(mean, cov, (seq_num,), "raise")


def preprocess_synthetic(
    output_file: Path,
    *,
    seq_num: int = 60,
    seq_len: int | None = None,
    seed: int | None = None,
) -> Plan:
    if seed is not None:
        np.random.seed(seed)

    periods = [24, 168, 720]
    if seq_len is None:
        seq_len = periods[-1] * 20

    data = []
    covariates = []
    for i in range(seq_num):
        start = int(np.random.uniform(0, periods[-1]))
        x = start + np.arange(seq_len)
        amplitudes = np.random.uniform(5, 10, 3)
        y = generate_sin(x, periods, amplitudes)
        data.append(y)
        covariates.append(gen_sin_covariates(x, i))

    data_arr = np.array(data)
    mean, cov = polynomial_decay_cov(seq_len)
    noise = multivariate_normal(mean, cov, seq_num)
    data_arr = data_arr + noise
    covariates_arr = np.array(covariates)
    data_arr = np.concatenate([data_arr[:, :, None], covariates_arr], axis=2)
    save_array(output_file, data_arr.astype(np.float32))
    return Plan("synthetic generation", [], [output_file])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bundle the Pyraformer preprocessing entry points.")
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="Root of the LTSF-Linear checkout. Relative paths are resolved against this root.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print the planned outputs without writing files.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    elect = subparsers.add_parser("elect", help="Preprocess the electricity data for the single-step route.")
    elect.add_argument("--csv", type=str, required=True, help="Path to LD2011_2014.txt.")
    elect.add_argument("--output-dir", type=str, required=True, help="Directory for the .npy outputs.")
    elect.add_argument("--window-size", type=int, default=192, help="Sliding window size used by the source script.")
    elect.add_argument("--stride-size", type=int, default=24, help="Window stride used by the source script.")
    elect.add_argument("--train-start", type=str, default="2011-01-01 00:00:00")
    elect.add_argument("--train-end", type=str, default="2014-08-31 23:00:00")
    elect.add_argument("--test-start", type=str, default="2014-08-25 00:00:00")
    elect.add_argument("--test-end", type=str, default="2014-09-07 23:00:00")

    flow = subparsers.add_parser("flow", help="Preprocess the app-flow data for the single-step route.")
    flow.add_argument("--csv", type=str, required=True, help="Path to the app-flow CSV or ZIP archive.")
    flow.add_argument("--output-dir", type=str, required=True, help="Directory for the .npy outputs.")
    flow.add_argument("--seq-length", type=int, default=192)
    flow.add_argument("--slide-step", type=int, default=24)
    flow.add_argument("--predict-length", type=int, default=24)

    wind = subparsers.add_parser("wind", help="Preprocess the wind data for the single-step route.")
    wind.add_argument("--csv", type=str, required=True, help="Path to the wind CSV.")
    wind.add_argument("--output-dir", type=str, required=True, help="Directory for the .npy outputs.")
    wind.add_argument("--seq-length", type=int, default=192)
    wind.add_argument("--slide-step", type=int, default=24)
    wind.add_argument("--predict-length", type=int, default=24)
    wind.add_argument("--start-day", type=str, default="1986-01-01 00:00:00")

    synthetic = subparsers.add_parser("synthetic", help="Generate the synthetic sinusoid dataset.")
    synthetic.add_argument("--output-file", type=str, required=True, help="Path for synthetic.npy.")
    synthetic.add_argument("--seq-num", type=int, default=60)
    synthetic.add_argument("--seq-len", type=int, default=None)
    synthetic.add_argument("--seed", type=int, default=None)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    repo_root = discover_repo_root(args.repo_root)

    if args.command == "elect":
        csv_path = resolve_path(repo_root, args.csv)
        output_dir = resolve_path(repo_root, args.output_dir)
        if args.dry_run:
            train_prefix = output_dir / "train_"
            test_prefix = output_dir / "test_"
            print_plan(
                Plan(
                    "elect dry-run",
                    [csv_path],
                    [
                        train_prefix.with_name(train_prefix.name + "data_elect.npy"),
                        train_prefix.with_name(train_prefix.name + "v_elect.npy"),
                        train_prefix.with_name(train_prefix.name + "label_elect.npy"),
                        test_prefix.with_name(test_prefix.name + "data_elect.npy"),
                        test_prefix.with_name(test_prefix.name + "v_elect.npy"),
                        test_prefix.with_name(test_prefix.name + "label_elect.npy"),
                    ],
                )
            )
            return 0
        plans = preprocess_elect(
            csv_path,
            output_dir,
            window_size=args.window_size,
            stride_size=args.stride_size,
            train_start=args.train_start,
            train_end=args.train_end,
            test_start=args.test_start,
            test_end=args.test_end,
        )
        for plan in plans:
            print_plan(plan)
        return 0

    if args.command == "flow":
        csv_path = resolve_path(repo_root, args.csv)
        output_dir = resolve_path(repo_root, args.output_dir)
        if args.dry_run:
            print_plan(
                Plan(
                    "flow dry-run",
                    [csv_path],
                    [
                        output_dir / "train_data_flow.npy",
                        output_dir / "train_v_flow.npy",
                        output_dir / "test_data_flow.npy",
                        output_dir / "test_v_flow.npy",
                    ],
                )
            )
            return 0
        plan = preprocess_flow(
            csv_path,
            output_dir,
            seq_length=args.seq_length,
            slide_step=args.slide_step,
            predict_length=args.predict_length,
        )
        print_plan(plan)
        return 0

    if args.command == "wind":
        csv_path = resolve_path(repo_root, args.csv)
        output_dir = resolve_path(repo_root, args.output_dir)
        if args.dry_run:
            print_plan(
                Plan(
                    "wind dry-run",
                    [csv_path],
                    [
                        output_dir / "train_data_wind.npy",
                        output_dir / "train_v_wind.npy",
                        output_dir / "test_data_wind.npy",
                        output_dir / "test_v_wind.npy",
                    ],
                )
            )
            return 0
        plan = preprocess_wind(
            csv_path,
            output_dir,
            seq_length=args.seq_length,
            slide_step=args.slide_step,
            predict_length=args.predict_length,
            start_day=args.start_day,
        )
        print_plan(plan)
        return 0

    if args.command == "synthetic":
        output_file = resolve_path(repo_root, args.output_file)
        if args.dry_run:
            print_plan(Plan("synthetic dry-run", [], [output_file]))
            return 0
        plan = preprocess_synthetic(
            output_file,
            seq_num=args.seq_num,
            seq_len=args.seq_len,
            seed=args.seed,
        )
        print_plan(plan)
        return 0

    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
