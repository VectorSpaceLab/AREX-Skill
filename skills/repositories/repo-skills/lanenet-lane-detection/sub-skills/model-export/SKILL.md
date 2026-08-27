---
name: model-export
description: "Routes LaneNet checkpoint freezing and optional MNN/mobile export
  workflows for frozen PB and MNN deployment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Export

Use this sub-skill when the user has a LaneNet TensorFlow checkpoint and wants a frozen `.pb` graph, or when they need to understand the optional `.pb` to MNN/mobile deployment path.

## Route First

- Need to create or resume checkpoints? Read [../training/SKILL.md](../training/SKILL.md) first.
- Need to run checkpoint-backed prediction or TuSimple evaluation before export? Read [../inference-evaluation/SKILL.md](../inference-evaluation/SKILL.md) first.
- Need frozen PB or MNN/mobile export details? Read [references/mnn-export.md](references/mnn-export.md).
- Export failed or the MNN runtime cannot find tensors/config values? Read [references/troubleshooting.md](references/troubleshooting.md).

## Core Helper

The bundled freeze helper is [scripts/freeze_lanenet_model.py](scripts/freeze_lanenet_model.py). It preserves the repository freeze API `convert_ckpt_into_pb_file(ckpt_file_path, pb_file_path)` and adds CLI help, repo-root handling, checkpoint preflight checks, and output-node reporting.

Quick shape from this sub-skill directory:

```bash
python scripts/freeze_lanenet_model.py \
  --repo-root <lanenet-repo-root> \
  --weights_path <checkpoint-prefix> \
  --save_path <output.pb>
```

The frozen graph uses these fixed nodes:

- input: `lanenet/input_tensor`
- binary segmentation output: `lanenet/final_binary_output`
- pixel embedding output: `lanenet/final_pixel_embedding_output`

## Boundaries

This sub-skill documents checkpoint freeze, MNN converter command shape, MNN `config.ini` fields, runtime preprocessing expectations, and export-specific troubleshooting. It intentionally does not bundle the MNN converter shell script or document a full C++/MNN build, because the converter and mobile runtime toolchain are external to the Python LaneNet repository.
