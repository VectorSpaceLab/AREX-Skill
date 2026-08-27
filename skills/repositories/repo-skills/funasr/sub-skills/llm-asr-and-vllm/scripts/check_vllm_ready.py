#!/usr/bin/env python3
"""Lightweight FunASR LLM-ASR/vLLM readiness diagnostic.

This helper reports model-family applicability, optional package availability,
dtype/device caveats, and Qwen3-ASR dependency compatibility. It intentionally
never downloads model weights, loads checkpoints, initializes vLLM, or allocates
a live ASR model.

Examples:
    python check_vllm_ready.py --model-family Fun-ASR-Nano --device cuda:0 --dtype bf16
    python check_vllm_ready.py --model-family Paraformer --target auto-model-vllm
    python check_vllm_ready.py --model-family Qwen3-ASR --target qwen3-native --check-qwen3
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.util
import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import Any, Optional


SUPPORTED_AUTOMODEL_VLLM = {"FunASRNano", "LLMASR", "LLMASRNAR", "GLMASR", "QwenAudioWarp"}
NON_AUTOMODEL_VLLM = {
    "Paraformer": "Non-autoregressive model using a CIF predictor; use standard FunASR AutoModel.",
    "SenseVoice": "Whisper-like encoder-decoder; use standard FunASR AutoModel.",
    "CTTransformer": "Small punctuation model; vLLM does not help.",
    "Conformer": "CTC/attention encoder-decoder; no autoregressive LLM decoder to accelerate.",
    "Qwen3ASR": "Qwen3-ASR uses the external qwen-asr package with its own optimized inference path.",
}


@dataclass
class Check:
    level: str
    code: str
    message: str
    next_step: Optional[str] = None


def add(checks: list[Check], level: str, code: str, message: str, next_step: str | None = None) -> None:
    checks.append(Check(level=level, code=code, message=message, next_step=next_step))


def package_version(dist_name: str) -> str | None:
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None
    except Exception:
        return None


def package_requires(dist_name: str) -> list[str]:
    try:
        return list(metadata.requires(dist_name) or [])
    except Exception:
        return []


def module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return False


def normalize_family(raw: str | None) -> tuple[str, str]:
    value = (raw or "unknown").strip()
    key = re.sub(r"[\s_]+", "-", value.lower())

    if key in {"funasrnano", "funasr-nano", "fun-asr-nano", "nano", "fun-asr-nano-2512"}:
        return "FunASRNano", value
    if "fun-asr-mlt-nano" in key or "fun-asr-nano" in key or "funaudiollm/fun-asr" in key:
        return "FunASRNano", value
    if key in {"glmasr", "glm-asr", "glm-asr-nano", "glm-asr-nano-2512"}:
        return "GLMASR", value
    if "glm-asr" in key or "zai-org/glm" in key or "zhipuai/glm" in key:
        return "GLMASR", value
    if key in {"qwen3asr", "qwen3-asr", "qwen-asr", "qwen3"}:
        return "Qwen3ASR", value
    if "qwen/qwen3-asr" in key or "qwen3-asr" in key:
        return "Qwen3ASR", value
    if "sensevoice" in key:
        return "SenseVoice", value
    if "paraformer" in key:
        return "Paraformer", value
    if "ct-transformer" in key or "cttransformer" in key:
        return "CTTransformer", value
    if "conformer" in key:
        return "Conformer", value
    if "llmasrnar" in key or "llm-asr-nar" in key:
        return "LLMASRNAR", value
    if "llmasr" in key or "llm-asr" in key:
        return "LLMASR", value
    if value in SUPPORTED_AUTOMODEL_VLLM or value in NON_AUTOMODEL_VLLM:
        return value, value
    return value, value


def is_automodel_vllm_target(target: str) -> bool:
    return target in {"auto", "auto-model-vllm", "direct-nano-vllm", "direct-glm-vllm"}


def strict_level(args: argparse.Namespace, default: str = "WARN") -> str:
    return "FAIL" if args.strict else default


def qwen_install_command(qwen_version: str | None = "0.0.6", transformer_spec: str | None = "==4.57.6", *, vllm_extra: bool = False) -> str:
    qwen_part = "qwen-asr"
    if vllm_extra:
        qwen_part += "[vllm]"
    if qwen_version:
        qwen_part += f"=={qwen_version}"
    if transformer_spec:
        transformer_part = f"transformers{transformer_spec}"
        return f'pip install -U "{qwen_part}" "{transformer_part}" accelerate'
    return f'pip install -U "{qwen_part}" transformers accelerate'


def check_funasr_applicability(family: str, checks: list[Check]) -> bool | None:
    """Return applicability if FunASR's own checker can be imported."""
    if not module_available("funasr"):
        add(
            checks,
            "WARN",
            "funasr-missing",
            "The 'funasr' module is not importable in this Python environment.",
            "Install FunASR before attempting standard AutoModel or AutoModelVLLM runtime checks.",
        )
        return None

    try:
        from funasr.auto.auto_model_vllm import check_vllm_applicable
    except Exception as exc:  # keep the helper diagnostic-friendly
        add(
            checks,
            "WARN",
            "funasr-vllm-helper-import",
            f"FunASR is importable, but its AutoModelVLLM applicability helper could not be imported: {exc}",
            "Use the local fallback map below, then fix FunASR optional import errors before a real vLLM run.",
        )
        return None

    try:
        applicable = bool(check_vllm_applicable(family))
    except ValueError as exc:
        add(checks, "FAIL", "model-family", str(exc), "Use standard FunASR AutoModel or the model-family-specific runtime named in the message.")
        return False
    except Exception as exc:
        add(checks, "WARN", "model-family-check", f"FunASR applicability check failed unexpectedly: {exc}")
        return None

    if applicable:
        add(checks, "PASS", "model-family", f"'{family}' is applicable to FunASR AutoModelVLLM.")
        return True

    add(
        checks,
        "WARN",
        "model-family-unknown",
        f"FunASR did not mark '{family}' as a supported AutoModelVLLM family.",
        "Inspect the model config. If it is not an autoregressive LLM-decoder ASR model, use standard AutoModel.",
    )
    return False


