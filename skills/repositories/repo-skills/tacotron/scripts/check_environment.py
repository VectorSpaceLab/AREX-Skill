#!/usr/bin/env python3
"""Check the legacy Tacotron runtime without downloading data or checkpoints.

Run from any directory. ``--repo-root`` must point to a Tacotron source
checkout; the helper changes into that checkout before importing source modules.
It never starts preprocessing, training, synthesis, or a server.
"""
import argparse
import importlib
import os
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Tacotron checkout to inspect")
    args = parser.parse_args()
    root = os.path.abspath(args.repo_root)
    required = ("hparams.py", "text", "datasets", "models", "util", "synthesizer.py")
    if not os.path.isdir(root):
        parser.error("--repo-root is not a directory: %s" % root)
    missing = [name for name in required
               if not os.path.exists(os.path.join(root, name))]
    if missing:
        parser.error("--repo-root is not a Tacotron checkout; missing: %s" %
                     ", ".join(missing))
    os.chdir(root)
    sys.path.insert(0, root)
    names = ["tensorflow", "librosa", "text", "datasets", "models", "util", "synthesizer"]
    failed = []
    print("checkout cwd:", root)
    for name in names:
        try:
            module = importlib.import_module(name)
            print("OK %-12s %s" % (name, getattr(module, "__version__", "imported")))
        except Exception as exc:  # diagnostic helper: show each failure and continue
            failed.append((name, exc))
            print("FAIL %-10s %s: %s" % (name, type(exc).__name__, exc))
    if failed:
        return 1
    import tensorflow as tf
    print("TensorFlow contrib available:", hasattr(tf, "contrib"))
    print("scope: imports only; no audio file, checkpoint, training, or server verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
