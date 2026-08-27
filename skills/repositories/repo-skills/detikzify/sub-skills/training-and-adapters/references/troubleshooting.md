# Troubleshooting

## Dependency issues

- If the refinement workflow fails to import TRL, the environment is missing the TRL vision-support fork.
- If a legacy model path fails, check for `timm` / `legacy` support.
- If adapter workflows fail to build text inputs, verify that the embedding model and processor were loaded together.

## Distributed launch issues

- Check `WORLD_SIZE`, `RANK`, and the `torchrun` launch command first.
- Some repo entrypoints, including `examples/tikzero/pretrain.py` and `examples/tikzero/train.py`, initialize `torch.distributed` at startup; when you run them directly for `--help` or a single-process debug invocation, set `RANK=0`, `WORLD_SIZE=1`, `MASTER_ADDR=127.0.0.1`, and a free `MASTER_PORT`.
- Make sure every process sees the same model and dataset paths.
- If a training job stalls at startup, verify the GPU runtime before investigating the dataset.

## Checkpoint and output issues

- An existing output directory may trigger resume logic.
- If a run should start fresh, use a new output directory or the workflow's overwrite flag.
- Keep an eye on the last checkpoint if DeepSpeed or gradient checkpointing is enabled.

## Data and memory issues

- Large datasets and sketchification are GPU-heavy and can fail for simple memory reasons.
- If a dataset filter removes too many examples, inspect the text length constraints instead of assuming the model is broken.
- Refinement and sketchification are both expensive enough that a quick CPU import does not validate the workflow.
