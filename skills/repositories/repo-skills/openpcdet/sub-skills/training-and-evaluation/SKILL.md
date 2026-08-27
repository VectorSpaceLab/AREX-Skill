---
name: training-and-evaluation
description: "Operate OpenPCDet train/test workflows, distributed launchers,
  checkpoint resume/eval_all, outputs, and evaluation troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# OpenPCDet Training and Evaluation

Use this sub-skill for training, evaluation, checkpoint resume, distributed jobs, output directories, result files, and CLI flags.

## Fast route

1. Verify runtime with `../../scripts/inspect_openpcdet_runtime.py --require-cuda-ops`.
2. Verify dataset products with `../data-preparation/SKILL.md`.
3. Summarize the target YAML with `../../scripts/summarize_openpcdet_config.py --cfg <config.yaml>`.
4. Build the train/test command with `../../scripts/plan_openpcdet_command.py`.
5. Read `references/train-test-workflows.md` for command semantics and failure modes.

## Command helper examples

Print commands from the generated skill root:

```bash
python scripts/plan_openpcdet_command.py --repo <checkout> --mode train --cfg <config.yaml> --extra-tag <tag>
python scripts/plan_openpcdet_command.py --repo <checkout> --mode test --cfg <config.yaml> --ckpt <checkpoint.pth> --save-to-file
```

Add `--execute` only when the user has authorized the job and dataset/GPU budget.

## Boundaries

- Dataset info/database generation belongs to `../data-preparation/SKILL.md`.
- Config/model-family selection belongs to `../models-and-configs/SKILL.md`.
- Demo/custom point-cloud inference belongs to `../inference-and-custom-data/SKILL.md`.
