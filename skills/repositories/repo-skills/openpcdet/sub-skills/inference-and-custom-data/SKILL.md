---
name: inference-and-custom-data
description: "Run and adapt OpenPCDet demo inference, custom point-cloud inputs,
  visualization, and CustomDataset workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# OpenPCDet Inference and Custom Data

Use this sub-skill for demo inference, `.bin`/`.npy` point clouds, checkpoint/config pairing, visualization, non-visual prediction adaptation, and custom dataset setup.

## Fast route

1. Verify runtime/native ops with `../../scripts/inspect_openpcdet_runtime.py --require-cuda-ops`.
2. Validate point-cloud files with `scripts/check_point_cloud_array.py`.
3. Read `references/demo-and-custom-data.md` for DemoDataset and CustomDataset semantics.
4. Build a demo command with `../../scripts/plan_openpcdet_command.py --mode demo`.
5. Route full dataset info/database generation to `../data-preparation/SKILL.md`.

## Demo command shape

```bash
# from the generated skill root
python scripts/plan_openpcdet_command.py --repo <checkout> --mode demo --cfg <config.yaml> --ckpt <checkpoint.pth> --data-path <point-file-or-dir> --ext .bin
```

The helper prints the command by default. Add `--execute` only after config/checkpoint/data/visualization dependencies are confirmed.

## Critical caveats

- `.bin` demo files are read as float32 and reshaped to `N x 4`.
- `.npy` demo files must be 2-D arrays with the expected point feature columns.
- The config's `POINT_FEATURE_ENCODING`, point cloud range, class names, and checkpoint must match.
- Open3D or Mayavi is needed for interactive drawing; non-visual inference should adapt the demo loop to save predictions instead.
