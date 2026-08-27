# Recognition CLI and configuration reference

See the [recognition router](../SKILL.md), [API/shape contract](api-reference.md),
[checkpoint aliases](model-zoo.md), and [troubleshooting guide](troubleshooting.md).
The [tiny smoke](../scripts/run_stgcn_smoke.py) is the safe first check; the
commands below can require real datasets, checkpoints, CUDA, and substantial
runtime.

## Application entry point

Applications are configuration-driven:

```text
mmskl path/to/config.yaml
# equivalent entry point:
python mmskl.py path/to/config.yaml
```

The first positional argument is a config path. A config may define
`argparse_cfg`, whose `bind_to` entries expose processor values as command-line
flags. Check the effective options for a specific config rather than assuming
that every flag is accepted:

```text
mmskl path/to/config.yaml --help
```

The command-line parser also supports the repository's documented pose-demo
shortcuts, but those are outside recognition and route to
[pose-estimation](../../pose-estimation/SKILL.md). Use an explicit recognition
config for ST-GCN.

Config paths and dataset paths must exist in the environment where the command
runs. Resolve relative dataset and work-directory paths deliberately; a valid
model config with missing data is not an evaluation.

## Test/evaluation pattern

A recognition test config contains a processor like:

```yaml
processor_cfg:
  type: "processor.recognition.test"
  checkpoint: "mmskeleton://st_gcn/ntu-xsub"
  model_cfg:
    type: "models.backbones.ST_GCN_18"
    in_channels: 3
    num_class: 60
    dropout: 0.5
    edge_importance_weighting: true
    graph_cfg:
      layout: "ntu-rgb+d"
      strategy: "spatial"
  dataset_cfg:
    type: "deprecated.datasets.skeleton_feeder.SkeletonFeeder"
    data_path: path/to/val_data.npy
    label_path: path/to/val_label.pkl
  batch_size: null
  gpu_batch_size: 64
  gpus: -1
```

The stock dataset-specific patterns use `num_class: 60` and the NTU layout for
NTU cross-subject/cross-view data, and `num_class: 400` with `layout:
openpose` for Kinetics-skeleton. Keep the dataset's actual joint count and
label vocabulary authoritative. The processor requires either `batch_size` or
`gpu_batch_size`; with `gpus < 0`, it derives the GPU count from
`torch.cuda.device_count()`.

Typical invocation:

```text
mmskl path/to/recognition-test.yaml
mmskl path/to/recognition-test.yaml --checkpoint path/to/local-checkpoint.pth
```

A local checkpoint avoids an implicit network dependency. This reference does
not establish that any data or remote checkpoint was downloaded or evaluated.

## Training pattern

A recognition train config contains:

```yaml
processor_cfg:
  type: "processor.recognition.train"
  model_cfg:
    type: "models.backbones.ST_GCN_18"
    in_channels: 3
    num_class: 60
    dropout: 0.5
    edge_importance_weighting: true
    graph_cfg:
      layout: "ntu-rgb+d"
      strategy: "spatial"
  loss_cfg:
    type: "torch.nn.CrossEntropyLoss"
  dataset_cfg:
    - type: "deprecated.datasets.skeleton_feeder.SkeletonFeeder"
      data_path: path/to/train_data.npy
      label_path: path/to/train_label.pkl
    - type: "deprecated.datasets.skeleton_feeder.SkeletonFeeder"
      data_path: path/to/val_data.npy
      label_path: path/to/val_label.pkl
  batch_size: 64
  gpus: 1
  optimizer_cfg:
    type: "torch.optim.SGD"
    lr: 0.1
    momentum: 0.9
    nesterov: true
    weight_decay: 0.0001
  workflow: [["train", 5], ["val", 1]]
  total_epochs: 80
  work_dir: path/to/work-dir
  resume_from:
  load_from:
```

`argparse_cfg` commonly binds `gpus`, `batch_size`, `work_dir`, and
`resume_from` for training. `--work_dir` changes where logs/checkpoints are
written; `--resume_from` resumes runner state, while `load_from` loads model
weights without being the same operation. Use a small synthetic forward first
and do not infer successful training from config parsing alone.

## Batch and GPU flags

- `batch_size` is the total loader batch size.
- `gpu_batch_size` is multiplied by the resolved GPU count when total
  `batch_size` is absent.
- `gpus` is a count in the legacy processor, not a general device string. A
  negative value means auto-detect CUDA device count; zero or an unavailable
  device set will not make the CUDA-wrapped processor CPU-safe.
- Lower batch size, worker count, and sequence length only after confirming the
  dataset/config contract. Avoid launching a long native run as a diagnostic.

For a user asking only whether the model API works, use the [download-free
smoke](../scripts/run_stgcn_smoke.py), not a train or evaluation command.
