#!/usr/bin/env python3
"""Build Tacotron eval or demo-server commands without loading a checkpoint."""
import argparse
import os
import shlex
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout-root", default=".",
                        help="Tacotron checkout whose cwd will run eval.py/demo_server.py")
    parser.add_argument("--mode", choices=("eval", "server"), required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--hparams", default="")
    args = parser.parse_args()
    if not args.checkpoint.strip():
        parser.error("--checkpoint cannot be empty")
    if args.port < 1 or args.port > 65535:
        parser.error("--port must be between 1 and 65535")
    if args.hparams:
        for item in args.hparams.split(","):
            if "=" not in item or not item.split("=", 1)[0].strip():
                parser.error("hparams must use comma-separated name=value pairs")
    program = "eval.py" if args.mode == "eval" else "demo_server.py"
    checkpoint = os.path.abspath(os.path.expanduser(args.checkpoint))
    command = ["python", program, "--checkpoint", checkpoint]
    if args.mode == "server":
        command += ["--port", str(args.port)]
    if args.hparams:
        command += ["--hparams", args.hparams]
    rendered = " ".join(shlex.quote(x) for x in command)
    checkout_root = os.path.abspath(os.path.expanduser(args.checkout_root))
    print("cd %s && %s" % (shlex.quote(checkout_root), rendered))
    print("dry-run: checkpoint not loaded; server not started")
    return 0


if __name__ == "__main__":
    sys.exit(main())