def check_qwen3_dependencies(args: argparse.Namespace, checks: list[Check]) -> dict[str, Any]:
    qwen_version = package_version("qwen-asr")
    transformers_version = package_version("transformers")
    accelerate_version = package_version("accelerate")
    vllm_version = package_version("vllm")
    info = {
        "qwen_asr": qwen_version,
        "transformers": transformers_version,
        "accelerate": accelerate_version,
        "vllm": vllm_version,
    }

    remediation = qwen_install_command(vllm_extra=args.target == "qwen3-native-vllm")
    if not qwen_version:
        add(
            checks,
            strict_level(args),
            "qwen3-qwen-asr-missing",
            "Qwen3-ASR requires the external 'qwen-asr' package; it is not installed.",
            remediation,
        )
        return info

    if not transformers_version:
        add(
            checks,
            strict_level(args),
            "qwen3-transformers-missing",
            f"qwen-asr=={qwen_version} is installed, but transformers is missing.",
            qwen_install_command(qwen_version=qwen_version, transformer_spec=None, vllm_extra=args.target == "qwen3-native-vllm"),
        )
        return info

    requirements = package_requires("qwen-asr")
    transformers_spec = None
    try:
        from packaging.requirements import InvalidRequirement, Requirement
        from packaging.version import InvalidVersion, Version
    except Exception:
        add(
            checks,
            "WARN",
            "qwen3-packaging-missing",
            "The 'packaging' module is unavailable, so the transformers requirement declared by qwen-asr could not be parsed.",
            "Install packaging or manually verify qwen-asr's transformers requirement before loading Qwen3-ASR.",
        )
        return info

    for requirement_text in requirements:
        try:
            requirement = Requirement(requirement_text)
        except InvalidRequirement:
            continue
        if requirement.name.lower() == "transformers":
            transformers_spec = str(requirement.specifier) or None
            break

    if transformers_spec:
        try:
            Version(transformers_version)
            compatible = transformers_version in Requirement(f"transformers{transformers_spec}").specifier
        except InvalidVersion:
            compatible = True
            add(
                checks,
                "WARN",
                "qwen3-transformers-custom-version",
                f"transformers version '{transformers_version}' is not PEP 440; treating it as a custom build and not failing the check.",
                "Run a tiny Qwen3 import/runtime smoke before relying on this custom transformers build.",
            )

        if compatible:
            add(
                checks,
                "PASS",
                "qwen3-transformers",
                f"qwen-asr=={qwen_version} declares transformers{transformers_spec}, and transformers=={transformers_version} satisfies it.",
            )
        else:
            command = qwen_install_command(
                qwen_version=qwen_version,
                transformer_spec=transformers_spec,
                vllm_extra=args.target == "qwen3-native-vllm",
            )
            add(
                checks,
                "FAIL",
                "qwen3-transformers-mismatch",
                (
                    f"Qwen3-ASR dependency mismatch: qwen-asr=={qwen_version} requires "
                    f"transformers{transformers_spec}, but the active environment has "
                    f"transformers=={transformers_version}. This can trigger qwen_asr errors "
                    "such as `AttributeError: 'Qwen3ASRConfig' object has no attribute 'thinker_config'`."
                ),
                f"Run: {command}",
            )
    else:
        add(
            checks,
            "INFO",
            "qwen3-transformers-spec",
            f"qwen-asr=={qwen_version} is installed, but no explicit transformers requirement was found in package metadata.",
            "Use qwen-asr's documentation or a small import smoke to verify compatibility.",
        )

    if args.target == "qwen3-native-vllm":
        if not vllm_version:
            add(
                checks,
                strict_level(args),
                "qwen3-native-vllm-missing",
                "Qwen3 native vLLM/streaming was requested, but vLLM is not installed.",
                qwen_install_command(qwen_version=qwen_version, transformer_spec=transformers_spec or "==4.57.6", vllm_extra=True),
            )
        elif not vllm_version.startswith("0.14"):
            add(
                checks,
                "WARN",
                "qwen3-native-vllm-version",
                f"vllm=={vllm_version} is installed; Qwen3 native vLLM guidance expects the version pinned by qwen-asr[vllm] (documented around vLLM 0.14.x).",
                qwen_install_command(qwen_version=qwen_version, transformer_spec=transformers_spec or "==4.57.6", vllm_extra=True),
            )

    return info


