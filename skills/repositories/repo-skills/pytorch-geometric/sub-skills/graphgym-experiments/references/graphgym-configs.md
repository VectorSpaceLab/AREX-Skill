# GraphGym Configs

GraphGym describes an experiment with a YAML file. Missing values are filled by GraphGym defaults when `torch_geometric.graphgym.set_cfg` is available and optional dependencies are installed. Treat the YAML as the source of truth for reproducibility, and validate it before launching training.

## Minimal Shape

A practical node-classification config usually includes:

```yaml
accelerator: cpu
out_dir: results
num_workers: 0
dataset:
  format: PyG
  name: Cora
  task: node
  task_type: classification
train:
  batch_size: 128
  eval_period: 1
  ckpt_period: 100
  sampler: full_batch
model:
  type: gnn
  loss_fun: cross_entropy
gnn:
  layers_mp: 2
  dim_inner: 16
  layer_type: gcnconv
  stage_type: stack
  dropout: 0.1
optim:
  optimizer: adam
  base_lr: 0.01
  max_epoch: 200
```

For a quick CPU smoke configuration, set `accelerator: cpu`, `num_workers: 0`, and a small `optim.max_epoch`. For real experiments, ensure `dataset.dir` points to an acceptable cache location and that dataset downloads are permitted.

## Important Sections

- `out_dir`: base result directory. GraphGym derives config-specific and per-seed run directories from this value.
- `accelerator`: `cpu`, `cuda`, or `auto`; choose `cpu` when reproducibility or GPU availability is uncertain.
- `dataset`: dataset format, name, task, split behavior, encoders, transforms, and local/cache location.
- `train`: batch size, sampler, evaluation/checkpoint periods, checkpoint behavior, and sampling settings.
- `val`: validation/test sampler behavior when different from training.
- `model`: model type, loss function, graph pooling, link decoding, and task-specific thresholds.
- `gnn`: message-passing depth, hidden dimension, layer type, stage type, activation, dropout, normalization, and aggregation choices.
- `optim`: optimizer, learning rate, weight decay, scheduler, and epoch count.

GraphGym supports at most two levels for standard config keys, such as `dataset.name` or `gnn.layer_type`. Custom config groups should follow the same shallow pattern unless a project has explicitly registered and tested deeper handling.

## Single Experiments

The source run-single pattern is equivalent to:

```bash
python main.py --cfg configs/my_experiment.yaml --repeat 3
```

Use this only inside a prepared GraphGym project where `main.py` imports any custom registration package before loading the config. `--repeat` increments seeds and creates one run directory per seed. Before running, ask whether dataset downloads, result writes, checkpoint writes, optional dependencies, and training time are acceptable.

## Batch Experiments

The source run-batch concept has two stages:

1. Generate many derived YAML files from a base config, optional budget config, and grid file.
2. Queue the generated configs with a repeat count, concurrency limit, and sleep interval.

Treat batch mode as benchmark-scale. It can create many configs, start many Python processes, download datasets, and write large result trees. Prefer reviewing the base config and grid first, then doing a single tiny smoke run before queueing a batch.

## Result Layout

GraphGym writes under `out_dir` and creates config-specific output folders. A repeated experiment creates per-seed subdirectories and aggregation outputs. Common files include copied `config.yaml`, logs, per-split `stats.json`, best-epoch summaries, and aggregate CSV/JSON outputs depending on the run type.

If results look missing, first confirm the effective `out_dir`, config filename stem, seed/repeat count, and whether aggregation ran after all seeds completed.

## Safe Validation

Run the bundled validator before training:

```bash
python scripts/validate_graphgym_config.py path/to/config.yaml
```

It checks YAML parseability, known section names, common key types, common enum values, and high-risk settings. It does not import GraphGym, instantiate datasets, generate grids, start training, or write results.
