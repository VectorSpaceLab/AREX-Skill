#!/usr/bin/env python3
"""Plan an ExecuTorch LLM export/deployment command without downloading assets."""
from __future__ import annotations
import argparse, json


def main():
    ap = argparse.ArgumentParser(description="Plan ExecuTorch LLM export inputs and command shape.")
    ap.add_argument("--model", required=True, help="Model family or local model name, e.g. llama, gemma, whisper.")
    ap.add_argument("--backend", default="cpu", help="cpu, cuda, metal, vulkan, qnn, xnnpack, ios, android, etc.")
    ap.add_argument("--method", choices=["native", "optimum", "custom"], default="native")
    ap.add_argument("--quantization", default="none")
    ap.add_argument("--output-dir", default="llm-export-artifacts")
    args = ap.parse_args()
    assets = ["local weights/checkpoint", "tokenizer files", "model config", "representative prompt"]
    if args.method == "optimum":
        command = ["optimum-cli", "export", "executorch", "--model", "<local-or-hf-model>", "--task", "text-generation", "--output_dir", args.output_dir]
    elif args.method == "native":
        command = ["python", "<native-executorch-llm-export-entry>", "--checkpoint", "<checkpoint>", "--tokenizer", "<tokenizer>", "--backend", args.backend, "--output-dir", args.output_dir]
    else:
        command = ["python", "<custom-wrapper-export>.py", "--model-config", "<config>", "--backend", args.backend, "--output-dir", args.output_dir]
    print(json.dumps({"method": args.method, "model": args.model, "backend": args.backend, "quantization": args.quantization, "required_assets": assets, "command_template": command, "notes": ["This is a plan only; do not download weights or build runners without approval.", "Route qnn backend execution to the qualcomm sub-skill."]}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

