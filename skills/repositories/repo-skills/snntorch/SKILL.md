---
name: snntorch
description: "Use snnTorch to build spiking neuron models, encode data into
  spikes, train with surrogate gradients, plot spike tensors, export/import NIR
  graphs, and maintain legacy spikevision workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# snnTorch

Use this skill when a task touches the `snntorch` package: stateful spiking neurons, spike encoders, surrogate gradients, training helpers, plotting, NIR exchange, or legacy neuromorphic datasets.

## Install and import check

Read [Install and import](references/install-and-import.md) for the package-level install matrix.
For a quick smoke test, run:

```bash
pip install snntorch
python -c "import snntorch as snn; print(snn.__version__)"
python scripts/stack_smoke.py
```

If you need the broader stack for plotting, NIR, or legacy dataset workflows, add the optional dependencies described in that reference.

## Route by task

- Build, combine, or debug neuron and layer workflows, hidden-state ownership, reset semantics, recurrent cells, BNTT, or `GradedSpikes` -> [`core-neurons`](sub-skills/core-neurons/SKILL.md)
- Convert raw tensors or labels into spikes, choose surrogate gradients, compute losses or accuracies, inspect monitors, run backprop wrappers, or use STDP -> [`encoding-training`](sub-skills/encoding-training/SKILL.md)
- Export supported models to NIR or import NIR graphs back into snnTorch -> [`nir-interoperability`](sub-skills/nir-interoperability/SKILL.md)
- Plot rasters, spike counts, traces, or animations -> [`plotting`](sub-skills/plotting/SKILL.md)
- Use the legacy `spikevision` dataset wrappers or migrate old neuromorphic dataset code -> [`spikevision`](sub-skills/spikevision/SKILL.md)

## Common starting points

- If the model returns the wrong number of values, states leak across batches, or `nn.Sequential` breaks on tuple outputs, start with `core-neurons`.
- If the task starts with tensors or labels and ends with spike codes, a loss, or a training step, start with `encoding-training`.
- If `export_to_nir` or `import_from_nir` fails with type inference or graph-shape errors, start with `nir-interoperability`.
- If plotting fails in a headless environment or `spike_count` labels behave oddly, start with `plotting`.
- If an old tutorial or repo script uses `snntorch.spikevision`, treat it as legacy and start with `spikevision`; new work should use Tonic instead.

## Shared references

- [Install and import](references/install-and-import.md)
- [Workflow map](references/workflows.md)
- [Cross-cutting troubleshooting](references/troubleshooting.md)
- [Repository provenance](references/repo-provenance.md)
- [Routing metadata](references/repo-routing-metadata.json)
- [`scripts/stack_smoke.py`](scripts/stack_smoke.py)

## Boundaries

This skill is a runtime router, not a maintainer guide. It does not cover release engineering, CI, packaging automation, or repo-specific development tasks. Keep the generated guidance self-contained inside this skill tree and use the sub-skills for workflow depth.
