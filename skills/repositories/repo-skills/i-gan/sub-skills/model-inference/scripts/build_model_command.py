#!/usr/bin/env python3
"""Build a dry-run command for iGAN DCGAN sample generation.

This helper adapts the repository's standalone sample workflow without importing
Theano, OpenCV, or repo-local modules. It prints the command/environment plan a
user could run later in a compatible legacy iGAN checkout.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from typing import Dict, List, Optional

MODEL_ZOO: Dict[str, Dict[str, object]] = {
    "outdoor_64": {"npx": 64, "n_layers": 3, "n_f": 128, "nc": 3, "note": "RGB landscape model"},
    "church_64": {"npx": 64, "n_layers": 3, "n_f": 128, "nc": 3, "note": "RGB LSUN church model"},
    "handbag_64": {"npx": 64, "n_layers": 3, "n_f": 128, "nc": 3, "note": "RGB handbag model"},
    "shoes_64": {"npx": 64, "n_layers": 3, "n_f": 128, "nc": 3, "note": "RGB shoes model"},
    "hed_shoes_64": {"npx": 64, "n_layers": 3, "n_f": 128, "nc": 1, "note": "one-channel HED shoe sketch model"},
}

DEFAULT_THEANO_FLAGS = "device={device},floatX=float32,nvcc.fastmath=True"


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build, but do not run, an iGAN generate_samples.py command.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model_name", default="outdoor_64", help="iGAN model-zoo/config name.")
    parser.add_argument("--model_type", default="dcgan_theano", help="Model implementation suffix.")
    parser.add_argument("--framework", default="theano", help="Framework argument preserved for generate_samples.py.")
    parser.add_argument("--model_file", default=None, help="Explicit model artifact path.")
    parser.add_argument("--output_image", default=None, help="Output image path for the sample grid.")
    parser.add_argument("--python", default="python", help="Python executable to place in the generated command.")
    parser.add_argument("--sample-script", default="generate_samples.py", help="Sample script path to place in the command.")
    parser.add_argument("--device", default="gpu0", help="Theano device name for default THEANO_FLAGS.")
    parser.add_argument("--theano-flags", default=None, help="Explicit THEANO_FLAGS value; overrides --device.")
    parser.add_argument("--no-theano-flags", action="store_true", help="Do not include THEANO_FLAGS in the command plan.")
    parser.add_argument("--check-model", action="store_true", help="Report whether the planned model file exists locally.")
    parser.add_argument("--allow-unknown", action="store_true", help="Allow model names/types outside the bundled iGAN model zoo.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    return parser.parse_args(argv)


def shell_join(argv: List[str]) -> str:
    return " ".join(shlex.quote(part) for part in argv)


def build_plan(args: argparse.Namespace) -> Dict[str, object]:
    known_model = args.model_name in MODEL_ZOO
    if not known_model and not args.allow_unknown:
        raise SystemExit(
            "Unknown model_name {!r}. Use one of {} or pass --allow-unknown for a custom model.".format(
                args.model_name, ", ".join(sorted(MODEL_ZOO))
            )
        )
    if args.model_type != "dcgan_theano" and not args.allow_unknown:
        raise SystemExit("This helper knows iGAN's dcgan_theano workflow; pass --allow-unknown for a custom model_type.")

    model_file = args.model_file or "./models/{}.{}".format(args.model_name, args.model_type)
    output_image = args.output_image or "{}_{}_samples.png".format(args.model_name, args.model_type)

    command_argv = [
        args.python,
        args.sample_script,
        "--model_name",
        args.model_name,
        "--model_type",
        args.model_type,
        "--framework",
        args.framework,
        "--model_file",
        model_file,
        "--output_image",
        output_image,
    ]

    env: Dict[str, str] = {}
    if not args.no_theano_flags:
        env["THEANO_FLAGS"] = args.theano_flags or DEFAULT_THEANO_FLAGS.format(device=args.device)

    shell_command = shell_join(command_argv)
    if env:
        env_prefix = " ".join("{}={}".format(k, shlex.quote(v)) for k, v in sorted(env.items()))
        shell_command = env_prefix + " " + shell_command

    model_status: Dict[str, object] = {"checked": bool(args.check_model), "path": model_file}
    if args.check_model:
        exists = os.path.isfile(model_file)
        model_status.update({"exists": exists, "status": "present" if exists else "missing"})

    return {
        "workflow": "generate_samples.py dry command plan",
        "model_name": args.model_name,
        "known_model": known_model,
        "model_type": args.model_type,
        "framework": args.framework,
        "model_file": model_file,
        "output_image": output_image,
        "model_config": MODEL_ZOO.get(args.model_name),
        "generation_defaults": {"n": 196, "batch_size": 49, "grid": [14, 14], "latent_dim": 100},
        "env": env,
        "argv": command_argv,
        "shell_command": shell_command,
        "model_status": model_status,
        "side_effects": "none; this helper does not import Theano, use a GPU, download files, or write images",
    }


def emit_text(plan: Dict[str, object]) -> None:
    print("iGAN sample-generation dry run")
    print("model_name: {}{}".format(plan["model_name"], " (known)" if plan["known_model"] else " (custom/unknown)"))
    print("model_type: {}".format(plan["model_type"]))
    config = plan.get("model_config")
    if config:
        print("model_config: npx={npx}, n_layers={n_layers}, n_f={n_f}, nc={nc} ({note})".format(**config))
    print("model_file: {}".format(plan["model_file"]))
    status = plan["model_status"]
    if status.get("checked"):
        print("model_status: {}".format(status["status"]))
    else:
        print("model_status: not checked (use --check-model to test local presence)")
    print("output_image: {}".format(plan["output_image"]))
    print("generation_defaults: n=196, batch_size=49, grid=14x14, latent_dim=100")
    if plan["env"]:
        for key, value in sorted(plan["env"].items()):
            print("env: {}={}".format(key, value))
    else:
        print("env: THEANO_FLAGS omitted by request")
    print("argv: {}".format(json.dumps(plan["argv"])))
    print("shell_command: {}".format(plan["shell_command"]))
    print("side_effects: {}".format(plan["side_effects"]))


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    plan = build_plan(args)
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        emit_text(plan)
    return 0


if __name__ == "__main__":
    sys.exit(main())
