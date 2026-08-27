---
name: graphgym-experiments
description: "Configure, validate, customize, and troubleshoot PyTorch Geometric
  GraphGym experiments without running unsafe benchmark-scale jobs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# GraphGym Experiments

Use this sub-skill when a task involves PyTorch Geometric GraphGym experiment YAML files, run-single/run-batch concepts, custom GraphGym registration, result directories, or GraphGym optional-dependency troubleshooting.

Do not use this sub-skill for general GNN layer design, arbitrary training-loop implementation, data container basics, heterogeneous graph modeling, explainability, or distributed training. Route those workflows to sibling sub-skills when present.

## Start Here

- Read [graphgym configs](references/graphgym-configs.md) when creating or editing GraphGym YAML, choosing `dataset`, `train`, `model`, `gnn`, or `optim` keys, or mapping run-single/run-batch shell concepts into safe commands.
- Read [customization](references/customization.md) when registering custom activations, layers, losses, datasets, loaders, optimizers, schedulers, metrics, training functions, networks, or config groups.
- Read [troubleshooting](references/troubleshooting.md) when imports fail for optional GraphGym extras, a config key/type is rejected, a registry key collides, results are hard to find, or a batch job would create expensive side effects.
- Run [validate_graphgym_config.py](scripts/validate_graphgym_config.py) to inspect a GraphGym YAML file without launching training, downloading datasets, using GPUs, or writing result directories.
- Copy or compare against [example_graphgym_node.yaml](scripts/example_graphgym_node.yaml) for a minimal CPU-friendly node-classification template.

## Safe Commands

```bash
python scripts/validate_graphgym_config.py \
  scripts/example_graphgym_node.yaml
python scripts/validate_graphgym_config.py --help
```

The validator prints JSON with `ok`, dependency status, recognized sections, warnings, and errors. It intentionally does not call `torch_geometric.graphgym.main`, `run_single.sh`, `run_batch.sh`, `configs_gen.py`, or any training entrypoint.

## Common Tasks

- Create a single experiment YAML with top-level sections such as `out_dir`, `dataset`, `train`, `model`, `gnn`, and `optim`; keep `accelerator: cpu` and low `optim.max_epoch` for smoke runs.
- Explain run-single as `python main.py --cfg <config.yaml> --repeat <n>` in a GraphGym project, but do not run it unless the user explicitly accepts dataset downloads, result writes, optional extras, and training time.
- Explain run-batch as generating perturbed configs from a base YAML and grid file, then queueing many runs; treat it as benchmark-scale by default.
- Register custom modules with `torch_geometric.graphgym.register_*` decorators or direct calls, using unique lowercase keys and testing registry insertion before training.
- Confirm results under the configured `out_dir`, then distinguish per-seed run directories from aggregated metrics and copied config files.

## Route Boundaries

- For PyG model layer internals, `MessagePassing`, `GCNConv`, `GATConv`, `SAGEConv`, or training-loop code outside GraphGym, use `../gnn-modeling/SKILL.md`.
- For `Data`, `HeteroData`, custom datasets, transforms, or local fixture validation, use `../data-and-datasets/SKILL.md`.
- For mini-batch loaders, neighbor sampling, and link loaders outside GraphGym configs, use `../loaders-and-sampling/SKILL.md`.
- For large-scale distributed execution, remote backends, multi-GPU, and hardware scheduling, use `../scalable-distributed/SKILL.md`.
