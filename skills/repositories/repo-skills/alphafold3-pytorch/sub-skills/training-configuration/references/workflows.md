# Training configuration workflows

These workflows are intentionally staged so that configuration inspection is
separate from Fabric launch, dataset reads, checkpoint writes, and training.
Use a small model, a tiny finite dataset, and a short step budget for any
runtime smoke check.

## 1. Read-only YAML preflight

1. Identify whether the document is a model, trainer, or conductor mapping.
2. If it is nested, select the exact dotpath (for example `training.main`).
3. Run:

   ```bash
   python scripts/validate_config.py --help
   python scripts/validate_config.py path/to/config.yaml --kind auto
   ```

4. For a nested mapping, add `--dotpath model` or
   `--dotpath training.main` as appropriate. Use `--json` when another tool
   needs machine-readable errors and warnings.
5. Resolve model-required-field errors, missing `DirectoryPath`/`FilePath`
   values, invalid dataset choices, order mismatches, factory-conflicting
   dataset sources, and unsafe checkpoint warnings before constructing
   anything.

The helper imports the config models only for validation; it never invokes a
factory, constructs `Trainer`/`Fabric`, creates directories, reads dataset
records, or loads checkpoints.

## 2. Bounded direct Trainer diagnostic

Use this only after the YAML or direct arguments have been preflighted.

1. Choose a reduced model whose atom/input/pair/template dimensions agree with
   the dataset. The model-inference skill owns the reduced-model contract.
2. Use a small in-memory or already prepared local dataset. A dataset item must
   be an `AtomInput` or a registered input type that can become one.
3. Construct the exported `DataLoader` first with `batch_size=1` or another
   explicitly bounded value. Inspect one collated batch and confirm padding,
   windowing, optional masks, labels, and feature depths.
4. Construct `Trainer` with `accelerator='cpu'` or an explicitly verified
   accelerator, `num_train_steps` of one or a few, `valid_every=1` only when a
   tiny validation set is supplied, and `checkpoint_every=1` only in a disposable
   approved output namespace.
5. Prefer `use_ema=False` for a first data/model wiring check, then test EMA as
   a separate bounded concern. Keep `fp16=False` until Fabric/device support is
   confirmed.
6. If the step succeeds, inspect the loss breakdown, optimizer/scheduler step,
   and checkpoint path. This is a wiring diagnostic, not a quality or throughput
   claim.

Remember that constructing the trainer launches Fabric and creates its
checkpoint folder. A failed construction may still have initialized a logger,
process group, or directory; use a dedicated approved output namespace.

## 3. YAML trainer with a dataset source

A serializable trainer document can carry a model mapping and a
`dataset_config`:

```yaml
model:
  dim_atom_inputs: 3
  dim_template_feats: 108
  dim_template_model: 8
  atoms_per_window: 27
  dim_atom: 4
  dim_atompair_inputs: 5
  dim_atompair: 4
  dim_input_embedder_token: 4
  dim_single: 4
  dim_pairwise: 4
  dim_token: 4
  num_dist_bins: null
  num_plddt_bins: 50
  num_pde_bins: 64
  num_pae_bins: 64
  sigma_data: 16
  diffusion_num_augmentations: 4
  loss_confidence_weight: 0.0001
  loss_distogram_weight: 0.01
  loss_diffusion_weight: 4.0
num_train_steps: 2
batch_size: 1
grad_accum_every: 1
valid_every: 1
ema_decay: 0.999
lr: 0.0001
clip_grad_norm: 10.0
accelerator: cpu
checkpoint_prefix: smoke.ckpt.
checkpoint_every: 1
checkpoint_folder: ./approved-smoke-checkpoints
overwrite_checkpoints: false
use_ema: false
dataset_config:
  dataset_type: atom
  train_folder: ./prepared-atom-inputs
```

The example is a pattern, not a promise that the folders exist or that a
small model is biologically meaningful. `dataset_type: pdb` instead selects
`PDBDataset`; add valid/test folders only when they are prepared and part of
this run. Use `convert_pdb_to_atom` only with an explicit storage and mutation
plan because conversion writes atom-input files.

