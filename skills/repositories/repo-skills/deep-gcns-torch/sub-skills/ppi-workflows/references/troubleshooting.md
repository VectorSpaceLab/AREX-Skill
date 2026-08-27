# PPI troubleshooting

This guide diagnoses source-observed boundaries without fetching data,
checkpoints, or dependencies. Keep the original error, PyTorch/PyG versions,
phase, loader mode, device, architecture tuple, and checkpoint basename in the
report.

## Data root, downloads, and split failures

### `PPI` tries to download or raw files are missing

The PyG PPI dataset normally downloads and processes data when the requested
root is incomplete. That is an unsafe side effect for this operating skill.
Stop the run, ask the caller to stage an approved local dataset, and verify the
three split contracts (`train`, `val`, `test`) before retrying. Do not add a
`download()` call, use a network URL, or silently substitute OGB proteins.

Check that the prepared root has compatible processed/raw data for the installed
PyG version and that every split exposes `x`, `edge_index`, and `y`. A root with
only training graphs will fail later when the model tries to infer
`num_classes` from the test dataset.

### Feature or label shape errors

Print the first local graph's shapes before constructing the model:

```text
x.shape          -> [N, 50] by the standard contract
edge_index.shape -> [2, E]
y.shape          -> [N, 121]
```

Set `--in_channels` to the actual feature width. Do not set `--n_classes`; the
source infers it from the test dataset. If a checkpoint's final layer does not
match the inferred class count, use a checkpoint trained for the same PPI label
set rather than reshaping weights.

## Imports and PyG version drift

### `ModuleNotFoundError: opt`, `architecture`, `gcn_lib`, or `utils`

The source example combines directory-local imports (`opt`, `architecture`)
with a source-root import path for `gcn_lib` and `utils`. Run the neutral
`<ppi-entrypoint>` command shape from a caller project that supplies those
modules, or adapt that caller project into a normal package. The original
source example is evidence only; do not open or execute it as part of the
runtime workflow. Do not hard-code an original checkout or private absolute
path into a runtime skill and do not make a copied skill pretend that those
modules are bundled.

A modern environment may still expose compatibility aliases for the source's
imports, but deprecation warnings are not proof that the full path works. Probe
imports and a tiny synthetic model construction before allocating PPI data.

### `DataLoader`/`DataListLoader` import or collation errors

The source imports loaders from the deprecated compatibility location
`torch_geometric.data`. Modern PyG also exposes them under
`torch_geometric.loader`; prefer the installed version's supported import when
adapting code. Keep the distinction clear:

- ordinary `DataLoader` yields a collated `Batch` with concatenated node
  tensors and a node-level `batch` vector;
- `DataListLoader` yields a list of `Data` objects for PyG `DataParallel`.

Do not pass a list to a model expecting `data.x` unless PyG DataParallel is the
component receiving and scattering that list. Conversely, do not assume a
collated `Batch` is valid input to the legacy DataParallel path.

### Multi-GPU validation behaves differently from training

The source uses `DataListLoader` only for the training loader when
`--multi_gpus` is enabled. It still creates ordinary validation/test loaders,
and `test()` moves each batch directly to the selected device. This is an
unverified source-era asymmetry. First run single-device evaluation. If
multi-GPU evaluation is required, explicitly adapt and test its loader/model
interface in the caller's code; do not claim the unmodified source path is
supported.

## GPU, CPU, and memory issues

### CUDA is unavailable or a CPU run fails while loading a checkpoint

Without `--use_cpu`, the parser selects CUDA if PyTorch reports it available;
`--use_cpu` forces CPU. Confirm that PyTorch, PyG, `torch-scatter`, and
`torch-cluster` were built for one coherent ABI/backend. A CPU smoke can verify
basic tensor/model construction but cannot validate PPI-scale throughput or a
V100 benchmark.

The source's checkpoint loader calls `torch.load` without an explicit
`map_location`. A model state is saved on CPU, but optimizer state in a training
checkpoint may contain device tensors. Test-only loading is safer than CPU
optimizer resume; for a CPU resume, convert the checkpoint in a separate,
caller-controlled step and verify optimizer state placement rather than
silently dropping it.

