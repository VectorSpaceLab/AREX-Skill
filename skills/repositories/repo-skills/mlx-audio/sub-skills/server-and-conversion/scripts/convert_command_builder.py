from __future__ import annotations

import argparse
import shlex


def _quote(value: object) -> str:
    return shlex.quote(str(value))


def _append_option(parts: list[str], flag: str, value: object | None) -> None:
    if value is None:
        return
    parts.extend([flag, _quote(value)])


def _append_flag(parts: list[str], flag: str, enabled: bool) -> None:
    if enabled:
        parts.append(flag)


def build_command(args: argparse.Namespace) -> list[str]:
    if not args.hf_path:
        raise SystemExit("--hf-path is required")
    if not args.mlx_path:
        raise SystemExit("--mlx-path is required")
    if args.quantize and args.dequantize:
        raise SystemExit("choose either --quantize or --dequantize, not both")
    if not args.quantize and any(
        value is not None
        for value in (args.q_bits, args.q_group_size, args.q_mode if args.q_mode != "affine" else None, args.quant_predicate)
    ):
        raise SystemExit("quantization-specific flags require --quantize")

    parts = ["python", "-m", "mlx_audio.convert"]
    _append_option(parts, "--hf-path", args.hf_path)
    _append_option(parts, "--mlx-path", args.mlx_path)
    _append_flag(parts, "--quantize", args.quantize)
    _append_option(parts, "--q-group-size", args.q_group_size)
    _append_option(parts, "--q-bits", args.q_bits)
    _append_option(parts, "--q-mode", args.q_mode)
    _append_option(parts, "--quant-predicate", args.quant_predicate)
    _append_option(parts, "--dtype", args.dtype)
    _append_option(parts, "--upload-repo", args.upload_repo)
    _append_option(parts, "--revision", args.revision)
    _append_flag(parts, "--dequantize", args.dequantize)
    _append_option(parts, "--model-domain", args.model_domain)
    return parts


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a safe MLX Audio conversion command")
    parser.add_argument("--hf-path", required=True)
    parser.add_argument("--mlx-path", required=True)
    parser.add_argument("--quantize", action="store_true")
    parser.add_argument("--q-group-size", type=int)
    parser.add_argument("--q-bits", type=int)
    parser.add_argument("--q-mode", default="affine", choices=["affine", "mxfp4", "mxfp8", "nvfp4"])
    parser.add_argument("--quant-predicate", choices=["mixed_2_6", "mixed_3_4", "mixed_3_6", "mixed_4_6"])
    parser.add_argument("--dtype", choices=["float16", "bfloat16", "float32"])
    parser.add_argument("--upload-repo")
    parser.add_argument("--revision")
    parser.add_argument("--dequantize", action="store_true")
    parser.add_argument("--model-domain", choices=["tts", "stt", "sts", "lid"])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(" ".join(build_command(args)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
