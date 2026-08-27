#!/usr/bin/env python3
"""Emit a minimal project-specific Mask_RCNN training script template.

This helper is intentionally non-training. It writes or prints a starter script
that future agents can adapt to a real dataset subclass and weight path.
"""

from __future__ import annotations

import argparse
from pathlib import Path

TEMPLATE = '''#!/usr/bin/env python3
"""Project-specific Mask_RCNN training entry point.

Fill in the dataset subclass, weight paths, and configuration for your project.
This template does not download data or train by itself.
"""

from mrcnn.config import Config
from mrcnn import model as modellib


class TrainConfig(Config):
    NAME = "my_dataset"
    NUM_CLASSES = 1 + 1  # background + foreground classes
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1
    IMAGE_MIN_DIM = 512
    IMAGE_MAX_DIM = 512
    STEPS_PER_EPOCH = 100
    VALIDATION_STEPS = 5


# TODO: import and prepare your dataset subclasses from a project-specific module.
# dataset_train = ...
# dataset_val = ...


def main():
    config = TrainConfig()
    model = modellib.MaskRCNN(mode="training", config=config, model_dir="logs")
    # model.load_weights("path/to/weights.h5", by_name=True, exclude=[...])
    # model.train(dataset_train, dataset_val, learning_rate=config.LEARNING_RATE,
    #             epochs=30, layers="heads")


if __name__ == "__main__":
    main()
'''


def main() -> int:
    ap = argparse.ArgumentParser(description="Emit a minimal Mask_RCNN training template.")
    ap.add_argument("--output", type=Path, help="Write the template to this file instead of stdout.")
    args = ap.parse_args()
    if args.output:
        args.output.write_text(TEMPLATE)
        print(f"wrote {args.output}")
    else:
        print(TEMPLATE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
