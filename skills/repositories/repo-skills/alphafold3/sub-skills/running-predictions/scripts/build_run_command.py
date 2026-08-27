#!/usr/bin/env python3
"""Build an AlphaFold 3 run command without executing it."""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import PurePosixPath


def _bool_flag(name: str, enabled: bool) -> list[str]:
    return [f"--{name}=true" if enabled else f"--{name}=false"]


def _container_path(host_path: str, mount_point: str, *, file_name: str | None = None) -> str:
    if file_name is not None:
        return str(PurePosixPath(mount_point) / file_name)
    return mount_point


def _add_optional(command: list[str], flag: str, value: str | int | None) -> None:
    if value is not None:
        command.append(f"--{flag}={value}")


def build_run_alphafold_args(args: argparse.Namespace, *, docker_paths: bool) -> list[str]:
    if bool(args.json_path) == bool(args.input_dir):
        raise SystemExit("Specify exactly one of --json_path or --input_dir.")
    if not args.output_dir:
        raise SystemExit("--output_dir is required.")
    if not args.run_data_pipeline and not args.run_inference:
        raise SystemExit("At least one stage must run; enable data pipeline or inference.")

    if docker_paths:
        input_flag = []
        if args.json_path:
            input_flag = ["--json_path", _container_path(args.json_path, "/root/af_input", file_name=PurePosixPath(args.json_path).name)]
        else:
            input_flag = ["--input_dir", "/root/af_input"]
        output_dir = "/root/af_output"
        model_dir = "/root/models"
        db_dirs = ["/root/public_databases"] if args.db_dir else []
    else:
        input_flag = ["--json_path", args.json_path] if args.json_path else ["--input_dir", args.input_dir]
        output_dir = args.output_dir
        model_dir = args.model_dir
        db_dirs = args.db_dir or []

    run_args = ["python", args.runner]
    run_args.append(f"{input_flag[0]}={input_flag[1]}")
    run_args.append(f"--output_dir={output_dir}")
    if model_dir:
        run_args.append(f"--model_dir={model_dir}")
    for db_dir in db_dirs:
        run_args.append(f"--db_dir={db_dir}")

    run_args.extend(_bool_flag("run_data_pipeline", args.run_data_pipeline))
    run_args.extend(_bool_flag("run_inference", args.run_inference))

    if args.force_output_dir:
        run_args.append("--force_output_dir=true")
    if args.compress_large_output_files:
        run_args.append("--compress_large_output_files=true")
    if args.save_embeddings:
        run_args.append("--save_embeddings=true")
    if args.save_distogram:
        run_args.append("--save_distogram=true")

    _add_optional(run_args, "gpu_device", args.gpu_device)
    _add_optional(run_args, "buckets", args.buckets)
    _add_optional(run_args, "flash_attention_implementation", args.flash_attention_implementation)
    _add_optional(run_args, "jax_compilation_cache_dir", args.jax_compilation_cache_dir)
    _add_optional(run_args, "num_recycles", args.num_recycles)
    _add_optional(run_args, "num_diffusion_samples", args.num_diffusion_samples)
    _add_optional(run_args, "num_seeds", args.num_seeds)
    _add_optional(run_args, "jackhmmer_n_cpu", args.jackhmmer_n_cpu)
    _add_optional(run_args, "jackhmmer_max_parallel_shards", args.jackhmmer_max_parallel_shards)
    _add_optional(run_args, "nhmmer_n_cpu", args.nhmmer_n_cpu)
    _add_optional(run_args, "nhmmer_max_parallel_shards", args.nhmmer_max_parallel_shards)

    for item in args.extra_flag:
        run_args.append(item if item.startswith("--") else f"--{item}")

    return run_args


