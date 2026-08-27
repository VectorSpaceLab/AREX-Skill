---
name: detection-workflows
description: "Guides SimpleDet config-driven training, bbox and mask evaluation,
  fine-tuning, inference-speed benchmarking, checkpoints, and GPU-aware workflow
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Detection workflows

Use this route for training, bbox evaluation, mask evaluation, inference speed,
fine-tuning, FP16, model/config selection, or checkpoint output. Read
[cli-reference.md](references/cli-reference.md), then
[configuration.md](references/configuration.md) before constructing a command.

## Gate the workflow

SimpleDet is symbolic/static-shape MXNet. Its entry scripts import configs by
turning `config/foo.py` into module `config.foo`, read roidbs from
`data/cache/`, construct `mx.gpu` contexts from `KvstoreParam.gpus`, and write
under `experiments/`. Confirm all three before any long run.

Use the bundled wrapper to make the checkout root explicit and avoid unsafe
shell composition:

```bash
python <skill-root>/scripts/run_workflow.py --repo-root /path/to/simpledet \
  --entrypoint speed --config config/faster_r50v1_fpn_1x.py \
  --shape 800 1333 --gpu 0 --count 100 --dry-run
```

Remove `--dry-run` only after the setup diagnostic, config inspection, cache
validation, checkpoint check, and required CUDA backend check pass. The wrapper
does not make a workflow safe: the selected entry point can allocate GPUs,
read large data, load weights, and write experiments.

## Workflow routes

- `train`: fit or resume a detector; long-running and weight-mutating.
- `test`: bbox evaluation from a compatible checkpoint.
- `mask-test`: bbox plus instance-mask evaluation; requires polygon data.
- `speed`: static-shape one-GPU forward benchmark; requires `--shape`.

Use [workflows.md](references/workflows.md) for staged execution and
[troubleshooting.md](references/troubleshooting.md) for failures.

## Route onward

- Missing runtime or CUDA/mxnext: [setup-and-operations](../setup-and-operations/SKILL.md).
- Missing cache or bad annotations: [data-preparation](../data-preparation/SKILL.md).
- New model or symbol contract: [model-customization](../model-customization/SKILL.md).

Use [scripts/inspect_config.py](scripts/inspect_config.py) for source/config
inspection; it reports missing optional runtime packages rather than starting a
symbol build. Use the root [run_workflow.py](../../scripts/run_workflow.py)
wrapper for actual entry-point invocation.