## 4. Conductor multi-phase preflight and selection

For a conductor:

1. Validate the root mapping with `--kind conductor`.
2. Confirm every name in `training_order` occurs exactly once in practice and
   every key in `training` occurs in the order. Validate each phase with
   `--dotpath training.<name>` as a trainer mapping.
3. Compare each phase's effective checkpoint namespace:
   `root.checkpoint_folder / phase.checkpoint_folder` and
   `root.checkpoint_prefix + phase.checkpoint_prefix`.
4. Select one phase explicitly when constructing it. The convenience factory
   creates that phase; it does not automatically execute the full order.
5. For fine-tuning, decide whether to load model-only state or the full
   optimizer/scheduler/step state before starting the next phase. A phase's
   injected dataset may be different, but model dimensions and feature
   contracts must remain compatible.

A useful synthetic check is a three-phase conductor in which the second phase
inherits the root model but overrides `lr`, `dataset_config`, and checkpoint
prefix. The expected result is a distinct effective checkpoint namespace and a
clear record of which values are inherited versus overridden.

## 5. DataLoader and collation check

Use the standalone `DataLoader` or collation function when the question is
batch shape rather than optimization:

1. Select two or three tiny examples with intentionally different atom/token
   lengths and with one optional MSA/template field absent.
2. Run `collate_inputs_to_batched_atom_input` with the target
   `atoms_per_window`. Confirm the atompair representation is windowed once,
   integer labels use the expected pad value, and the output is a
   `BatchedAtomInput`.
3. Try `transform_to_atom_inputs=False` only when all examples are already
   `AtomInput` objects. Otherwise leave conversion enabled or provide a
   `map_input_fn` that returns a registered input type.
4. Pass the collated batch to a reduced model only in the model-inference
   workflow. Do not use a training call to debug an input representation.

Mixed PDB/atom examples, unequal optional fields, and a map function that
returns `None` are useful synthetic cases because they expose errors hidden by
uniform examples.

## 6. Checkpoint and resume plan

Before a run, record:

- the exact model initialization/checkpoint source;
- the checkpoint folder and prefix namespace;
- whether `overwrite_checkpoints` is false;
- the save cadence and maximum expected number of files;
- whether resume should restore optimizer, scheduler, and step state; and
- whether a model-only load is needed for fine-tuning.

During a bounded run, prefer a new namespace. Directory loading selects the
latest matching file by the numeric step in its filename, so a shared folder
with ambiguous prefixes is unsafe. `trainer.save(path)` refuses an existing
file unless its own `overwrite=True` argument is used; generated periodic
saves use the trainer's `overwrite_checkpoints` setting.

## 7. Fabric, precision, logging, and distributed evaluation

Use an explicit matrix rather than changing several controls at once:

| Diagnostic | Accelerator | Precision | EMA | Distributed eval | Purpose |
|---|---|---|---|---|---|
| CPU wiring | `cpu` | full precision | off | off | isolate collation/model/data wiring |
| EMA wiring | `cpu` | full precision | on | off | exercise EMA state without GPU pressure |
| accelerator check | verified target | full precision | off | as planned | prove Fabric device setup |
| mixed precision check | verified CUDA/other backend | `fp16=True` | off | as planned | prove precision configuration separately |
| distributed evaluation | verified multi-process setup | as planned | as planned | on | prove reduction and dataset visibility |

`fp16=True` maps to Fabric `'16-mixed'`; do not also pass a precision value in
`fabric_kwargs`. TensorBoard is enabled by default in `TrainerConfig`, so turn
it off or set an approved log directory for a diagnostic if logging is not part
of the question. Do not launch a distributed job merely to validate a YAML
shape.

## 8. Full-training resource gate

Before moving beyond a bounded check, estimate model memory, atom/token length,
MSA/template counts, diffusion augmentations, gradient accumulation, batch
size, validation/test frequency, EMA device placement, checkpoint storage, and
logger volume. Stop if the plan requires dataset-scale conversion, network
acquisition, an unverified accelerator, production defaults on CPU, or a
checkpoint namespace that may replace existing files. The training skill can
explain the plan; it does not make those resource or safety decisions silently.
