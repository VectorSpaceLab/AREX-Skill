#!/usr/bin/env python3
"""Check TensorLayer importability and run a tiny model smoke test.

Run this helper from any current working directory after installing the
package. Use --vision when you also want to check matplotlib/cv2 imports that
vision/app workflows rely on.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--vision',
        action='store_true',
        help='Also import matplotlib and cv2 to confirm vision helpers.',
    )
    args = parser.parse_args()

    try:
        import tensorflow as tf
        import tensorlayer as tl
        from tensorlayer.layers import Dense, Input
        from tensorlayer.models import Model
    except Exception as exc:  # pragma: no cover - diagnostic helper
        print(f'tensorlayer import failed: {exc}', file=sys.stderr)
        return 1

    print(f'tensorlayer {tl.__version__}')
    print(f'tensorflow {tf.__version__}')

    if args.vision:
        try:
            import cv2
            import matplotlib
        except Exception as exc:  # pragma: no cover - diagnostic helper
            print(f'vision dependency import failed: {exc}', file=sys.stderr)
            return 2
        print(f'matplotlib {matplotlib.__version__}')
        print(f'cv2 {cv2.__version__}')

    ni = Input([None, 4], name='input')
    nn = Dense(3, act=tf.nn.relu, name='dense')(ni)
    model = Model(inputs=ni, outputs=nn, name='tiny')
    model.eval()
    out = model(np.ones((2, 4), dtype=np.float32))
    print(f'tiny-model-output {tuple(out.shape)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
