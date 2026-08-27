#!/usr/bin/env python3
"""Build a DALLE-pytorch generation command template."""
import argparse, json, shlex


def main():
    p = argparse.ArgumentParser(description="Build a command matching the DALLE-pytorch generation helper surface.")
    p.add_argument("--dalle-path", required=True)
    p.add_argument("--text", required=True, help="Prompt text; use | to separate multiple prompts for the historical helper.")
    p.add_argument("--num-images", type=int, default=128)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--top-k", type=float, default=0.9)
    p.add_argument("--outputs-dir", default="./outputs")
    p.add_argument("--bpe-path")
    p.add_argument("--hug", action="store_true")
    p.add_argument("--chinese", action="store_true")
    p.add_argument("--taming", action="store_true")
    p.add_argument("--vqgan-model-path")
    p.add_argument("--vqgan-config-path")
    p.add_argument("--gentxt", action="store_true")
    p.add_argument("--as-json", action="store_true")
    args = p.parse_args()

    cmd = ["python", "generate.py", "--dalle_path", args.dalle_path, "--text", args.text,
           "--num_images", str(args.num_images), "--batch_size", str(args.batch_size),
           "--top_k", str(args.top_k), "--outputs_dir", args.outputs_dir]
    for flag, value in [("--bpe_path", args.bpe_path), ("--vqgan_model_path", args.vqgan_model_path), ("--vqgan_config_path", args.vqgan_config_path)]:
        if value:
            cmd.extend([flag, value])
    for flag, enabled in [("--hug", args.hug), ("--chinese", args.chinese), ("--taming", args.taming), ("--gentxt", args.gentxt)]:
        if enabled:
            cmd.append(flag)
    warnings = [
        "The historical helper calls CUDA and writes output files.",
        "Tokenizer/VAE flags must match the checkpoint's training configuration.",
        "Pipe characters split multiple prompts in the helper surface.",
    ]
    payload = {"command": cmd, "shell": " ".join(shlex.quote(x) for x in cmd), "warnings": warnings}
    if args.as_json:
        print(json.dumps(payload, indent=2))
    else:
        print(payload["shell"])
        for warning in warnings:
            print(f"# WARNING: {warning}")


if __name__ == "__main__":
    main()
