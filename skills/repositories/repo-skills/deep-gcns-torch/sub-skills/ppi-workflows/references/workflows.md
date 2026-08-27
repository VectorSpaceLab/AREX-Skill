# PPI workflow reference

This reference records the source example's operating contract. It is not a
training script and it does not authorize network access. Substitute a caller-
provided, already prepared data root and checkpoint; never use the workflow to
trigger the PyG PPI download or to retrieve a checkpoint from an external drive.

## Task and data root

The task is multilabel node classification on the PyG `PPI` dataset. The
example constructs three dataset objects with `split='train'`, `split='val'`,
and `split='test'`, all rooted at `--data_dir`. The parser default is
`/data/deepgcn/ppi`, but a portable invocation should always pass an explicit
caller-owned local root.

Use these neutral invocation shapes with a caller-supplied entry point and
already staged local inputs. Replace `<ppi-entrypoint>` and the angle-bracket
placeholders; these commands do not name or depend on an original checkout.
The original source example is evidence only and must not be opened or run as a
runtime prerequisite.

```bash
# Train the source-observed default configuration on a prepared local dataset.
python -u <ppi-entrypoint> --phase train --data_dir <prepared-ppi-root>

# Train a documented alternative: EdgeConv, dense blocks, 28 blocks, 256 filters.
python -u <ppi-entrypoint> --phase train \
  --conv edge --data_dir <prepared-ppi-root> \
  --block dense --n_filters 256 --n_blocks 28

# Test a residual MR checkpoint; every architecture identity flag must agree.
python -u <ppi-entrypoint> --phase test \
  --pretrained_model <ppi-res-mr-28-256_val_best.pth> \
  --data_dir <prepared-ppi-root> \
  --n_filters 256 --n_blocks 28 --conv mr --block res

# Test a dense MR checkpoint.
python -u <ppi-entrypoint> --phase test \
  --pretrained_model <ppi-dense-mr-14-256_val_best.pth> \
  --data_dir <prepared-ppi-root> \
  --n_filters 256 --n_blocks 14 --conv mr --block dense
```

These are caller-adaptable command shapes, not bundled scripts. The checkpoint
basenames remain source-observed architecture recipes; use a caller-owned
checkpoint path whose tensors have been verified against the requested model.

## Architecture choices

The model is a static sparse DeepGCN-style network:

1. A head `GraphConv(50, n_filters, conv, act, norm, bias, n_heads)` maps the
   input features to the deep width.
2. `n_blocks - 1` static blocks consume the same `edge_index`.
3. `block=res` uses residual blocks with residual scale 1.
4. `block=plain` uses the same block implementation with residual scale 0;
   it is the non-residual/plain behavior, not a separate dynamic KNN path.
5. `block=dense` concatenates each new block output with all preceding features,
   so the feature width grows with depth.
6. A fusion MLP and prediction MLP produce one logit vector per node.

The README-facing convolution choices are:

| Flag | Meaning and routing |
|---|---|
| `--conv edge` | EdgeConv-style static layer; route layer construction to `graph-layers`. |
| `--conv mr` | MRConv-style static layer; route layer construction to `graph-layers`. |
| `--conv gin` | GIN-style static layer; route layer construction to `graph-layers`. |
| `--conv gcn` | GCN-style static layer; route layer construction to `graph-layers`. |
| `--conv gat` | GAT-style static layer; `n_filters` should be divisible by `n_heads`. |
| `--conv sage` | Source-recognized SAGE path, but the inspected modern PyG environment has an `RSAGEConv` compatibility failure; do not present it as a verified current-backend route. |

The implementation also recognizes `rsage`, although it is absent from the
README help text and is not a portable recommendation. Generic constructor
signatures, aggregation semantics, KNN, and backend compatibility belong in
the `graph-layers` skill rather than here.

Other architecture flags are:

- `--n_filters` is the hidden width and defaults to `256` in the parser.
- `--n_blocks` is the number of basic blocks and defaults to `14`.
- `--in_channels` defaults to `50` and must match `data.x.shape[1]`.
- `--act` accepts the source's `relu`, `prelu`, or `leakyrelu` choices.
- `--norm` accepts `batch` or `instance` in the parser.
- `--bias` is passed to the graph layers and MLPs.
- `--n_heads` controls GAT heads and defaults to `1`.
- `--dropout` controls the prediction MLP dropout and defaults to `0.2`.

The README describes the default residual MR model as 14 layers with 64
filters, while the current parser sets `n_filters=256`, `n_blocks=14`,
`block=res`, and `conv=mr`. To reproduce the 64-filter description, pass
`--n_filters 64` explicitly; otherwise trust the parser values.

## Exact parser flags

`OptInit` accepts the following flags. Values in braces describe source
behavior, not an enforced `argparse` choice list.

### Phase, device, and dataset

| Flag | Default | Use |
|---|---:|---|
| `--phase` | `test` | The code treats exactly `train` as training and all other values as test; use only `train` or `test`. |
| `--use_cpu` | off | Force `torch.device('cpu')`; otherwise use CUDA when available and CPU as fallback. |
| `--data_dir` | `/data/deepgcn/ppi` | Root passed to all PyG PPI split objects. It must already contain the required data for an offline run. |
| `--batch_size` | `1` | PyG graph batch size. The help text says 8, but the parsed default is 1. |
| `--in_channels` | `50` | Input feature width; must match the prepared PPI tensors. |

### Training and resume

