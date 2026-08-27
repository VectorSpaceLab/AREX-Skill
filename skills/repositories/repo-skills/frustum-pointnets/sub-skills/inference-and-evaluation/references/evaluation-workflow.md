# Evaluation workflow

The validation path has two data modes. Ground-truth frustums permit loss/IoU
comparison; RGB-detection frustums carry detector confidence and require
`--from_rgb_detection` plus an index file to write per-frame results.

The source commands then invoke an offline KITTI evaluator after inference. The
evaluator source is C++ and must be compiled for the host; do not use a stale
binary from another platform. Keep the model output directory, evaluator input
`data/` directory, and summary logs separate.

Before a run, check:

- model checkpoint prefix exists and matches v1/v2;
- pickle object stream and point channel count match the CLI;
- RGB detector file and generated RGB-frustum pickle refer to the same frame ids;
- output directory is new and writable;
- evaluator compiler/toolkit is available if AP is required.

The test-set path is not a turnkey command in this release. It needs test-set
2D detector outputs and modified preparation/index settings. Do not infer test
AP from a validation run.
