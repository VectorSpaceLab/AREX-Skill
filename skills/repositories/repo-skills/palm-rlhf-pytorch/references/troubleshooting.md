# Troubleshooting

## Purpose

This file collects package-wide failure modes that cut across the sub-skills.
Use a sub-skill's own troubleshooting reference for workflow-specific details.

## Install And Import Issues

### `ModuleNotFoundError` for `palm_rlhf_pytorch`

Likely causes:
- The package was not installed into the target environment.
- The user is still running the system Python instead of the inspected environment.
- A source checkout path shadows the installed package.

Recovery:
- Install the package in editable mode from the repository checkout with `python -m pip install -e .`.
- Re-run the bundled inspector: `python scripts/inspect_palm_rlhf.py --device auto --check-cuda`.
- Confirm the import comes from the installed package, not a different checkout.

### Missing runtime dependencies

The base package depends on `accelerate`, `beartype`, `einops`, `einx`, `adam-atan2-pytorch`, `memmap-replay-buffer`, `torch-einops-utils`, `hl-gauss-pytorch`, `torch`, `tqdm`, and `x-mlps-pytorch`.

The inspected repository also contains source examples that import `lion_pytorch`, but that extra is not declared in `pyproject.toml`.

Recovery:
- Install only the dependencies needed for the selected workflow.
- Treat `examples.py` and `train.py` as reference-only unless you explicitly add the missing extra.
- Do not assume a successful import of the package proves that the source example scripts can run unchanged.

## Backend And Device Issues

### CUDA is available but the skill is only using CPU smoke checks

This is not a failure for the selected scope. The skill intentionally treats CUDA acceleration as optional because the package's public workflows are CPU-capable for smoke validation.

Recovery:
- Use `--device auto` in bundled scripts for convenience.
- Use `--device cpu` if you need a deterministic baseline.
- Use `--flash-attn` only if you want to compare the SDPA path.

### `flash_attn=True` fails or behaves unexpectedly

Likely causes:
- PyTorch is too old for scaled-dot-product attention.
- A CUDA device is unavailable.
- You are comparing SDPA with a different CPU path.

Recovery:
- Set `flash_attn=False` first.
- Re-run a tiny smoke check with the bundled scripts.
- Compare CPU and CUDA runs only after the shape and loss checks pass.

## Workflow-Specific Surfaces

### No pretrained checkpoint is shipped

The README states that the repository does not ship a trained model.

Recovery:
- Use the PaLM and reward-model smoke scripts to verify mechanics only.
- Do not promise inference quality or a ready-to-use chatbot checkpoint.

### Source example or training scripts are expensive

`examples.py` and `train.py` are useful evidence but not the default runtime path for the skill.

Recovery:
- Use the bundled tiny smoke scripts instead.
- Treat the original scripts as reference material or as explicit maintainer-only workflows.

### Prompt or mask shape errors

Typical symptoms:
- Assertion failures mentioning prompt inputs.
- Mismatched reward or generation shapes.
- Confusion about `seq_len` versus suffix length.

Recovery:
- Read the relevant sub-skill API reference.
- Confirm whether you are using `prompt_mask`, `prompt_lengths`, or `prompt_token_ids`.
- Remember that `PaLM.generate(seq_len=...)` counts the total target length.

## When To Stop

Stop and ask for help if the task needs a missing wheel, a blocked backend, a large training run, or a source example that depends on undeclared extras and the user has not asked to install them.
