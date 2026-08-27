# Trainer and DataLoader API

This reference covers the training surface exposed by the package. It is an
operating guide, not a promise that a default-sized AlphaFold 3 model fits on
the current device.

## Public construction surface

| API | Contract and important defaults | Side effects or cautions |
|---|---|---|
| `Trainer(model, *, dataset, num_train_steps, batch_size, ...)` | Required: model, training dataset, positive step count, and batch size. Useful controls include `grad_accum_every=1`, `valid_dataset=None`, `test_dataset=None`, `valid_every=1000`, `ema_decay=0.999`, `lr=1.8e-3`, `clip_grad_norm=10`, `accelerator='auto'`, `checkpoint_prefix='af3.ckpt.'`, `checkpoint_every=1000`, `checkpoint_folder='./checkpoints'`, `overwrite_checkpoints=False`, `distributed_eval=True`, `fp16=False`, and `use_ema=True`. | Creates Fabric when one is not supplied, calls `fabric.launch()`, sets up model/optimizer/dataloaders, initializes EMA when applicable, and creates the checkpoint folder. Do not use construction as a read-only config check. |
| `DataLoader(dataset, *, atoms_per_window=None, map_input_fn=None, transform_to_atom_inputs=True, **kwargs)` | Wraps PyTorch `DataLoader` with `collate_inputs_to_batched_atom_input`. `atoms_per_window` windowizes full pair features; `map_input_fn` runs before conversion; `transform_to_atom_inputs=False` requires every item already be an `AtomInput`. | A batch can be padded and transformed during iteration. A map function that changes input type or feature dimensions must preserve the model contract. |
| `collate_inputs_to_batched_atom_input(inputs, int_pad_value=-1, atoms_per_window=None, map_input_fn=None, transform_to_atom_inputs=True)` | Converts registered input types to `AtomInput`, windowizes unwindowed atom-pair features, pads tensors to batch maxima, and returns `BatchedAtomInput`. Integer labels default to `-1`, booleans to `False`, and floating values to `0.0` unless a field has a special pad value. | If only some items convert, convertible items may be randomly duplicated to restore the requested batch length. With conversion disabled, mixed input types fail. This is a data-shape concern, not a model-forward choice. |
| `TrainerConfig.create_instance(...)` | Builds a model from its nested `Alphafold3Config`, creates PDB or atom datasets from `DatasetConfig`, optionally creates a weighted sampler, adds a TensorBoard logger, then constructs `Trainer`. A model and/or dataset can instead be injected when the YAML omits them. | Dataset and logger setup happen before `Trainer`; directory/file checks and dataset loading are real work. A caller-provided dataset conflicts with a corresponding YAML dataset source. |
| `create_trainer_from_yaml(path, dotpath=[], **kwargs)` | Selects one mapping from a YAML document and delegates to `TrainerConfig`. `dotpath` may be a dotted string or list of keys. | The factory constructs a trainer and therefore launches Fabric and creates checkpoint directories. Use the bundled validator for inspection. |
| `ConductorConfig.create_instance(trainer_name, **kwargs)` | Selects one named phase, shares the root model, nests the phase checkpoint folder below the root folder, and prefixes the phase checkpoint prefix with the root prefix. | The phase name must be in `training`. The factory mutates the selected `TrainerConfig`'s checkpoint folder/prefix in memory. Validate order and effective namespaces before constructing. |
| `create_trainer_from_conductor_yaml(path, dotpath=[], trainer_name=..., **kwargs)` | Parses a conductor document and constructs the selected phase only. | It does not run all phases automatically; orchestration of phase order remains the caller's responsibility. |

`create_alphafold3_from_yaml` is the model-only factory. Model architecture,
forward modes, and tensor dimensions belong to `model-inference`; this skill
only validates the model configuration needed by a trainer.

## Trainer lifecycle

A normal bounded run has this shape:

1. Build or load the model and choose datasets that return `PDBInput` or
   `AtomInput` (or another registered input that converts to `AtomInput`).
2. Decide whether to supply a custom Fabric, optimizer, scheduler, sampler, or
   input mapping function. Keep injected objects out of YAML; YAML factories
   only describe serializable configuration.
3. Construct `Trainer` with a deliberately small `num_train_steps`, batch,
   crop/input size, validation cadence, and checkpoint cadence.
4. Fabric sets up the model and optimizer and wraps the dataloaders. The train
   loop collates batches, calls the model with `return_loss_breakdown=True`,
   accumulates gradients, clips gradients, steps the optimizer/scheduler, and
   updates EMA.
