#!/usr/bin/env python3
# Copyright (c) 2022 Huawei Technologies Co., Ltd.
# Licensed under CC BY-NC-SA 4.0 (Attribution-NonCommercial-ShareAlike 4.0 International) (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode
#
# The code is released for academic research use only. For commercial use, please contact Huawei Technologies Co., Ltd.
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Adapted from RePaint's guided_diffusion/scheduler.py into a headless, self-contained CLI helper.

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

SOURCE_DEFAULT_START_RESAMPLING = 100000000
DEFAULT_JUMP_PARAMS = {
    "t_T": 250,
    "n_sample": 1,
    "jump_length": 10,
    "jump_n_sample": 10,
    "jump2_length": 1,
    "jump2_n_sample": 1,
    "jump3_length": 1,
    "jump3_n_sample": 1,
    "start_resampling": SOURCE_DEFAULT_START_RESAMPLING,
}
DEFAULT_SIMPLE_PARAMS = {
    "t_T": 250,
    "t_0": -1,
    "n_sample": 1,
    "n_steplength": 1,
}


def get_schedule(t_T: int, t_0: int, n_sample: int, n_steplength: int, debug: int = 0) -> List[int]:
    if n_steplength > 1:
        if not n_sample > 1:
            raise RuntimeError("n_steplength has no effect if n_sample=1")

    t = t_T
    times = [t]
    while t >= 0:
        t = t - 1
        times.append(t)
        n_steplength_cur = min(n_steplength, t_T - t)

        for _ in range(n_sample - 1):
            for _ in range(n_steplength_cur):
                t = t + 1
                times.append(t)
            for _ in range(n_steplength_cur):
                t = t - 1
                times.append(t)

    _check_times(times, t_0, t_T)

    if debug == 2:
        _plot_times(times)

    return times


def _check_times(times: List[int], t_0: int, t_T: int) -> None:
    assert times[0] > times[1], (times[0], times[1])
    assert times[-1] == -1, times[-1]
    for t_last, t_cur in zip(times[:-1], times[1:]):
        assert abs(t_last - t_cur) == 1, (t_last, t_cur)
    for t in times:
        assert t >= t_0, (t, t_0)
        assert t <= t_T, (t, t_T)


def _plot_times(times: List[int], out_path: Optional[Path] = None, title: Optional[str] = None) -> Path:
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        if exc.name == "matplotlib":
            raise ModuleNotFoundError(
                "matplotlib is required for plotting. Install matplotlib or rerun with --no-plot."
            ) from exc
        raise

    fig, ax = plt.subplots(figsize=(14, 6))
    x = list(range(len(times)))
    ax.plot(x, times, linewidth=1.25)
    ax.set_xlabel("Schedule index")
    ax.set_ylabel("Diffusion time t")
    ax.grid(True, alpha=0.25)
    if title:
        ax.set_title(title)
    fig.tight_layout()

    if out_path is None:
        out_path = Path("schedule.png")
    out_path = out_path.expanduser().resolve() if out_path.is_absolute() else out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    return out_path


