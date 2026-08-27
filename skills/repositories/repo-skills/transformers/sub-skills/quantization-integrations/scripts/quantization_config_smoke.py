#!/usr/bin/env python3
"""No-download smoke checks for Transformers quantization config objects."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import sys
from typing import Any


INSTALL_HINTS = {
    "transformers": "pip install --upgrade transformers",
    "torch": "pip install torch",
    "accelerate": "pip install accelerate",
    "bitsandbytes": "pip install bitsandbytes accelerate torch",
    "gptq": "pip install --upgrade accelerate optimum transformers && pip install gptqmodel --no-build-isolation",
    "awq": "pip install autoawq",
    "torchao": "pip install --upgrade torchao torch transformers",
}


METHOD_CHOICES = (
    "bitsandbytes-4bit",
    "bitsandbytes-8bit",
    "gptq",
    "awq",
    "torchao-note",
    "gguf-note",
)


def package_version(package_name: str) -> str | None:
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def import_transformers_attr(attr_name: str) -> Any:
    try:
        transformers = importlib.import_module("transformers")
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(f"MISSING optional dependency: transformers import failed ({exc}). {INSTALL_HINTS['transformers']}") from exc

    try:
        return getattr(transformers, attr_name)
    except AttributeError as exc:
        raise RuntimeError(
            f"UNAVAILABLE config class: transformers.{attr_name} is not exposed by this Transformers install."
        ) from exc
    except Exception as exc:  # Lazy imports can raise optional dependency errors.
        raise RuntimeError(f"MISSING optional dependency while importing {attr_name}: {exc}") from exc


def config_to_dict(config: Any) -> dict[str, Any]:
    if hasattr(config, "to_dict"):
        data = config.to_dict()
    else:
        data = dict(getattr(config, "__dict__", {}))
    return json.loads(json.dumps(data, default=str))


def build_bitsandbytes(args: argparse.Namespace) -> tuple[Any, list[str]]:
    BitsAndBytesConfig = import_transformers_attr("BitsAndBytesConfig")
    kwargs: dict[str, Any] = {
        "load_in_4bit": args.method == "bitsandbytes-4bit",
        "load_in_8bit": args.method == "bitsandbytes-8bit",
    }
    notes = ["Requires torch plus a bitsandbytes build compatible with the target CPU/GPU backend for model loading."]

    if args.method == "bitsandbytes-4bit":
        kwargs.update(
            bnb_4bit_quant_type=args.quant_type,
            bnb_4bit_compute_dtype=args.compute_dtype,
            bnb_4bit_use_double_quant=args.double_quant,
        )
        if args.offload:
            notes.append("CPU fp32 offload is an 8-bit bitsandbytes feature; ignoring --offload for 4-bit config construction.")
    else:
        kwargs.update(
            llm_int8_threshold=args.llm_int8_threshold,
            llm_int8_enable_fp32_cpu_offload=args.offload,
        )
        if args.offload:
            notes.append("8-bit CPU offload stores offloaded weights in fp32; check CPU RAM and device_map explicitly.")

    return BitsAndBytesConfig(**kwargs), notes


def build_gptq(args: argparse.Namespace) -> tuple[Any, list[str]]:
    GPTQConfig = import_transformers_attr("GPTQConfig")
    dataset: str | list[str] | None = args.dataset
    if args.dataset_text:
        dataset = [args.dataset_text]
    config = GPTQConfig(
        bits=args.bits,
        dataset=dataset,
        group_size=args.group_size,
        desc_act=args.desc_act,
        sym=not args.asymmetric,
        backend=args.backend,
    )
    notes = [
        "Config construction does not run calibration or prove gptqmodel kernels.",
        "Real GPTQ quantization needs a tokenizer and representative calibration data.",
    ]
    return config, notes


def build_awq(args: argparse.Namespace) -> tuple[Any, list[str]]:
    AwqConfig = import_transformers_attr("AwqConfig")
    config = AwqConfig(
        bits=args.bits,
        group_size=args.group_size,
        zero_point=not args.no_zero_point,
        backend=args.awq_backend,
        version=args.awq_version,
    )
    notes = [
        "Config construction does not prove autoawq/gptqmodel backend availability or model architecture support.",
        "For pre-quantized AWQ checkpoints, prefer checkpoint metadata unless intentionally overriding backend options.",
    ]
    if args.fuse_max_seq_len is not None:
        notes.append(
            "--fuse-max-seq-len is a loading/fused-module planning check; current config construction does not prove fused kernels."
        )
    return config, notes


def build_note_config(args: argparse.Namespace) -> tuple[dict[str, Any], list[str]]:
    if args.method == "torchao-note":
        notes = [
            "TorchAoConfig usually requires torchao AOBaseConfig objects; this smoke script avoids importing torchao by default.",
            "Install torchao and construct the specific torchao.quantization config object before model loading.",
            "The removed string-based TorchAoConfig API should not be used with current docs.",
        ]
        return {"method": "torchao", "no_download": True, "config_object_required": True}, notes

    notes = [
        "GGUF/GGML is an artifact-format workflow, not a generic PyTorch quantization_config replacement.",
        "Validate that the user has a GGUF file or repository with compatible tokenizer/model metadata.",
    ]
    return {"method": "gguf", "no_download": True, "artifact_format": True}, notes


def check_packages(args: argparse.Namespace) -> list[str]:
    packages = ["transformers"]
    if args.check_backend:
        packages.extend(["torch", "accelerate"])
        if args.method.startswith("bitsandbytes"):
            packages.append("bitsandbytes")
        elif args.method == "gptq":
            packages.extend(["optimum", "gptqmodel"])
        elif args.method == "awq":
            packages.append("autoawq")
        elif args.method == "torchao-note":
            packages.append("torchao")
    lines = []
    for package_name in packages:
        version = package_version(package_name)
        if version is None:
            hint_key = "gptq" if package_name in {"gptqmodel", "optimum"} and args.method == "gptq" else package_name
            hint = INSTALL_HINTS.get(hint_key, f"pip install {package_name}")
            lines.append(f"MISSING optional dependency: {package_name}. Guidance: {hint}")
        else:
            lines.append(f"FOUND {package_name}=={version}")
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build selected Transformers quantization config objects without downloading models.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--method", choices=METHOD_CHOICES, default="bitsandbytes-4bit", help="Config family to smoke check.")
    parser.add_argument("--bits", type=int, default=4, help="Bit width for GPTQ/AWQ checks.")
    parser.add_argument("--group-size", type=int, default=128, help="Group size for GPTQ/AWQ checks; -1 means per-column when supported.")
    parser.add_argument("--dataset", choices=("wikitext2", "c4", "c4-new"), default=None, help="Named GPTQ calibration dataset marker.")
    parser.add_argument("--dataset-text", default=None, help="One literal calibration text sample for GPTQ config construction.")
    parser.add_argument("--desc-act", action="store_true", help="Enable GPTQ descending activation order.")
    parser.add_argument("--asymmetric", action="store_true", help="Use asymmetric GPTQ quantization when supported by the backend.")
    parser.add_argument("--backend", default=None, help="GPTQ backend value such as auto or marlin.")
    parser.add_argument("--quant-type", choices=("fp4", "nf4"), default="nf4", help="bitsandbytes 4-bit quantization type.")
    parser.add_argument("--compute-dtype", default="bfloat16", help="bitsandbytes 4-bit compute dtype string, such as float16 or bfloat16.")
    parser.add_argument("--double-quant", action="store_true", help="Enable bitsandbytes nested/double quantization.")
    parser.add_argument("--offload", action="store_true", help="Enable bitsandbytes 8-bit fp32 CPU offload planning.")
    parser.add_argument("--llm-int8-threshold", type=float, default=6.0, help="bitsandbytes LLM.int8 outlier threshold.")
    parser.add_argument(
        "--awq-backend",
        default="auto",
        choices=(
            "auto",
            "auto_trainable",
            "machete",
            "marlin",
            "exllama_v2",
            "exllama_v1",
            "gemm",
            "gemm_triton",
            "gemv",
            "gemv_fast",
            "torch_awq",
            "torch_fused_awq",
        ),
        help="AWQ backend value for config construction.",
    )
    parser.add_argument("--awq-version", default="gemm", choices=("gemm", "gemv", "gemv_fast", "llm-awq"), help="AWQ format/version.")
    parser.add_argument("--no-zero-point", action="store_true", help="Disable AWQ zero point quantization.")
    parser.add_argument("--fuse-max-seq-len", type=int, default=None, help="Document planned AWQ fused max sequence length; no model loading is performed.")
    parser.add_argument("--check-backend", action="store_true", help="Also report optional backend package presence.")
    parser.add_argument("--print-json", action="store_true", help="Print machine-readable JSON summary.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    builders = {
        "bitsandbytes-4bit": build_bitsandbytes,
        "bitsandbytes-8bit": build_bitsandbytes,
        "gptq": build_gptq,
        "awq": build_awq,
        "torchao-note": build_note_config,
        "gguf-note": build_note_config,
    }

    try:
        config, notes = builders[args.method](args)
        package_lines = check_packages(args)
        summary = {
            "method": args.method,
            "config_class": config.__class__.__name__,
            "config": config_to_dict(config),
            "packages": package_lines,
            "notes": notes,
        }
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"ERROR: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1

    print("OK quantization config validated")
    print(f"method: {summary['method']}")
    print(f"config_class: {summary['config_class']}")
    for line in package_lines:
        print(line)
    for note in notes:
        print(f"NOTE: {note}")
    if args.print_json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
