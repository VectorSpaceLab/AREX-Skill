---
name: training
description: "Route MMAudio DDP training, smoke runs, checkpoint resume, EMA
  synthesis, and training-side output inspection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training

Use this route when a user wants to launch, resume, or debug MMAudio training on CUDA, or needs a bounded smoke command for a quick environment check. This route assumes precomputed feature memmaps and external model assets already exist. It does not extract features or run arbitrary batch evaluation.

## Read first

- `references/training-workflow.md` for the end-to-end lifecycle, command patterns, expected outputs, and resume precedence.
- `references/configuration.md` for Hydra keys, supported model variants, batch-size semantics, and path conventions.
- `references/troubleshooting.md` for NCCL, env-var, checkpoint, model-variant, and asset failures.
- `scripts/build_train_command.py` to render a smoke-safe or full `torchrun` command without launching training.

## What this route owns

- DDP training launch on one node.
- `example_train` smoke runs and bounded one-iteration checks.
- Checkpoint resume, pretrained `weights` loading, and checkpoint precedence.
- EMA synthesis, TensorBoard logging, and the built-in post-training sample path.
- Interpreting artifacts under `output/<exp_id>/`.

## What this route excludes

- Feature extraction and memmap creation.
- Batch evaluation on arbitrary datasets.
- Demo or Gradio inference for pretrained models.

## Before you launch

- Use `torchrun`; `train.py` imports `mmaudio.sample` at module load, so plain `python train.py --help` can fail unless the distributed env vars are present.
- Confirm CUDA is available. This route has no CPU fallback.
- Install `av_bench`; the training loop and final sample use it when evaluation runs.
- Populate `ext_weights/` with the required empty-string, VAE, Synchformer, and vocoder assets for the chosen model.
- Make sure the example memmap fixtures, training memmaps, and any required validation/test caches exist before relying on `example_train` or a real training run.

## Typical path

1. Build a command with `scripts/build_train_command.py`.
2. Launch with `OMP_NUM_THREADS=4 torchrun --standalone --nproc_per_node=<N> train.py ...`.
3. Watch `output/<exp_id>/` for checkpoints, EMA files, logs, and sampled audio/video.
4. If you are resuming, decide whether you want an exact checkpoint or only model weights; do not pass both.
5. After the run, inspect the final EMA and the sample/eval outputs before deciding whether to continue training.

## Common gotchas

- The runtime code divides `batch_size` by the number of GPUs, so the value you pass must be compatible with the world size.
- `large_44k_v2` is not a training target in this code path.
- The built-in post-training sample is fixed to the extracted VGGSound test path defined in the config; for other evaluation datasets or metrics, use the evaluation route.
- The smoke command still reaches the built-in sample path at the end, so a "successful" smoke run needs the example fixtures plus the test cache to survive that final step.
- `mini_train` is not a reliable standalone smoke flag in the current loader logic; use `example_train=True` instead.