def get_schedule_jump(
    t_T: int,
    n_sample: int,
    jump_length: int,
    jump_n_sample: int,
    jump2_length: int = 1,
    jump2_n_sample: int = 1,
    jump3_length: int = 1,
    jump3_n_sample: int = 1,
    start_resampling: int = SOURCE_DEFAULT_START_RESAMPLING,
) -> List[int]:
    jumps: Dict[int, int] = {}
    for j in range(0, t_T - jump_length, jump_length):
        jumps[j] = jump_n_sample - 1

    jumps2: Dict[int, int] = {}
    for j in range(0, t_T - jump2_length, jump2_length):
        jumps2[j] = jump2_n_sample - 1

    jumps3: Dict[int, int] = {}
    for j in range(0, t_T - jump3_length, jump3_length):
        jumps3[j] = jump3_n_sample - 1

    t = t_T
    ts: List[int] = []

    while t >= 1:
        t = t - 1
        ts.append(t)

        if t + 1 < t_T - 1 and t <= start_resampling:
            for _ in range(n_sample - 1):
                t = t + 1
                ts.append(t)

                if t >= 0:
                    t = t - 1
                    ts.append(t)

        if jumps3.get(t, 0) > 0 and t <= start_resampling - jump3_length:
            jumps3[t] = jumps3[t] - 1
            for _ in range(jump3_length):
                t = t + 1
                ts.append(t)

        if jumps2.get(t, 0) > 0 and t <= start_resampling - jump2_length:
            jumps2[t] = jumps2[t] - 1
            for _ in range(jump2_length):
                t = t + 1
                ts.append(t)
            jumps3 = {}
            for j in range(0, t_T - jump3_length, jump3_length):
                jumps3[j] = jump3_n_sample - 1

        if jumps.get(t, 0) > 0 and t <= start_resampling - jump_length:
            jumps[t] = jumps[t] - 1
            for _ in range(jump_length):
                t = t + 1
                ts.append(t)
            jumps2 = {}
            for j in range(0, t_T - jump2_length, jump2_length):
                jumps2[j] = jump2_n_sample - 1

            jumps3 = {}
            for j in range(0, t_T - jump3_length, jump3_length):
                jumps3[j] = jump3_n_sample - 1

    ts.append(-1)

    _check_times(ts, -1, t_T)

    return ts


def get_schedule_jump_paper() -> List[int]:
    t_T = 250
    jump_length = 10
    jump_n_sample = 10

    jumps: Dict[int, int] = {}
    for j in range(0, t_T - jump_length, jump_length):
        jumps[j] = jump_n_sample - 1

    t = t_T
    ts: List[int] = []

    while t >= 1:
        t = t - 1
        ts.append(t)

        if jumps.get(t, 0) > 0:
            jumps[t] = jumps[t] - 1
            for _ in range(jump_length):
                t = t + 1
                ts.append(t)

    ts.append(-1)

    _check_times(ts, -1, t_T)

    return ts


def get_schedule_jump_test(to_supplement: bool = False) -> Path:
    ts = get_schedule_jump(
        t_T=250,
        n_sample=1,
        jump_length=10,
        jump_n_sample=10,
        jump2_length=1,
        jump2_n_sample=1,
        jump3_length=1,
        jump3_n_sample=1,
        start_resampling=250,
    )
    out_path = Path("schedule.png")
    _plot_times(ts, out_path=out_path, title="RePaint jump schedule")
    if to_supplement:
        supplemental = Path("jump_sched.pdf")
        _plot_times(ts, out_path=supplemental, title="RePaint jump schedule")
    print(out_path)
    return out_path


def load_config_schedule(path: Path) -> Dict[str, Any]:
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "PyYAML is required to read --config files. Install pyyaml or pass explicit CLI parameters."
        ) from exc

    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a YAML mapping")
    params = data.get("schedule_jump_params")
    if params is None:
        raise ValueError(f"{path} does not define schedule_jump_params")
    if not isinstance(params, dict):
        raise ValueError("schedule_jump_params must be a mapping")
    return params


def _positive_int(value: Any, name: str) -> int:
    value = int(value)
    if value < 1:
        raise ValueError(f"{name} must be >= 1")
    return value


def _nonnegative_int(value: Any, name: str) -> int:
    value = int(value)
    if value < 0:
        raise ValueError(f"{name} must be >= 0")
    return value