5. At `valid_every` steps, validation uses the EMA model when present. Test
   evaluation runs after the training loop when a test dataset is supplied.
6. Main rank saves a checkpoint at `checkpoint_every` steps. The loop prints
   loss summaries and writes dictionaries through Fabric loggers.

`grad_accum_every` divides each loss/backward contribution and delays the
optimizer step until all accumulation iterations finish. It increases compute
per optimizer step without changing the dataloader batch size. Keep the
product of batch size and accumulation explicit in the resource plan.

## Dataset and collation contract

`DatasetConfig.dataset_type` chooses `PDBDataset` (`'pdb'`) or `AtomDataset`
(`'atom'`). The training folder is required; validation and test folders are
optional. PDB datasets may be converted to on-disk atom inputs through
`convert_pdb_to_atom=True`, but that conversion is preprocessing and can be
expensive or mutating. `train_weighted_sampler` is only meaningful for a PDB
training dataset and is created with the trainer batch size.

The wrapped loader passes `atoms_per_window=model.atoms_per_window` when used
by `Trainer`. Consequently, all examples in a batch must be collatable after
input conversion, with compatible feature depths and label semantics. Missing
optional tensors are represented by field defaults during collation; this does
not repair inconsistent model dimensions. See
[`configuration.md`](configuration.md) for YAML keys and
[`troubleshooting.md`](troubleshooting.md) for mixed-batch failures.

## Optimizer, scheduler, and EMA

If no optimizer is injected, `Trainer` uses Adam with the configured `lr`,
`default_adam_kwargs`, and a warmup/decay lambda scheduler unless a scheduler
is injected. At most one of `use_adam_atan2`, `use_adopt_atan2`, and
`use_lion` may be true. Those alternate optimizers remove the Adam `eps`
keyword from the default kwargs. If the model is compiled, the source requires
runtime type checking to be disabled before construction; this is not a safe
first diagnostic.

EMA is enabled by default, but is only materialized when evaluation is enabled
on the relevant rank or switch-EMA behavior is requested. `ema_on_cpu=True`
trades device memory for host transfers. `ema_kwargs` must match the installed
`ema_pytorch` version. For a tiny CPU check, disabling EMA is a valid way to
separate model/data correctness from EMA memory and dependency issues; do not
interpret it as production-equivalent validation.

## Fabric, precision, and evaluation

`accelerator='auto'` delegates selection to Lightning Fabric. Use an explicit
`'cpu'`, `'cuda'`, or supported accelerator name in a bounded plan when
reproducibility matters. `fp16=True` injects Fabric precision `'16-mixed'` and
must not be combined with a `fabric_kwargs.precision` value. If a custom Fabric
is supplied, the caller owns its launch/setup semantics.

With `distributed_eval=True`, validation/test dataloaders are set up on all
ranks and reduced through Fabric. With it disabled, the implementation tracks
evaluation on the main rank to avoid every rank maintaining evaluation state.
The appropriate setting depends on distributed dataset visibility and EMA
placement; it is not a substitute for checking rank/device behavior.

When `use_tensorboard=True` in `TrainerConfig`, a
`TensorBoardLogger(tensorboard_log_dir, **logger_kwargs)` is added. The logger
is created during factory construction. Confirm that TensorBoard is installed,
that the log directory is writable, and that the run's logging volume is
bounded before constructing the trainer.

## Checkpoint API

- `trainer.save(path, overwrite=False)` writes model initialization metadata,
  optimizer and scheduler state, step count, and train ID. It refuses to
  replace an existing path unless `overwrite=True`.
- `trainer.save_checkpoint()` creates a generated filename containing the
  train ID, configured prefix, and current step, and uses
  `overwrite_checkpoints`.
- `trainer.load(path, strict=True, prefix=None, only_model=False,
  reset_steps=False)` accepts a file or a directory. A directory selects the
  latest matching checkpoint by the numeric step in the filename. `only_model`
  leaves optimizer/scheduler and step state untouched; `reset_steps` resets the
  loaded step counter when full state is loaded.
- `trainer.load_from_checkpoint_folder(**kwargs)` is a convenience wrapper.

Checkpoint files contain optimizer state and can be substantially larger than
model weights. A resume plan should name the exact file or a unique directory
and decide whether optimizer/scheduler/step state is wanted. Use
`overwrite_checkpoints=False` unless replacement has been explicitly approved;
validation should warn, not silently normalize, an overwrite request.
