#!/usr/bin/env python3
"""Smoke-check CIFAR-100 model factories against a checkout.

This helper is intentionally safe:
- no dataset download
- no training loop
- no checkpoint loading
- no file writes
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SUPPORTED_NETS = [
    "vgg16",
    "vgg13",
    "vgg11",
    "vgg19",
    "densenet121",
    "densenet161",
    "densenet169",
    "densenet201",
    "googlenet",
    "inceptionv3",
    "inceptionv4",
    "inceptionresnetv2",
    "xception",
    "resnet18",
    "resnet34",
    "resnet50",
    "resnet101",
    "resnet152",
    "preactresnet18",
    "preactresnet34",
    "preactresnet50",
    "preactresnet101",
    "preactresnet152",
    "resnext50",
    "resnext101",
    "resnext152",
    "shufflenet",
    "shufflenetv2",
    "squeezenet",
    "mobilenet",
    "mobilenetv2",
    "nasnet",
    "attention56",
    "attention92",
    "seresnet18",
    "seresnet34",
    "seresnet50",
    "seresnet101",
    "seresnet152",
    "wideresnet",
    "stochasticdepth18",
    "stochasticdepth34",
    "stochasticdepth50",
    "stochasticdepth101",
]
SUPPORTED_SET = set(SUPPORTED_NETS)
DEFAULT_REPRESENTATIVE_NETS = ["vgg16", "resnet18", "mobilenetv2", "squeezenet", "googlenet"]


class SmokeError(RuntimeError):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-check CIFAR-100 model factories from a checkout."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Path to a checkout that contains utils.py and models/.",
    )
    parser.add_argument(
        "--net",
        action="append",
        default=[],
        help="Model token to smoke. Repeat this flag or pass 'all'.",
    )
    parser.add_argument(
        "--representative",
        action="store_true",
        help="Smoke a small representative subset when --net is omitted.",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "auto"),
        default="auto",
        help="Execution device for the random forward.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Random forward batch size.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List supported tokens and exit.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable text.",
    )
    return parser


def emit_json(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True))
    sys.stdout.write("\n")


def emit_list(json_mode: bool) -> int:
    payload = {
        "ok": True,
        "count": len(SUPPORTED_NETS),
        "supported_nets": SUPPORTED_NETS,
    }
    if json_mode:
        emit_json(payload)
        return 0

    print("Supported model tokens:")
    for net in SUPPORTED_NETS:
        print(f"- {net}")
    return 0


def fail(message: str, json_mode: bool) -> int:
    if json_mode:
        emit_json({"ok": False, "error": message})
    else:
        print(message, file=sys.stderr)
    return 1


def resolve_nets(requested: list[str], representative: bool = False) -> list[str]:
    if not requested:
        if representative:
            return list(DEFAULT_REPRESENTATIVE_NETS)
        raise SmokeError("No --net provided. Pass one or more --net values, --representative, or --net all.")

    if any(token == "all" for token in requested):
        return list(SUPPORTED_NETS)

    invalid = [token for token in requested if token not in SUPPORTED_SET]
    if invalid:
        invalid_text = ", ".join(sorted(set(invalid)))
        raise SmokeError(
            f"Unsupported model token(s): {invalid_text}. Use --list or references/model-catalog.md."
        )

    ordered: list[str] = []
    seen = set()
    for token in requested:
        if token not in seen:
            ordered.append(token)
            seen.add(token)
    return ordered


def load_repo_factory(repo_root: Path | None):
    if repo_root is None:
        raise SmokeError("--repo-root is required for smoke runs.")

    repo_root = repo_root.expanduser().resolve()
    if not repo_root.is_dir():
        raise SmokeError("The directory passed via --repo-root is not an existing checkout.")
    if not (repo_root / "utils.py").is_file():
        raise SmokeError("The directory passed via --repo-root does not contain utils.py.")
    if not (repo_root / "models").is_dir():
        raise SmokeError("The directory passed via --repo-root does not contain models/.")

    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)

    try:
        import torch
    except Exception as exc:  # pragma: no cover - import failure is environment-specific
        raise SmokeError(f"torch import failed: {exc}") from exc

    try:
        import utils as repo_utils
    except Exception as exc:  # pragma: no cover - import failure is environment-specific
        raise SmokeError(f"repo import failed while loading utils.py: {exc}") from exc

    return torch, repo_utils.get_network


def resolve_device(torch, requested: str):
    if requested == "cpu":
        return torch.device("cpu")
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise SmokeError("CUDA was requested but torch.cuda.is_available() is false.")
        return torch.device("cuda")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def smoke_one(torch, get_network, name: str, device, batch_size: int) -> dict:
    if name not in SUPPORTED_SET:
        raise SmokeError(
            f"Unsupported model token '{name}'. Use --list or references/model-catalog.md."
        )

    factory_args = argparse.Namespace(net=name, gpu=(device.type == "cuda"))
    try:
        model = get_network(factory_args)
    except SystemExit as exc:
        raise SmokeError(
            f"{name}: utils.get_network exited unexpectedly. Use a supported token from the catalog."
        ) from exc
    except Exception as exc:
        raise SmokeError(f"{name}: model import or instantiation failed: {exc}") from exc

    model.eval()
    try:
        model_device = next(model.parameters()).device
    except StopIteration:
        model_device = device

    sample = torch.randn(batch_size, 3, 32, 32, device=model_device)
    with torch.no_grad():
        output = model(sample)

    if not torch.is_tensor(output):
        raise SmokeError(f"{name}: expected a tensor output, got {type(output).__name__}")

    output_shape = tuple(int(x) for x in output.shape)
    if len(output_shape) != 2 or output_shape[0] != batch_size or output_shape[1] != 100:
        raise SmokeError(
            f"{name}: expected output shape ({batch_size}, 100), got {output_shape}"
        )

    param_count = int(sum(param.numel() for param in model.parameters()))
    return {
        "net": name,
        "status": "ok",
        "device": str(model_device),
        "input_shape": [batch_size, 3, 32, 32],
        "output_shape": list(output_shape),
        "param_count": param_count,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list:
        return emit_list(args.json)

    if args.batch_size < 1:
        return fail("--batch-size must be >= 1.", args.json)

    try:
        requested_nets = resolve_nets(args.net, representative=args.representative)
    except SmokeError as exc:
        return fail(str(exc), args.json)

    try:
        torch, get_network = load_repo_factory(args.repo_root)
    except SmokeError as exc:
        return fail(str(exc), args.json)

    try:
        device = resolve_device(torch, args.device)
    except SmokeError as exc:
        return fail(str(exc), args.json)

    results = []
    for name in requested_nets:
        try:
            results.append(smoke_one(torch, get_network, name, device, args.batch_size))
        except SmokeError as exc:
            results.append({"net": name, "status": "error", "error": str(exc)})

    overall_ok = all(entry.get("status") == "ok" for entry in results)

    if args.json:
        emit_json(
            {
                "ok": overall_ok,
                "requested_device": args.device,
                "resolved_device": str(device),
                "batch_size": args.batch_size,
                "results": results,
            }
        )
    else:
        for entry in results:
            if entry.get("status") == "ok":
                print(
                    f"{entry['net']}: ok on {entry['device']} | "
                    f"input={tuple(entry['input_shape'])} -> output={tuple(entry['output_shape'])} | "
                    f"params={entry['param_count']}"
                )
            else:
                print(f"{entry['net']}: FAIL - {entry['error']}", file=sys.stderr)
        if not overall_ok:
            print("One or more smoke checks failed.", file=sys.stderr)

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