| Flag | Default | Use |
|---|---:|---|
| `--total_epochs` | `2000` | Training loop limit. This is a long run, not a safe smoke. |
| `--save_freq` | `10` | Parsed but not consulted by the current PPI loop. Best checkpoints are saved when validation/test score improves. |
| `--iter` | `-1` | Initial iteration counter; incremented per training loader batch. |
| `--lr_adjust_freq` | `20` | Parsed but not consulted. |
| `--lr_patience` | `100` | Patience passed to `ReduceLROnPlateau`. |
| `--lr` | `2e-3` | Adam learning rate; resumed scheduler state may replace it. |
| `--lr_decay_rate` | `0.8` | Parsed but not consulted; the scheduler uses a hard-coded factor of `0.5`. |
| `--print_freq` | `10` | Parsed but not consulted by the current loop. |
| `--postname` | empty | Appended to the logical run name and checkpoint basename. |
| `--multi_gpus` | off | Uses `DataListLoader` for training and PyG `DataParallel`; see loader caveat below. |
| `--pretrained_model` | empty | Load a model checkpoint; in training, also attempts optimizer/scheduler resume. |

### Model and saving

| Flag | Default | Use |
|---|---:|---|
| `--model_name` | empty | Parsed but not used by the PPI model. |
| `--kernel_size` | `20` | Parsed but unused because PPI uses static `GraphConv` with supplied edges. |
| `--block` | `res` | `res`, `plain`, or `dense`; see architecture choices. |
| `--act` | `relu` | Activation passed into graph layers/MLPs. |
| `--norm` | `batch` | Normalization passed into graph layers/MLPs. |
| `--knn` | `tree` | Parsed but unused by the static PPI architecture. |
| `--bias` | `True` | Boolean passed into layers; it uses `type=bool`, so shell text such as `False` is not a reliable false value. |
| `--n_filters` | `256` | Hidden feature width. |
| `--n_blocks` | `14` | Number of basic blocks. |
| `--dropout` | `0.2` | Prediction-head dropout probability. |
| `--conv` | `mr` | `edge`, `mr`, `sage`, `gin`, `gcn`, or `gat` in the public recipe; see compatibility notes. |
| `--n_heads` | `1` | GAT head count; use a divisor of `n_filters`. |
| `--epsilon` | `0.2` | Parsed but unused by this static PPI model. |
| `--stochastic` | `True` | Parsed but unused by this static PPI model; it also uses `type=bool`. |
| `--ckpt_path` | empty | Changes the save root; the source appends `checkpoints/ckpts-...` below it. |
| `--save_best_only` | `True` | Parsed but not consulted; current code always writes validation-best and test-best files when improved. |

There is no `--n_classes` flag. The model reads `test_loader.dataset.num_classes`
before construction. Changing label width or loading a checkpoint from a
nonmatching task therefore causes a prediction-head shape mismatch.

## Loader and device behavior

Without `--multi_gpus`, the source uses a PyG `DataLoader` for train, validation,
and test. `DataLoader` collates multiple PPI graphs into one batch with a
node-level `batch` vector; the model still operates on the concatenated
`x`, `edge_index`, and `y` tensors.

With `--multi_gpus`, training uses `DataListLoader`, and the model is wrapped
with PyG `DataParallel`. The training step concatenates `y` from the list for
the loss/metric, while PyG DataParallel scatters graph objects to replicas.
Validation and test loaders are still built as ordinary `DataLoader` objects in
the source, and `test()` calls `data.to(device)`. Treat this as a source-era
asymmetry: verify the installed PyG version and adapt the evaluation loader
before relying on multi-GPU evaluation. Modern PyG exposes the loaders under
`torch_geometric.loader`, while the source imports deprecated compatibility
aliases from `torch_geometric.data`.

## Training and evaluation semantics

Training uses `BCEWithLogitsLoss`, Adam, and `ReduceLROnPlateau` stepped on the
average training loss after each epoch. The loop computes train, validation,
and test micro F1 each epoch. It writes a validation-best checkpoint whenever
validation micro F1 improves and a test-best checkpoint whenever test micro F1
improves. Selecting a test-best model is useful as a source diagnostic but is
test-set selection and should not be reported as an unbiased held-out result.

After training, the source loads the validation-best and test-best checkpoints
and evaluates each on the test loader. One log message calls the first result
"the model on validation dataset", although the loader used is the test loader;
interpret the numeric result by the actual loader, not by that label.

## Checkpoint naming and output paths

The logical name is assembled as:

```text
ppi-{block}-{conv}-{n_blocks}-{n_filters}[-{postname}]
```

The default save path is a dated directory under the PPI example's checkpoint
area, named conceptually `ckpts-{logical-name}-{YYMMDD}`. If `--ckpt_path` is
set, the source appends `checkpoints/ckpts-{logical-name}-{YYMMDD}` below that
root. The two best files are:

```text
{logical-name}_val_best.pth
{logical-name}_test_best.pth
```

A documented pretrained basename such as
`ppi-res-mr-28-256_val_best.pth` communicates the task, block, convolution,
block count, and filter width. It does not encode `in_channels`, `n_heads`,
activation, normalization, dropout, or label count; verify those separately.

The PPI main module's writer stores `epoch`, `state_dict`,
`optimizer_state_dict`, and `scheduler_state_dict`. Its loader expects the
`state_dict` key and normalizes a leading `module.` prefix when the saved and
current DataParallel modes differ. Do not substitute a checkpoint written by a
different utility merely because it is also a `.pth` file: another repository
utility uses `model_state_dict`, which the PPI loader does not read.