def _build_jump_params(args: argparse.Namespace) -> Dict[str, int]:
    params: Dict[str, int] = dict(DEFAULT_JUMP_PARAMS)
    if args.config is not None:
        config_params = load_config_schedule(args.config)
        unexpected = sorted(set(config_params) - set(DEFAULT_JUMP_PARAMS))
        if unexpected:
            raise ValueError(f"unsupported schedule_jump_params keys: {', '.join(unexpected)}")
        for key, value in config_params.items():
            params[key] = int(value)

    for key in DEFAULT_JUMP_PARAMS:
        value = getattr(args, key)
        if value is not None:
            params[key] = int(value)

    params["t_T"] = _positive_int(params["t_T"], "t_T")
    params["n_sample"] = _positive_int(params["n_sample"], "n_sample")
    params["jump_length"] = _positive_int(params["jump_length"], "jump_length")
    params["jump_n_sample"] = _positive_int(params["jump_n_sample"], "jump_n_sample")
    params["jump2_length"] = _positive_int(params["jump2_length"], "jump2_length")
    params["jump2_n_sample"] = _positive_int(params["jump2_n_sample"], "jump2_n_sample")
    params["jump3_length"] = _positive_int(params["jump3_length"], "jump3_length")
    params["jump3_n_sample"] = _positive_int(params["jump3_n_sample"], "jump3_n_sample")
    params["start_resampling"] = _nonnegative_int(params["start_resampling"], "start_resampling")
    return params


def _build_simple_params(args: argparse.Namespace) -> Dict[str, int]:
    params: Dict[str, int] = dict(DEFAULT_SIMPLE_PARAMS)
    for key in DEFAULT_SIMPLE_PARAMS:
        value = getattr(args, key)
        if value is not None:
            params[key] = int(value)

    params["t_T"] = _positive_int(params["t_T"], "t_T")
    params["t_0"] = int(params["t_0"])
    params["n_sample"] = _positive_int(params["n_sample"], "n_sample")
    params["n_steplength"] = _positive_int(params["n_steplength"], "n_steplength")
    if params["t_0"] > -1:
        raise ValueError("t_0 must be <= -1 because the schedule ends at -1")
    if params["n_steplength"] > 1 and params["n_sample"] == 1:
        raise RuntimeError("n_steplength has no effect if n_sample=1")
    return params


def _summarize(times: List[int], mode: str, params: Dict[str, int], preview_count: int) -> Dict[str, Any]:
    pairs = list(zip(times[:-1], times[1:]))
    reverse_steps = sum(1 for a, b in pairs if b < a)
    forward_steps = sum(1 for a, b in pairs if b > a)
    summary = {
        "mode": mode,
        "parameters": params,
        "entries": len(times),
        "transitions": len(pairs),
        "reverse_denoise_steps": reverse_steps,
        "forward_undo_steps": forward_steps,
        "start": times[0],
        "end": times[-1],
        "min": min(times),
        "max": max(times),
        "preview": {
            "first": times[:preview_count],
            "last": times[-preview_count:],
        },
        "notes": [],
    }
    if mode == "jump":
        if params["jump_n_sample"] == 1:
            summary["notes"].append("jump_n_sample=1 disables the main jump family")
        if params["start_resampling"] > params["t_T"]:
            summary["notes"].append("start_resampling is above t_T; resampling is eligible from the beginning")
        if params["jump_length"] >= params["t_T"]:
            summary["notes"].append("jump_length is at least t_T; the main jump family has no jump locations")
    return summary


def _write_json(path: Path, payload: Dict[str, Any]) -> Path:
    path = path.expanduser().resolve() if path.is_absolute() else path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def _write_csv(path: Path, times: Iterable[int]) -> Path:
    path = path.expanduser().resolve() if path.is_absolute() else path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["index", "t"])
        for idx, t in enumerate(times):
            writer.writerow([idx, t])
    return path


