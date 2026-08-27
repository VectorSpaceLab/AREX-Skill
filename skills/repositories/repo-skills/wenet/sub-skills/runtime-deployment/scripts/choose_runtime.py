#!/usr/bin/env python3
"""Choose a WeNet runtime target and list expected artifacts/prerequisites."""

from __future__ import annotations

import argparse
import json

RUNTIMES = {
    ("linux", "libtorch"): {
        "artifacts": ["JIT final.zip or final_quant.zip", "units.txt", "tokenizer resources", "optional global_cmvn"],
        "prerequisites": ["CMake", "C++ compiler", "compatible libtorch"],
        "next": "Export JIT with model-export before building libtorch runtime.",
    },
    ("linux", "onnxruntime"): {
        "artifacts": ["encoder.onnx", "ctc.onnx", "decoder.onnx", "units.txt", "tokenizer/CMVN resources"],
        "prerequisites": ["CMake", "ONNX Runtime SDK/provider", "matching export chunk settings"],
        "next": "Export ONNX CPU/GPU with model-export and keep runtime chunk settings aligned.",
    },
    ("linux", "openvino"): {
        "artifacts": ["OpenVINO-compatible exported model", "units/tokenizer resources"],
        "prerequisites": ["OpenVINO toolkit", "CMake", "supported model ops"],
        "next": "Verify OpenVINO conversion support for the trained model family.",
    },
    ("linux", "tensorrt"): {
        "artifacts": ["ONNX/TensorRT-ready artifacts", "model repository/config", "units/tokenizer resources"],
        "prerequisites": ["NVIDIA GPU", "driver", "CUDA", "TensorRT/Triton", "authorized service ports"],
        "next": "Verify CUDA/TensorRT stack, then build a tiny server smoke before benchmarking.",
    },
    ("android", "libtorch"): {
        "artifacts": ["mobile-compatible JIT model", "units/tokenizer resources"],
        "prerequisites": ["Android Gradle toolchain", "mobile libtorch/AARs", "target ABI"],
        "next": "Build the Android app only after model resources are bundled for the target ABI.",
    },
    ("ios", "libtorch"): {
        "artifacts": ["mobile-compatible JIT model", "units/tokenizer resources"],
        "prerequisites": ["Xcode", "CocoaPods or equivalent", "iOS-compatible runtime libs"],
        "next": "Validate a tiny local audio sample on device/simulator before optimization.",
    },
    ("web", "libtorch"): {
        "artifacts": ["JIT/runtime model files", "web app model bundle"],
        "prerequisites": ["Python web dependencies", "runtime binding", "authorized local port"],
        "next": "Use a local demo only after package/runtime dependencies and model bundle are available.",
    },
    ("raspberrypi", "onnxruntime"): {
        "artifacts": ["ONNX files", "units/tokenizer resources"],
        "prerequisites": ["ARM-compatible ONNX Runtime", "compiler/toolchain", "memory budget"],
        "next": "Prefer CPU ONNX export and test one short audio before service packaging.",
    },
    ("linux", "ipex"): {
        "artifacts": ["IPEX-compatible exported model", "units/tokenizer resources"],
        "prerequisites": ["Intel Extension for PyTorch", "compatible Intel runtime"],
        "next": "Run model-export preflight for IPEX and verify the Intel stack.",
    },
    ("linux", "bpu"): {
        "artifacts": ["Horizon BPU converted binary", "metadata", "units/tokenizer resources"],
        "prerequisites": ["Horizon SDK/toolchain", "target BPU hardware"],
        "next": "Use BPU export/conversion only in a Horizon-supported environment.",
    },
    ("linux", "xpu"): {
        "artifacts": ["Kunlun XPU-compatible model/runtime files", "units/tokenizer resources"],
        "prerequisites": ["Kunlun SDK/toolchain", "target XPU hardware"],
        "next": "Validate on target XPU hardware; CPU checks do not prove XPU runtime.",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Map WeNet deployment target to artifacts and prerequisites.")
    parser.add_argument("--platform", required=True, choices=sorted({p for p, _ in RUNTIMES}), help="Target platform.")
    parser.add_argument("--backend", required=True, choices=sorted({b for _, b in RUNTIMES}), help="Inference backend/engine.")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format.")
    args = parser.parse_args()

    key = (args.platform, args.backend)
    if key not in RUNTIMES:
        available = [f"{p}/{b}" for p, b in sorted(RUNTIMES)]
        result = {"ok": False, "message": "unsupported platform/backend pair", "available": available}
        print(json.dumps(result, sort_keys=True))
        return 1

    result = {"ok": True, "platform": args.platform, "backend": args.backend, **RUNTIMES[key]}
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"# WeNet runtime: {args.platform}/{args.backend}\n")
        print("## Artifacts")
        for item in result["artifacts"]:
            print(f"- {item}")
        print("\n## Prerequisites")
        for item in result["prerequisites"]:
            print(f"- {item}")
        print(f"\n## Next step\n{result['next']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
