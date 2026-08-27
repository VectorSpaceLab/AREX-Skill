# Cross-cutting troubleshooting

This file covers package-wide installation and import issues that affect multiple sub-skills.

## Common symptoms and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError` for `pytorch_metric_learning` | The package was not installed into the active environment | Install the package again, preferably with the editable `.[with-hooks-cpu]` path when working from a checkout. |
| `ImportError` for `torchvision` | The environment is missing the companion vision package | Install a compatible `torch` / `torchvision` pair before the repo package. |
| `ImportError` for `faiss` or `faiss.contrib.torch_utils` | The hooks extra was not installed | Use `pytorch-metric-learning[with-hooks-cpu]` for the CPU faiss path. |
| `ImportError` for `record_keeper` or tensorboard symbols | Logging dependencies are missing | Install the hooks extra or the missing logging dependencies explicitly. |
| `pip check` fails | One or more packages conflict after install | Reinstall into a clean prefix or repair the conflicting package set. |
| CPU import works but GPU/distributed code is unverified | The inspection environment intentionally does not include a CUDA backend | Treat GPU/distributed behavior as optional unless the task specifically requires it. |

## Package-wide recovery checklist

1. Verify the environment Python really belongs to the private inspection prefix.
2. Run `python -m pip check` before trusting an import-only success.
3. Confirm the package version matches the repository provenance.
4. Install the `with-hooks-cpu` extra when the task touches evaluation, inference, or logging.
5. Keep GPU and dataset-download claims separate from the CPU smoke checks unless you explicitly verified them.

## When to read the sub-skills

- `sub-skills/components/SKILL.md` for loss, miner, reducer, regularizer, and extension issues.
- `sub-skills/training/SKILL.md` for trainer, hook, checkpoint, and logging issues.
- `sub-skills/evaluation/SKILL.md` for faiss, metrics, and inference issues.
- `sub-skills/data/SKILL.md` for dataset and sampler issues.