def inspect_torch(checks: list[Check], device: str, need_vllm_runtime: bool, args: argparse.Namespace) -> dict[str, Any]:
    info: dict[str, Any] = {"available": False}
    if not module_available("torch"):
        add(checks, strict_level(args), "torch-missing", "torch is not importable.", "Install a FunASR-compatible torch build before loading ASR models.")
        return info

    try:
        torch = importlib.import_module("torch")
        info["available"] = True
        info["version"] = getattr(torch, "__version__", None)
        cuda = getattr(torch, "cuda", None)
        if cuda is not None:
            try:
                info["cuda_available"] = bool(cuda.is_available())
                info["cuda_version"] = getattr(torch.version, "cuda", None)
                info["cuda_device_count"] = int(cuda.device_count()) if info["cuda_available"] else 0
                if info["cuda_available"] and info["cuda_device_count"]:
                    info["cuda_device_0"] = cuda.get_device_name(0)
            except Exception as exc:
                info["cuda_error"] = str(exc)
    except Exception as exc:
        add(checks, strict_level(args), "torch-import", f"torch import failed: {exc}")
        return info

    device_type = (device or "").split(":", 1)[0].lower()
    if device_type == "cuda":
        if info.get("cuda_available"):
            add(checks, "PASS", "torch-cuda", f"torch CUDA is available ({info.get('cuda_device_count', 0)} device(s); torch CUDA build {info.get('cuda_version')}).")
        else:
            add(
                checks,
                strict_level(args),
                "torch-cuda-unavailable",
                "A CUDA device was requested, but torch.cuda.is_available() is false.",
                "Use a CUDA-capable torch/vLLM environment or choose standard CPU AutoModel instead of vLLM acceleration.",
            )
    elif device_type == "npu":
        add(
            checks,
            "WARN",
            "npu-caveat",
            "NPU/Ascend was requested. PyTorch AutoModel compatibility and AutoModelVLLM/vLLM-Ascend operator support must be validated separately.",
            "Capture torch, torch_npu, CANN, vLLM-Ascend, NPU model, dtype, and full operator stack traces before claiming support.",
        )
    elif need_vllm_runtime:
        add(
            checks,
            "WARN",
            "device-not-cuda",
            f"Device '{device}' was requested for a vLLM-oriented path. FunASR Nano/GLM vLLM acceleration is CUDA-oriented in the documented path.",
            "Use a CUDA device for throughput, or fall back to standard AutoModel for CPU-oriented work.",
        )
    return info


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    checks: list[Check] = []
    family, raw_family = normalize_family(args.model_family)
    target = args.target
    if target == "auto":
        if family == "Qwen3ASR":
            target = "qwen3-native"
        elif family in NON_AUTOMODEL_VLLM and family != "Qwen3ASR":
            target = "auto-model"
        elif family in SUPPORTED_AUTOMODEL_VLLM:
            target = "auto-model-vllm"

    funasr_version = package_version("funasr")
    vllm_version = package_version("vllm")
    env_info: dict[str, Any] = {
        "python": sys.version.split()[0],
        "funasr": funasr_version,
        "vllm": vllm_version,
    }

    if funasr_version:
        add(checks, "PASS", "funasr", f"funasr distribution is installed (version {funasr_version}).")
    elif module_available("funasr"):
        add(checks, "PASS", "funasr", "funasr module is importable, but distribution metadata version was not found.")
    else:
        add(checks, strict_level(args), "funasr", "funasr is not importable.", "Install FunASR before using this runtime guidance.")

    need_vllm_runtime = target in {"auto-model-vllm", "direct-nano-vllm", "direct-glm-vllm", "qwen3-native-vllm"}

    if family in NON_AUTOMODEL_VLLM:
        reason = NON_AUTOMODEL_VLLM[family]
        if target in {"auto-model-vllm", "direct-nano-vllm", "direct-glm-vllm"}:
            add(
                checks,
                "FAIL",
                "model-family",
                f"{family} should not be routed to FunASR AutoModelVLLM: {reason}",
                "Use standard FunASR AutoModel, or Qwen3's external qwen_asr runtime when the family is Qwen3-ASR.",
            )
        elif family == "Qwen3ASR":
            add(
                checks,
                "INFO",
                "model-family",
                "Qwen3-ASR is LLM-based but belongs to the external qwen-asr runtime, not FunASR AutoModelVLLM.",
                "Use FunASR AutoModel for the wrapper, or qwen_asr.Qwen3ASRModel for native Qwen3 runtime.",
            )
        else:
            add(checks, "INFO", "model-family", f"{family} is not a vLLM family: {reason}")
    elif is_automodel_vllm_target(target):
        app = check_funasr_applicability(family, checks)
        if app is None:
            if family in SUPPORTED_AUTOMODEL_VLLM:
                add(checks, "PASS", "model-family-fallback", f"Fallback map marks '{family}' as an AutoModelVLLM-capable LLM-ASR family.")
            else:
                add(checks, strict_level(args), "model-family-fallback", f"Fallback map does not know '{family}' as an AutoModelVLLM family.")
    else:
        add(checks, "INFO", "target", f"Target '{target}' does not require FunASR AutoModelVLLM readiness.")

    if need_vllm_runtime and family != "Qwen3ASR":
        if vllm_version:
            add(checks, "PASS", "vllm", f"vllm distribution is installed (version {vllm_version}).")
        else:
            add(
                checks,
                strict_level(args),
                "vllm-missing",
                "vLLM is not installed. FunASR can still import, but Nano/GLM AutoModelVLLM runtime initialization will fail.",
                "Install a vLLM build compatible with the NVIDIA driver CUDA version, letting vLLM own the torch/torchaudio/torchvision wheel set.",
            )
    elif family == "Qwen3ASR" and target not in {"qwen3-native", "qwen3-native-vllm", "auto-model"}:
        add(
            checks,
            "FAIL",
            "qwen3-wrong-backend",
            "Qwen3-ASR was paired with a FunASR AutoModelVLLM-style target, which is unsupported.",
            "Use target 'qwen3-native' or 'qwen3-native-vllm' instead.",
        )

    if args.dtype == "fp16" and family in {"FunASRNano", "GLMASR"}:
        add(
            checks,
            "WARN",
            "dtype-fp16",
            f"{family} can produce degraded or garbage transcription with fp16 in the audio-embedding path.",
            "Prefer dtype='bf16'. Use dtype='fp32' on GPUs without bfloat16 support.",
        )
    elif args.dtype in {"bf16", "fp32"} and family in {"FunASRNano", "GLMASR", "Qwen3ASR"}:
        add(checks, "PASS", "dtype", f"dtype='{args.dtype}' is the safer documented choice for {family}.")

    torch_info = inspect_torch(checks, args.device, need_vllm_runtime, args)
    env_info["torch"] = torch_info

    qwen_info = None
    if family == "Qwen3ASR" or args.check_qwen3:
        qwen_info = check_qwen3_dependencies(args, checks)
        env_info["qwen3"] = qwen_info

    if family == "FunASRNano":
        add(
            checks,
            "INFO",
            "nano-ctc",
            "Nano text transcription can work without timestamps; timestamps require complete CTC weights in the checkpoint.",
        )
    if family == "GLMASR":
        add(
            checks,
            "INFO",
            "glm-long-audio",
            "GLM-ASR vLLM should be used on short/fixed segments; do not assume long-audio dynamic VAD support.",
        )

    overall = "fail" if any(c.level == "FAIL" for c in checks) else "warn" if any(c.level == "WARN" for c in checks) else "pass"
    return {
        "schema": "funasr.llm_vllm_readiness.v1",
        "input": {
            "model_family": raw_family,
            "normalized_family": family,
            "requested_target": args.target,
            "resolved_target": target,
            "device": args.device,
            "dtype": args.dtype,
            "strict": args.strict,
        },
        "overall": overall,
        "environment": env_info,
        "checks": [asdict(c) for c in checks],
    }


