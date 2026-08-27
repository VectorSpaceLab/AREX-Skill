#!/usr/bin/env python3
"""Inspect Tacotron model symbols or build a small TensorFlow 1.x graph.

Without ``--repo-root`` this prints an unverified reference summary only. A
checkout-backed inspection imports the source from the supplied root and does
not load checkpoints or validate audio quality.
"""
import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Tacotron checkout to inspect")
    parser.add_argument("--build-graph", action="store_true", help="Build a small inference graph")
    args = parser.parse_args()
    if not args.repo_root:
        if args.build_graph:
            parser.error("--build-graph requires --repo-root")
        print("reference only (no checkout inspected; values are unverified)")
        print("model: tacotron")
        print("public outputs: mel_outputs, linear_outputs, alignments")
        print("default dimensions: num_mels=80, num_freq=1025, outputs_per_step=5")
        return 0
    root = os.path.abspath(args.repo_root)
    required = ("hparams.py", "models", "text", "util")
    if not os.path.isdir(root):
        parser.error("--repo-root is not a directory: %s" % root)
    missing = [name for name in required
               if not os.path.exists(os.path.join(root, name))]
    if missing:
        parser.error("--repo-root is not a Tacotron checkout; missing: %s" %
                     ", ".join(missing))
    os.chdir(root)
    sys.path.insert(0, root)
    import hparams
    import models
    print("checkout cwd:", root)
    print("model:", models.create_model.__name__)
    print("hparams:", "num_mels=%s num_freq=%s outputs_per_step=%s max_iters=%s" % (
        hparams.hparams.num_mels, hparams.hparams.num_freq,
        hparams.hparams.outputs_per_step, hparams.hparams.max_iters))
    if args.build_graph:
        import tensorflow as tf
        tf.reset_default_graph()
        inputs = tf.placeholder(tf.int32, [1, None], name="inspect_inputs")
        lengths = tf.placeholder(tf.int32, [1], name="inspect_lengths")
        model = models.create_model("tacotron", hparams.hparams)
        model.initialize(inputs, lengths)
        print("mel:", model.mel_outputs.shape)
        print("linear:", model.linear_outputs.shape)
        print("alignments:", model.alignments.shape)
        print("graph smoke: built without checkpoint or audio synthesis")
    else:
        print("source inspection only: graph not built; checkpoint/audio not verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
