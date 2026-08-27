# Troubleshooting

## Purpose

Use this root troubleshooting guide for cross-family failures shared by GAN, VAE, RBM, and Helmholtz Machine examples. Family-specific notes live under each sub-skill's `references/troubleshooting.md`.

## First response checklist

1. Identify the model family: GAN, VAE, RBM, or Helmholtz Machine.
2. Use `references/model-catalog.md` or `scripts/model_catalog.py` to map the request to a source artifact label and owner sub-skill.
3. Run `scripts/check_legacy_stack.py` if the user wants to execute unchanged scripts.
4. Decide whether the user wants a legacy environment or a modern compatibility patch.
5. Avoid launching a full training loop as a quick smoke test; prefer parser/static/compatibility checks unless the user explicitly approves a long run and any downloads.

## Common failures

| Symptom | Likely cause | What to do next |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'tensorflow.examples'` | Modern TensorFlow no longer bundles the old MNIST helper used across the repo. | Use a TF1-era environment or patch the script to a modern MNIST loader before trying to train. |
| `AttributeError: module 'numpy' has no attribute 'float'` | NumPy 1.24+ removed `np.float`; RBM and Helmholtz examples hit this directly. | Replace with `float` or `np.float64`, or pin a legacy NumPy build if preserving the script unchanged matters. |
| `AttributeError: module 'numpy' has no attribute 'int'` | NumPy 1.24+ removed `np.int`; some GAN/VAE PyTorch variants use it for labels. | Replace with `int` or `np.int64`, or pin a compatible NumPy. |
| `IndexError: invalid index of a 0-dim tensor` | Modern PyTorch scalar tensors cannot be read with `.data[0]`. | Replace old scalar logging with `.item()` before rerunning. |
| MNIST not found or downloads unexpectedly | The scripts use relative paths such as `../../MNIST_data` and old download helpers. | Pre-seed MNIST at the expected location or patch the loader to accept an explicit data directory. |
| Output images are missing or land in the wrong directory | `out/` is relative to the process working directory, not an absolute output path. | Check the working directory and write permissions; patch output paths if running from another location. |
| No CLI flags work | The repository has no argparse/Click CLI. | Edit constants in source or write an external wrapper; do not invent flags that the scripts do not accept. |
| Training appears stuck | Many examples run for 100k to 1M iterations and only print/save periodically. | Treat this as expected for full training; do not use full training as a routine validation check. |

## Family routing reminders

- GAN variants: `sub-skills/gan/SKILL.md`
- VAE variants: `sub-skills/vae/SKILL.md`
- Binary RBM CD/PCD: `sub-skills/rbm/SKILL.md`
- Helmholtz Machine wake-sleep: `sub-skills/helmholtz-machine/SKILL.md`

## Safe validation approach

For repository-skill verification or quick triage, prefer:

```bash
python scripts/check_legacy_stack.py
python scripts/model_catalog.py --family gan
```

Only run original long training scripts when the user explicitly needs execution, the data path is known, the environment is compatible, and the runtime cost is acceptable.