def print_text(report: dict[str, Any]) -> None:
    inp = report["input"]
    print("FunASR LLM-ASR / vLLM readiness")
    print("=" * 38)
    print(f"model family: {inp['model_family']} -> {inp['normalized_family']}")
    print(f"target: {inp['requested_target']} -> {inp['resolved_target']}")
    print(f"device: {inp['device']}    dtype: {inp['dtype']}")
    print(f"overall: {report['overall'].upper()}")
    print()
    for check in report["checks"]:
        print(f"{check['level']:>4} {check['code']}: {check['message']}")
        if check.get("next_step"):
            print(f"     next: {check['next_step']}")
    print()
    print("Environment summary:")
    env = report["environment"]
    print(f"  python: {env.get('python')}")
    print(f"  funasr: {env.get('funasr') or 'not installed'}")
    print(f"  vllm: {env.get('vllm') or 'not installed'}")
    torch_info = env.get("torch") or {}
    if torch_info.get("available"):
        print(f"  torch: {torch_info.get('version')}  cuda_available={torch_info.get('cuda_available')}  cuda_build={torch_info.get('cuda_version')}")
        if torch_info.get("cuda_device_0"):
            print(f"  cuda_device_0: {torch_info.get('cuda_device_0')}")
    else:
        print("  torch: not importable")
    if "qwen3" in env:
        q = env["qwen3"]
        print(f"  qwen-asr: {q.get('qwen_asr') or 'not installed'}")
        print(f"  transformers: {q.get('transformers') or 'not installed'}")
        print(f"  accelerate: {q.get('accelerate') or 'not installed'}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check FunASR LLM-ASR/vLLM routing readiness without loading a model.")
    parser.add_argument("--model-family", required=True, help="Model family, config class, or model id (for example Fun-ASR-Nano, GLM-ASR-Nano, Qwen3-ASR, Paraformer).")
    parser.add_argument(
        "--target",
        default="auto",
        choices=["auto", "auto-model", "auto-model-vllm", "direct-nano-vllm", "direct-glm-vllm", "qwen3-native", "qwen3-native-vllm"],
        help="Runtime route to validate. 'auto' resolves from the model family.",
    )
    parser.add_argument("--device", default="cuda:0", help="Requested runtime device, such as cuda:0, cpu, or npu:0.")
    parser.add_argument("--dtype", default="bf16", choices=["bf16", "fp16", "fp32", "auto"], help="Requested compute dtype.")
    parser.add_argument("--check-qwen3", action="store_true", help="Also inspect qwen-asr/transformers compatibility even when the family is not Qwen3-ASR.")
    parser.add_argument("--strict", action="store_true", help="Treat missing runtime dependencies/backend checks as failures and return a non-zero exit code.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report = build_report(args)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 1 if report["overall"] == "fail" and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