def _default_stem(mode: str, params: Dict[str, int]) -> str:
    if mode == "jump":
        stem = f"schedule_jump_tT{params['t_T']}_jl{params['jump_length']}_jn{params['jump_n_sample']}"
        if params.get("n_sample", 1) != 1:
            stem += f"_ns{params['n_sample']}"
        if params.get("jump2_length", 1) != 1 or params.get("jump2_n_sample", 1) != 1:
            stem += f"_j2{params['jump2_length']}x{params['jump2_n_sample']}"
        if params.get("jump3_length", 1) != 1 or params.get("jump3_n_sample", 1) != 1:
            stem += f"_j3{params['jump3_length']}x{params['jump3_n_sample']}"
        if params.get("start_resampling", SOURCE_DEFAULT_START_RESAMPLING) != SOURCE_DEFAULT_START_RESAMPLING:
            stem += f"_sr{params['start_resampling']}"
        return stem
    return f"schedule_simple_tT{params['t_T']}_ns{params['n_sample']}_sl{params['n_steplength']}"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render and summarize RePaint jump schedules in a headless, self-contained way.",
    )
    parser.add_argument("--mode", choices=("jump", "simple"), default="jump", help="Choose the RePaint jump helper or the alternate simple helper.")
    parser.add_argument("--config", type=Path, default=None, help="Optional RePaint YAML config that contains schedule_jump_params.")
    parser.add_argument("--t_T", type=int, default=None, help="Schedule horizon.")
    parser.add_argument("--n_sample", type=int, default=None, help="Local resampling count.")
    parser.add_argument("--jump_length", type=int, default=None, help="Main jump length for jump mode.")
    parser.add_argument("--jump_n_sample", type=int, default=None, help="Main jump visit count for jump mode.")
    parser.add_argument("--jump2_length", type=int, default=None, help="Optional second jump family length.")
    parser.add_argument("--jump2_n_sample", type=int, default=None, help="Optional second jump family visit count.")
    parser.add_argument("--jump3_length", type=int, default=None, help="Optional third jump family length.")
    parser.add_argument("--jump3_n_sample", type=int, default=None, help="Optional third jump family visit count.")
    parser.add_argument("--start_resampling", type=int, default=None, help="Delay threshold for resampling in jump mode.")
    parser.add_argument("--t_0", type=int, default=None, help="Lower bound used by the simple helper.")
    parser.add_argument("--n_steplength", type=int, default=None, help="Step length used by the simple helper.")
    parser.add_argument("--out", type=Path, default=None, help="PNG output path for the rendered plot.")
    parser.add_argument("--json-out", type=Path, default=None, help="JSON summary output path.")
    parser.add_argument("--csv-out", type=Path, default=None, help="Optional CSV schedule dump path.")
    parser.add_argument("--no-plot", action="store_true", help="Skip plotting and only validate/summarize the schedule.")
    parser.add_argument("--no-json", action="store_true", help="Skip JSON summary output.")
    parser.add_argument("--preview-count", type=int, default=12, help="Number of first/last schedule entries to include in the preview.")
    parser.add_argument("--print-times", action="store_true", help="Print the full schedule list as JSON to stdout.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        if args.mode == "jump":
            params = _build_jump_params(args)
            times = get_schedule_jump(**params)
        else:
            if args.config is not None:
                raise ValueError("--config reads schedule_jump_params and is only valid with jump mode")
            params = _build_simple_params(args)
            times = get_schedule(**params)

        if args.preview_count < 1:
            raise ValueError("--preview-count must be >= 1")

        summary = _summarize(times, args.mode, params, args.preview_count)

        stem = _default_stem(args.mode, params)
        out_path = args.out or (Path(f"{stem}.png") if not args.no_plot else None)
        if args.no_json:
            json_path = None
        elif args.json_out is not None:
            json_path = args.json_out
        elif args.out is not None:
            json_path = args.out.with_suffix(".json")
        else:
            json_path = Path(f"{stem}.json")

        if not args.no_plot:
            if out_path is None:
                out_path = Path(f"{stem}.png")
            plot_path = _plot_times(times, out_path=out_path, title=f"RePaint {args.mode} schedule")
            summary["plot"] = str(plot_path)
        if args.csv_out is not None:
            csv_written = _write_csv(args.csv_out, times)
            summary["csv"] = str(csv_written)
        if json_path is not None:
            summary["json"] = str(json_path)
            _write_json(json_path, summary)

        print(json.dumps(summary, indent=2, sort_keys=True))
        if args.print_times:
            print(json.dumps({"times": times}))
        return 0
    except (AssertionError, ValueError, RuntimeError, ModuleNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