def build_docker_command(args: argparse.Namespace) -> list[str]:
    volumes = []
    input_source = args.json_path if args.json_path else args.input_dir
    input_mount_source = str(PurePosixPath(input_source).parent) if args.json_path else input_source
    volumes.extend(["--volume", f"{input_mount_source}:/root/af_input:ro"])
    volumes.extend(["--volume", f"{args.output_dir}:/root/af_output"])
    if args.model_dir:
        volumes.extend(["--volume", f"{args.model_dir}:/root/models:ro"])
    if args.db_dir:
        if len(args.db_dir) > 1:
            raise SystemExit("Docker mode supports one --db_dir mount; use local mode or explicit --extra_flag database paths for split databases.")
        volumes.extend(["--volume", f"{args.db_dir[0]}:/root/public_databases:ro"])

    command = ["docker", "run", "--rm", "-it"]
    command.extend(volumes)
    if args.gpus:
        command.extend(["--gpus", args.gpus])
    command.append(args.image)
    command.extend(build_run_alphafold_args(args, docker_paths=True))
    return command


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["docker", "local"], default="docker", help="Print a Docker command or a local Python command.")
    parser.add_argument("--json_path", help="Path to one input JSON file.")
    parser.add_argument("--input_dir", help="Directory of input JSON files.")
    parser.add_argument("--output_dir", required=True, help="Output directory path.")
    parser.add_argument("--model_dir", help="Model parameter directory.")
    parser.add_argument("--db_dir", action="append", help="Database directory. Repeatable in local mode.")
    parser.add_argument("--runner", default="run_alphafold.py", help="Runner script path inside the selected environment.")
    parser.add_argument("--image", default="alphafold3", help="Docker image name.")
    parser.add_argument("--gpus", default="all", help="Docker --gpus value; use an empty string to omit.")

    stage = parser.add_argument_group("stage flags")
    stage.add_argument("--run_data_pipeline", dest="run_data_pipeline", action="store_true", default=True, help="Enable data pipeline stage.")
    stage.add_argument("--no-run_data_pipeline", dest="run_data_pipeline", action="store_false", help="Disable data pipeline stage.")
    stage.add_argument("--run_inference", dest="run_inference", action="store_true", default=True, help="Enable inference stage.")
    stage.add_argument("--no-run_inference", dest="run_inference", action="store_false", help="Disable inference stage.")

    output = parser.add_argument_group("output flags")
    output.add_argument("--force_output_dir", action="store_true", help="Allow existing non-empty output directory.")
    output.add_argument("--compress_large_output_files", action="store_true", help="Compress large output files.")
    output.add_argument("--save_embeddings", action="store_true", help="Request embeddings output.")
    output.add_argument("--save_distogram", action="store_true", help="Request distogram output.")

    perf = parser.add_argument_group("performance flags")
    perf.add_argument("--gpu_device", type=int, help="GPU device index.")
    perf.add_argument("--buckets", help="Comma-separated compilation buckets.")
    perf.add_argument("--flash_attention_implementation", choices=["triton", "cudnn", "xla"], help="Flash attention implementation.")
    perf.add_argument("--jax_compilation_cache_dir", help="JAX compilation cache directory.")
    perf.add_argument("--num_recycles", type=int, help="Number of recycles.")
    perf.add_argument("--num_diffusion_samples", type=int, help="Number of diffusion samples.")
    perf.add_argument("--num_seeds", type=int, help="Expand a single input seed to this many seeds.")
    perf.add_argument("--jackhmmer_n_cpu", type=int, help="CPUs per Jackhmmer process.")
    perf.add_argument("--jackhmmer_max_parallel_shards", type=int, help="Maximum parallel Jackhmmer shards.")
    perf.add_argument("--nhmmer_n_cpu", type=int, help="CPUs per Nhmmer process.")
    perf.add_argument("--nhmmer_max_parallel_shards", type=int, help="Maximum parallel Nhmmer shards.")
    parser.add_argument("--extra_flag", action="append", default=[], help="Additional raw run_alphafold.py flag, e.g. --extra_flag=max_template_date=2020-01-01. Repeatable.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    command = build_docker_command(args) if args.mode == "docker" else build_run_alphafold_args(args, docker_paths=False)
    print(shlex.join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