### Out-of-memory or very slow training

The PPI graphs are large and the default training budget is 2,000 epochs. For a
bounded diagnosis, use an already prepared small fixture or evaluation and
reduce `--batch_size`, `--n_filters`, `--n_blocks`, and (if applicable) GAT
heads. Dense blocks retain concatenated features and can consume more memory
than residual/plain blocks at the same nominal depth. Do not infer benchmark
quality from a reduced run.

`--kernel_size`, `--knn`, `--epsilon`, and `--stochastic` do not reduce PPI
memory in this static architecture: they are parsed but not used by
`DeepGCN`. Dynamic KNN questions belong to `graph-layers`.

## Checkpoint and architecture mismatches

### Missing/unexpected keys or matrix-size errors

Compare the requested model against the logical checkpoint identity:
`block`, `conv`, `n_blocks`, and `n_filters`. Then compare `in_channels`,
`n_heads`, normalization/activation choices, and the dataset-derived class
count. Dense block widths depend on depth and hidden width, so a dense checkpoint
cannot be loaded into a residual/plain model with the same basename fragments.

The PPI loader expects a top-level `state_dict`. A checkpoint from a different
writer may use `model_state_dict`; inspect the payload instead of changing the
loader blindly. Leading `module.` prefixes are normalized for DataParallel
versus single-device models, but that only solves wrapper naming.

Use an absolute, caller-provided checkpoint path to avoid the source parser's
relative-path heuristics. The logical basename should follow:

```text
ppi-{block}-{conv}-{n_blocks}-{n_filters}_{val|test}_best.pth
```

### Training resume starts at the wrong epoch or optimizer fails

`--pretrained_model` sets the model state in both phases. In training, the
source also loads optimizer/scheduler state and uses the checkpoint epoch as
the starting epoch. A test phase resets the reported epoch to `-1`. A checkpoint
without compatible optimizer/scheduler fields can still be useful for
model-only test, but is not a faithful training resume.

## Metric and reporting mistakes

### The run reports `mF1`, but the requested metric is macro F1

Inspect the metric call, not the log spelling. The source calls
`f1_score(..., average="micro")`; it does not compute macro F1. Compute and
label `average="macro"` separately if required, and state whether scores are
aggregated per loader batch or globally over all nodes.

Predictions are `(logits > 0)`, and labels are multilabel indicators. Accuracy,
argmax class IDs, sigmoid probabilities passed directly to
`BCEWithLogitsLoss`, or a multiclass F1 are not equivalent substitutions.

### Validation/test numbers look selected or mislabeled

The source saves both validation-best and test-best checkpoints during training
and later evaluates both on the test loader. Test-best is test-informed. The
post-training message describing a validation-best result is also easy to
misread because it says validation while using `test_loader`. Report the actual
checkpoint and loader split explicitly.

## CLI pitfalls and routing boundaries

- `--phase` has no argparse choices. Any value other than exact `train` takes
  the test branch; use `train` or `test` explicitly.
- `--bias`, `--stochastic`, and `--save_best_only` use `type=bool`. Passing the
  nonempty shell string `False` may parse as true. Prefer the defaults or adapt
  the parser with an explicit boolean parser in caller code.
- `--save_freq`, `--lr_adjust_freq`, `--lr_decay_rate`, `--print_freq`, and
  `--model_name` are accepted but do not control the current PPI loop.
- `--kernel_size`, `--knn`, `--epsilon`, and `--stochastic` are legacy dynamic-
  graph knobs and do not alter this static PPI architecture.
- For generic layer signatures, SAGE/RSAGE compatibility, GAT head constraints,
  or GENConv semantics, route to [graph-layers](../../graph-layers/SKILL.md).
- For OGB `ogbn-proteins`, reversible models, or OGB feature encoders, route to
  [ogb-workflows](../../ogb-workflows/SKILL.md); do not compare its checkpoint
  or metric conventions as if it were PPI.
