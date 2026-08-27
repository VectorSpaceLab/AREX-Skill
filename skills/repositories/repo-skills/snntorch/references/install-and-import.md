# Install and import

Use this reference when you need a public install command, a minimal import check, or a reminder of which optional packages enable which snnTorch workflows.

## Baseline install

The base package is installed with:

```bash
pip install snntorch
```

A quick import check is:

```bash
python - <<'PY'
import snntorch as snn
print(snn.__version__)
PY
```

## Optional workflow packages

Add the following packages only when the task needs them:

| Workflow need | Helpful packages |
| --- | --- |
| Core neuron, surrogate, encoding, and training workflows | `torch` |
| Spike visualization | `matplotlib` and, for notebook-style animations, `celluloid` |
| NIR export/import | `nir` and `nirtorch` |
| Legacy `spikevision` dataset wrappers | `torchvision`, `h5py`, and `pandas` |

The repository metadata also defines a broader `full` dependency set that brings in `torch`, `matplotlib`, `nir`, and `nirtorch` when that extra is available in your install path.

## Broader smoke check

If you want a quick read on the wider runtime stack, run [`scripts/stack_smoke.py`](../scripts/stack_smoke.py). It imports the main snnTorch surfaces and can optionally probe CUDA with `--cuda`.

## If import fails

- First check that `torch` is installed in the same environment as `snntorch`.
- For plotting, confirm that `matplotlib` is installed before importing `snntorch.spikeplot`.
- For NIR, confirm that both `nir` and `nirtorch` are installed.
- For legacy spikevision, confirm that `torchvision`, `h5py`, and `pandas` are installed.
- If you are on a GPU host and need CUDA, use a torch wheel that matches your driver/toolkit combination, then rerun the import and smoke checks.

For workflow-specific failure modes, see [Cross-cutting troubleshooting](troubleshooting.md) and the owning sub-skill.
