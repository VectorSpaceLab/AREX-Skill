#!/usr/bin/env python3
"""Validate a pix2code trained-artifact directory before sampling.

This helper is read-only by default. It can optionally attempt a lightweight
legacy model load when `--load-model` is supplied and the historical ML stack is
available.
"""

from __future__ import print_function

import argparse
import os
REQUIRED = ["pix2code.json", "pix2code.h5", "meta_dataset.npy", "words.vocab"]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check pix2code trained artifact directories.")
    parser.add_argument("--artifacts", required=True, help="Directory expected to contain the trained pix2code files")
    parser.add_argument("--load-model", action="store_true", help="Attempt a lightweight legacy model load after file validation")
    args = parser.parse_args(argv)

    artifact_dir = os.path.abspath(args.artifacts)
    print("Artifact directory: {}".format(artifact_dir))
    if not os.path.isdir(artifact_dir):
        raise SystemExit("ERROR: artifact directory does not exist")

    missing = [name for name in REQUIRED if not os.path.isfile(os.path.join(artifact_dir, name))]
    if missing:
        raise SystemExit("ERROR: missing files: {}".format(", ".join(missing)))

    meta = os.path.join(artifact_dir, "meta_dataset.npy")
    try:
        import numpy as np
        try:
            data = np.load(meta, allow_pickle=True)
        except TypeError:
            data = np.load(meta)
        print("meta_dataset.npy shape: {} contents: {}".format(getattr(data, 'shape', 'unknown'), data))
    except Exception as exc:
        raise SystemExit("ERROR: unable to load meta_dataset.npy: {}: {}".format(exc.__class__.__name__, exc))

    print("PASS required files present: {}".format(", ".join(REQUIRED)))

    if args.load_model:
        try:
            from keras.models import model_from_json
            with open(os.path.join(artifact_dir, 'pix2code.json'), 'r') as fh:
                model = model_from_json(fh.read())
            model.load_weights(os.path.join(artifact_dir, 'pix2code.h5'))
            print('Legacy Keras model load succeeded')
        except Exception as exc:
            raise SystemExit('ERROR: legacy model load failed: {}: {}'.format(exc.__class__.__name__, exc))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
