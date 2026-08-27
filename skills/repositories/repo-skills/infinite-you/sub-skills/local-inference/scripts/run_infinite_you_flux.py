#!/usr/bin/env python3
"""Run or preflight InfiniteYou-FLUX from the bundled skill runtime.

The generated skill bundles the InfiniteYou pipeline implementation under the
skill root's runtime/ directory. Dry-run and check-only modes never
download models or instantiate the heavy pipeline. Full generation uses the
bundled runtime by default and therefore does not require the original source
checkout, but it still requires installed dependencies, CUDA, model files, and
license-compliant model access.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

VALID_MODEL_VERSIONS = ("aes_stage2", "sim_stage1")
VALID_INFU_FLUX_VERSION = "v1.0"
DEFAULT_BASE_MODEL_PATH = "./models/FLUX.1-dev"
DEFAULT_MODEL_DIR = "./models/InfiniteYou"
REMOTE_BASE_MODEL_ID = "black-forest-labs/FLUX.1-dev"
REMOTE_INFINITE_YOU_ID = "ByteDance/InfiniteYou"


def skill_root() -> Path:
    return Path(__file__).resolve().parents[3]


def bundled_runtime_root() -> Path:
    return skill_root() / "runtime"


def configure_no_network_checks() -> None:
    os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")
    os.environ.setdefault("ALBUMENTATIONS_DISABLE_VERSION_CHECK", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")


def configure_implementation_path(implementation_root: str | None = None) -> dict[str, Any]:
    """Prefer an explicit implementation override, otherwise use bundled runtime."""

    report: dict[str, Any] = {
        "bundled_runtime": str(bundled_runtime_root()),
        "implementation_root": implementation_root,
        "selected": None,
        "warnings": [],
        "errors": [],
    }

    runtime = bundled_runtime_root()
    if not (runtime / "pipelines" / "pipeline_infu_flux.py").is_file():
        report["errors"].append(f"Bundled runtime is incomplete: {runtime}")
    else:
        sys.path.insert(0, str(runtime))
        report["selected"] = str(runtime)

    if implementation_root:
        root = Path(implementation_root).expanduser().resolve()
        if not root.is_dir():
            report["errors"].append(f"--implementation-root does not exist or is not a directory: {implementation_root}")
        elif not (root / "pipelines" / "pipeline_infu_flux.py").is_file():
            report["errors"].append("--implementation-root must contain pipelines/pipeline_infu_flux.py")
        else:
            sys.path.insert(0, str(root))
            report["selected"] = str(root)
            report["warnings"].append("Using an implementation override instead of the bundled runtime.")

    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preflight or run InfiniteYou-FLUX local inference using the bundled skill runtime.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--implementation-root",
        "--repo-root",
        dest="implementation_root",
        help=(
            "Optional override root containing pipelines/. Omit this for the self-contained bundled runtime. "
            "The --repo-root alias is kept for compatibility with older commands."
        ),
    )
    parser.add_argument("--id-image", "--id_image", default=None, help="Identity image with a clear face. Required for --check-only and generation.")
    parser.add_argument("--control-image", "--control_image", default=None, help="Optional control image with a clear face for keypoint guidance.")
    parser.add_argument("--out-results-dir", "--out_results_dir", default="./results", help="Directory where generated PNG files are written.")
    parser.add_argument("--prompt", default="A man, portrait, cinematic", help="Text prompt for generation.")
    parser.add_argument("--base-model-path", "--base_model_path", default=DEFAULT_BASE_MODEL_PATH, help="Local FLUX base model directory or, with --allow-downloads, a Hugging Face repo id.")
    parser.add_argument("--model-dir", "--model_dir", default=DEFAULT_MODEL_DIR, help="Local InfiniteYou model directory or, with --allow-downloads, a repo id/fallback source.")
    parser.add_argument("--allow-downloads", action="store_true", help="Permit upstream model download/fallback behavior during full generation. Never used by --dry-run or --check-only.")
    parser.add_argument("--infu-flux-version", "--infu_flux_version", default=VALID_INFU_FLUX_VERSION, help="InfiniteYou-FLUX version; only v1.0 is supported.")
    parser.add_argument("--model-version", "--model_version", default="aes_stage2", choices=VALID_MODEL_VERSIONS, help="Model variant: aes_stage2 favors alignment/aesthetics; sim_stage1 favors identity similarity.")
    parser.add_argument("--cuda-device", "--cuda_device", default=0, type=int, help="CUDA device index to use for generation.")
    parser.add_argument("--seed", default=0, type=int, help="Seed; 0 asks torch to choose a random seed.")
    parser.add_argument("--guidance-scale", "--guidance_scale", default=3.5, type=float, help="Diffusion guidance scale.")
    parser.add_argument("--num-steps", "--num_steps", default=30, type=int, help="Number of denoising steps.")
    parser.add_argument("--width", default=864, type=int, help="Output/control canvas width.")
    parser.add_argument("--height", default=1152, type=int, help="Output/control canvas height.")
    parser.add_argument("--infusenet-conditioning-scale", "--infusenet_conditioning_scale", default=1.0, type=float, help="Scale applied to InfuseNet conditioning.")
    parser.add_argument("--infusenet-guidance-start", "--infusenet_guidance_start", default=0.0, type=float, help="Fraction of denoising steps where InfuseNet guidance starts.")
    parser.add_argument("--infusenet-guidance-end", "--infusenet_guidance_end", default=1.0, type=float, help="Fraction of denoising steps where InfuseNet guidance ends.")
    parser.add_argument("--enable-realism-lora", "--enable_realism_lora", action="store_true", help="Load the optional Realism LoRA from the InfiniteYou support tree.")
    parser.add_argument("--enable-anti-blur-lora", "--enable_anti_blur_lora", action="store_true", help="Load the optional Anti-blur LoRA from the InfiniteYou support tree.")
    parser.add_argument("--quantize-8bit", "--quantize_8bit", action="store_true", help="Enable optimum-quanto 8-bit quantization for selected modules.")
    parser.add_argument("--cpu-offload", "--cpu_offload", action="store_true", help="Enable the pipeline's CUDA/CPU offload path to reduce peak VRAM.")
    parser.add_argument("--dry-run", action="store_true", help="Print the normalized execution plan and exit without heavy imports or filesystem mutation.")
    parser.add_argument("--check-only", action="store_true", help="Validate inputs, bundled runtime imports, CUDA, and local model paths without generation or downloads.")
    parser.add_argument("--json", action="store_true", help="Emit dry-run/check output as JSON.")
    return parser.parse_args(argv)


def looks_like_local_path(value: str) -> bool:
    if value in {REMOTE_BASE_MODEL_ID, REMOTE_INFINITE_YOU_ID}:
        return False
    if value.startswith((".", "/", "~")):
        return True
    if os.sep in value:
        first = value.split(os.sep, 1)[0]
        if first in {"models", "model", "checkpoints", "weights", "path"}:
            return True
    return False


def local_path_report(path_value: str, expected_kind: str = "any") -> dict[str, Any]:
    path = Path(path_value).expanduser()
    exists = path.exists()
    is_ok = exists
    if exists and expected_kind == "dir":
        is_ok = path.is_dir()
    if exists and expected_kind == "file":
        is_ok = path.is_file()
    return {"path": str(path), "exists": exists, "kind_ok": is_ok, "expected_kind": expected_kind}


def selected_model_paths(args: argparse.Namespace) -> dict[str, str]:
    model_dir = Path(args.model_dir).expanduser()
    infu_model = model_dir / f"infu_flux_{args.infu_flux_version}" / args.model_version
    return {
        "model_dir": str(model_dir),
        "infu_model_path": str(infu_model),
        "infusenet_model": str(infu_model / "InfuseNetModel"),
        "image_proj_model": str(infu_model / "image_proj_model.bin"),
        "insightface_root": str(model_dir / "supports" / "insightface"),
        "optional_lora_dir": str(model_dir / "supports" / "optional_loras"),
    }


def validate_args(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    if args.infu_flux_version != VALID_INFU_FLUX_VERSION:
        errors.append("Only InfiniteYou-FLUX v1.0 is supported by this repository.")
    if args.model_version not in VALID_MODEL_VERSIONS:
        errors.append("--model-version must be aes_stage2 or sim_stage1.")
    if args.width <= 0 or args.height <= 0:
        errors.append("--width and --height must be positive integers.")
    if args.num_steps <= 0:
        errors.append("--num-steps must be positive.")
    if not (0.0 <= args.infusenet_guidance_start <= 1.0):
        errors.append("--infusenet-guidance-start must be between 0 and 1.")
    if not (0.0 <= args.infusenet_guidance_end <= 1.0):
        errors.append("--infusenet-guidance-end must be between 0 and 1.")
    if args.infusenet_guidance_start > args.infusenet_guidance_end:
        errors.append("--infusenet-guidance-start must not exceed --infusenet-guidance-end.")
    return errors


def normalized_plan(args: argparse.Namespace) -> dict[str, Any]:
    loras = []
    if args.enable_realism_lora:
        loras.append("realism")
    if args.enable_anti_blur_lora:
        loras.append("anti_blur")
    return {
        "implementation_root": args.implementation_root,
        "bundled_runtime": str(bundled_runtime_root()),
        "id_image": args.id_image,
        "control_image": args.control_image,
        "out_results_dir": args.out_results_dir,
        "prompt": args.prompt,
        "base_model_path": args.base_model_path,
        "model_dir": args.model_dir,
        "allow_downloads": args.allow_downloads,
        "infu_flux_version": args.infu_flux_version,
        "model_version": args.model_version,
        "cuda_device": args.cuda_device,
        "seed": args.seed,
        "width": args.width,
        "height": args.height,
        "guidance_scale": args.guidance_scale,
        "num_steps": args.num_steps,
        "infusenet_conditioning_scale": args.infusenet_conditioning_scale,
        "infusenet_guidance_start": args.infusenet_guidance_start,
        "infusenet_guidance_end": args.infusenet_guidance_end,
        "loras": loras,
        "quantize_8bit": args.quantize_8bit,
        "cpu_offload": args.cpu_offload,
    }


def try_import(name: str) -> tuple[bool, str, str | None]:
    try:
        module = importlib.import_module(name)
        return True, "ok", getattr(module, "__file__", None)
    except Exception as exc:  # broad by design for preflight diagnostics
        return False, f"{type(exc).__name__}: {exc}", None


def check_cuda() -> dict[str, Any]:
    ok, message, _ = try_import("torch")
    if not ok:
        return {"torch_import": False, "error": message, "cuda_available": False}
    import torch

    report: dict[str, Any] = {
        "torch_import": True,
        "torch_version": torch.__version__,
        "torch_cuda_runtime": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count(),
    }
    if torch.cuda.is_available() and torch.cuda.device_count() > 0:
        report["device0"] = torch.cuda.get_device_name(0)
        report["device0_capability"] = list(torch.cuda.get_device_capability(0))
    return report


def add_path_checks(args: argparse.Namespace, errors: list[str], warnings: list[str], checks: dict[str, Any]) -> None:
    if not args.id_image:
        errors.append("id-image is required for check-only and generation.")
    for key in ("id_image", "control_image"):
        value = getattr(args, key)
        if value:
            report = local_path_report(value, "file")
            checks["paths"][key] = report
            if not report["kind_ok"]:
                errors.append(f"{key.replace('_', '-')} is missing or is not a file: {value}")

    out_dir = Path(args.out_results_dir).expanduser()
    checks["paths"]["out_results_dir"] = {
        "path": str(out_dir),
        "exists": out_dir.exists(),
        "parent_exists": out_dir.parent.exists(),
    }
    if not out_dir.exists() and not out_dir.parent.exists():
        errors.append(f"output directory parent does not exist: {out_dir.parent}")

    if args.model_dir and looks_like_local_path(args.model_dir):
        paths = selected_model_paths(args)
        checks["paths"]["model_dir"] = local_path_report(paths["model_dir"], "dir")
        checks["paths"]["infu_model_path"] = local_path_report(paths["infu_model_path"], "dir")
        checks["paths"]["infusenet_model"] = local_path_report(paths["infusenet_model"], "dir")
        checks["paths"]["image_proj_model"] = local_path_report(paths["image_proj_model"], "file")
        checks["paths"]["insightface_root"] = local_path_report(paths["insightface_root"], "dir")
        if args.enable_realism_lora:
            checks["paths"]["realism_lora"] = local_path_report(str(Path(paths["optional_lora_dir"]) / "flux_realism_lora.safetensors"), "file")
        if args.enable_anti_blur_lora:
            checks["paths"]["anti_blur_lora"] = local_path_report(str(Path(paths["optional_lora_dir"]) / "flux_anti_blur_lora.safetensors"), "file")
    else:
        warnings.append("model_dir is not a local path; full generation may use upstream download/fallback behavior only if --allow-downloads is set.")

    if args.base_model_path == REMOTE_BASE_MODEL_ID:
        warnings.append("base_model_path is the gated FLUX.1-dev repo id; license acceptance and Hugging Face authentication may be required.")
    elif args.base_model_path and looks_like_local_path(args.base_model_path):
        checks["paths"]["base_model_path"] = local_path_report(args.base_model_path, "dir")
    else:
        warnings.append("base_model_path is not local; full generation requires --allow-downloads and appropriate model access.")


def build_check_report(args: argparse.Namespace) -> dict[str, Any]:
    errors = validate_args(args)
    warnings: list[str] = []
    checks: dict[str, Any] = {
        "arguments": normalized_plan(args),
        "errors": errors,
        "warnings": warnings,
        "implementation": {},
        "paths": {},
        "imports": {},
        "cuda": {},
    }

    implementation = configure_implementation_path(args.implementation_root)
    checks["implementation"] = implementation
    errors.extend(implementation["errors"])
    warnings.extend(implementation["warnings"])

    add_path_checks(args, errors, warnings, checks)

    ok, msg, mod_file = try_import("pipelines.pipeline_infu_flux")
    checks["imports"]["pipelines.pipeline_infu_flux"] = {"ok": ok, "message": msg, "file": mod_file}
    if not ok:
        errors.append(f"import failed: pipelines.pipeline_infu_flux ({msg})")
    ok, msg, mod_file = try_import("PIL.Image")
    checks["imports"]["PIL.Image"] = {"ok": ok, "message": msg, "file": mod_file}
    if not ok:
        errors.append(f"import failed: PIL.Image ({msg})")
    checks["cuda"] = check_cuda()
    if not checks["cuda"].get("cuda_available"):
        warnings.append("CUDA is not available; InfiniteYou generation cannot run without code changes even if import checks pass.")

    checks["ok"] = not errors
    return checks


def emit_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print("InfiniteYou-FLUX plan")
    print(json.dumps(report.get("arguments", report), indent=2, sort_keys=True))
    errors = report.get("errors", [])
    warnings = report.get("warnings", [])
    if errors:
        print("\nErrors:", file=sys.stderr)
        for item in errors:
            print(f"  - {item}", file=sys.stderr)
    if warnings:
        print("\nWarnings:")
        for item in warnings:
            print(f"  - {item}")
    if "ok" in report:
        print(f"\nPreflight status: {'OK' if report['ok'] else 'NOT OK'}")


def sanitize_prompt(prompt: str) -> str:
    prompt_name = prompt[:150] + "*" if len(prompt) > 150 else prompt
    prompt_name = prompt_name.replace("/", "|")
    prompt_name = re.sub(r"[\r\n\t]+", " ", prompt_name).strip()
    return prompt_name or "prompt"


def generation_blockers(args: argparse.Namespace) -> list[str]:
    blockers: list[str] = []
    if not args.id_image:
        blockers.append("--id-image is required for generation.")
    if not args.allow_downloads:
        if not looks_like_local_path(args.model_dir):
            blockers.append("--model-dir is not local; pass a local InfiniteYou model directory or explicitly set --allow-downloads.")
        else:
            paths = selected_model_paths(args)
            required = [
                (paths["infusenet_model"], "directory"),
                (paths["image_proj_model"], "file"),
                (paths["insightface_root"], "directory"),
            ]
            for path, kind in required:
                p = Path(path)
                if kind == "directory" and not p.is_dir():
                    blockers.append(f"required model directory is missing: {path}")
                if kind == "file" and not p.is_file():
                    blockers.append(f"required model file is missing: {path}")
        if not looks_like_local_path(args.base_model_path):
            blockers.append("--base-model-path is not local; pass a local FLUX directory or explicitly set --allow-downloads.")
        elif not Path(args.base_model_path).expanduser().is_dir():
            blockers.append(f"local FLUX base model directory is missing: {args.base_model_path}")
    if args.enable_realism_lora and looks_like_local_path(args.model_dir):
        p = Path(args.model_dir).expanduser() / "supports" / "optional_loras" / "flux_realism_lora.safetensors"
        if not p.is_file():
            blockers.append(f"Realism LoRA file is missing: {p}")
    if args.enable_anti_blur_lora and looks_like_local_path(args.model_dir):
        p = Path(args.model_dir).expanduser() / "supports" / "optional_loras" / "flux_anti_blur_lora.safetensors"
        if not p.is_file():
            blockers.append(f"Anti-blur LoRA file is missing: {p}")
    return blockers


def run_generation(args: argparse.Namespace) -> Path:
    implementation = configure_implementation_path(args.implementation_root)
    if implementation["errors"]:
        raise RuntimeError("; ".join(implementation["errors"]))

    blockers = generation_blockers(args)
    if blockers:
        raise RuntimeError("Pre-generation safety check failed: " + "; ".join(blockers))

    import torch
    from PIL import Image

    try:
        from pipelines.pipeline_infu_flux import InfUFluxPipeline
    except ImportError as exc:
        raise RuntimeError(
            "Could not import the bundled InfiniteYou runtime. Install dependencies from runtime/requirements.txt "
            "and rerun check-only diagnostics."
        ) from exc

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available. InfiniteYou generation requires CUDA; --cpu-offload is not CPU-only execution.")
    torch.cuda.set_device(args.cuda_device)

    infu_model_path = os.path.join(args.model_dir, f"infu_flux_{args.infu_flux_version}", args.model_version)
    insightface_root_path = os.path.join(args.model_dir, "supports", "insightface")

    pipe = InfUFluxPipeline(
        base_model_path=args.base_model_path,
        infu_model_path=infu_model_path,
        insightface_root_path=insightface_root_path,
        infu_flux_version=args.infu_flux_version,
        model_version=args.model_version,
        quantize_8bit=args.quantize_8bit,
        cpu_offload=args.cpu_offload,
    )

    lora_dir = os.path.join(args.model_dir, "supports", "optional_loras")
    if not os.path.exists(lora_dir):
        lora_dir = "./models/InfiniteYou/supports/optional_loras"
    loras = []
    if args.enable_realism_lora:
        loras.append([os.path.join(lora_dir, "flux_realism_lora.safetensors"), "realism", 1.0])
    if args.enable_anti_blur_lora:
        loras.append([os.path.join(lora_dir, "flux_anti_blur_lora.safetensors"), "anti_blur", 1.0])
    pipe.load_loras(loras)

    seed = args.seed
    if seed == 0:
        seed = torch.seed() & 0xFFFFFFFF

    id_image = Image.open(args.id_image).convert("RGB")
    control_image = Image.open(args.control_image).convert("RGB") if args.control_image else None
    image = pipe(
        id_image=id_image,
        prompt=args.prompt,
        control_image=control_image,
        width=args.width,
        height=args.height,
        seed=seed,
        guidance_scale=args.guidance_scale,
        num_steps=args.num_steps,
        infusenet_conditioning_scale=args.infusenet_conditioning_scale,
        infusenet_guidance_start=args.infusenet_guidance_start,
        infusenet_guidance_end=args.infusenet_guidance_end,
        cpu_offload=args.cpu_offload,
    )

    out_dir = Path(args.out_results_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    index = len([p for p in out_dir.iterdir() if p.is_file()])
    id_name = Path(args.id_image).stem
    out_name = f"{index:05d}_{id_name}_{sanitize_prompt(args.prompt)}_seed{seed}.png"
    out_path = out_dir / out_name
    image.save(out_path)
    return out_path


def main(argv: list[str] | None = None) -> int:
    configure_no_network_checks()
    args = parse_args(argv)
    errors = validate_args(args)
    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        return 2

    if args.dry_run:
        implementation = configure_implementation_path(args.implementation_root)
        report = {"arguments": normalized_plan(args), "implementation": implementation, "warnings": implementation["warnings"], "errors": implementation["errors"], "ok": not implementation["errors"]}
        emit_report(report, args.json)
        return 0 if report["ok"] else 1

    if args.check_only:
        report = build_check_report(args)
        emit_report(report, args.json)
        return 0 if report["ok"] else 1

    try:
        out_path = run_generation(args)
    except RuntimeError as exc:
        print(f"runtime error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        message = str(exc)
        if "No face detected" in message:
            print(f"face detection error: {message}. Use a clear, frontal-ish image with one large visible face.", file=sys.stderr)
        else:
            print(f"value error: {message}", file=sys.stderr)
        return 1
    except Exception as exc:  # broad user-facing wrapper
        text = str(exc)
        exc_name = type(exc).__name__
        if exc_name == "OutOfMemoryError" or "out of memory" in text.lower():
            print(
                "CUDA out of memory: retry with --cpu-offload, --quantize-8bit, fewer steps, smaller dimensions, or a freer/larger GPU. "
                f"Original error: {exc}",
                file=sys.stderr,
            )
        elif "FLUX.1-dev" in text or "huggingface" in text.lower() or "401" in text or "403" in text:
            print(
                "model access error: verify local model paths or accept/authenticate the gated FLUX.1-dev model before generation. "
                f"Original error: {exc}",
                file=sys.stderr,
            )
        elif "CUDA" in text or "cuda" in text:
            print(
                "CUDA/runtime error: verify torch CUDA availability, device index, VRAM, and the offload/quantization settings. "
                f"Original error: {exc}",
                file=sys.stderr,
            )
        else:
            print(f"generation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
