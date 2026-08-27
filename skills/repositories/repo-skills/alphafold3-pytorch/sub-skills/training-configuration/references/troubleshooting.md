# Training configuration troubleshooting

Use the validator before reproducing a failure. Separate parse/Pydantic
errors from factory side effects, dataset reads, Fabric setup, and model
forward failures. The recovery actions below are deliberately bounded.

## Configuration and dotpaths

| Symptom | Likely cause | Recovery |
|---|---|---|
| YAML is empty, a scalar, or a list | The selected document is not a mapping. | Fix the YAML shape or select a mapping-valued dotpath. Do not pass a list index; `safe_deep_get` only walks dictionary keys. |
| Required model dimension is missing | `Alphafold3Config` has mandatory dimensions/bin/loss fields, even though the model class has broader defaults. | Add the required fields to the selected `model` mapping. For a trainer, either include a valid nested model or deliberately inject a model object at the factory call. |
| A trainer without `model` validates but factory construction asserts | `TrainerConfig.model` is optional to support injected models; YAML alone cannot supply the object. | Treat the validator warning as an intentional injection requirement. Do not call the YAML factory without `model=...`. |
| `config not found at path ...` | A dotpath segment is absent or points through a non-mapping. | Run the validator with the exact path, inspect the selected root, and use `training.<phase>` for a conductor phase. |
| Model fields contain a typo but validation succeeds | Config classes use Pydantic `extra='allow'`. | Remove or explicitly justify the extra. Confirm it is accepted by the eventual model constructor; acceptance by Pydantic alone is not enough. |
| Trainer field contains a typo and factory later raises `TypeError` | Trainer extras are allowed, then forwarded by `TrainerConfig.create_instance`; arbitrary extras are not valid Trainer keywords. | Compare extras with the installed Trainer signature and remove unsupported keys. |
| A duplicate YAML key gives a surprising value | YAML loaders generally retain the last value for a duplicate mapping key. | Make keys unique, especially `num_dist_bins`, dimensions, checkpoint paths, and phase names. |

## Dataset source and collation conflicts

| Symptom | Likely cause | Recovery |
|---|---|---|
| `dataset_type` is rejected | Only `'pdb'` and `'atom'` are supported by `DatasetConfig`. | Choose the correct dataset class; route other data preparation to `data-pipeline`. |
| `train_folder`/mapping file fails `DirectoryPath`/`FilePath` validation | Package validation checks existence at validation time and interprets relative paths from the process working directory. | Use an existing approved directory/file, run from the intended path base, or treat the result as an unverified layout. Do not create directories just to make validation pass. |
| `convert_pdb_to_atom` fails at trainer construction | Conversion is enabled with `dataset_type: atom`, or the PDB dataset/kwargs are not prepared. | Use `convert_pdb_to_atom` only for a PDB dataset and plan output storage, workers, and overwrite behavior explicitly. |
| Factory asserts that a dataset is already present | YAML has `dataset_config.train_folder` and the caller also injected `dataset=...`; the same can happen for valid/test. | Choose one source. For a quick in-memory diagnostic, omit `dataset_config`; for a reproducible run, keep dataset construction in YAML and do not inject the object. |
| Batch contains incompatible feature depths or shapes | Inputs converted to `AtomInput` do not agree, or a map function changes the contract. | Collate a tiny heterogeneous batch first, inspect `BatchedAtomInput`, and route feature/input semantics to `input-representation` or `model-inference` as appropriate. |
| `transform_to_atom_inputs=False` raises | At least one item is not already an `AtomInput`. | Enable conversion or normalize every dataset item before collation. Do not silence the assertion with a mixed batch. |
| Optional fields are unexpectedly padded | Collation fills absent fields with field-specific defaults, integer `-1`, boolean `False`, or floating `0.0`. | Confirm the model treats those masks/labels as padding and that the batch contains the required training labels. |
| Weighted sampler is slow, empty, or has a probability error | CSV mappings are missing/incompatible, the filtered set has no rows, or the sampler's precomputation is being run as a smoke check. | Validate file existence and mapping schema separately; use a tiny approved subset only for sampler wiring. Keep dataset-scale clustering/curation in `data-pipeline`. |

## Conductor phases

| Symptom | Likely cause | Recovery |
|---|---|---|
| Conductor validation says phase names differ | `training_order` and `training` keys are not the same set. | Add every phase exactly once to the order and remove stale phase mappings. Also reject duplicate names in the order even though set equality alone would miss them. |
| A phase cannot be selected | The requested `trainer_name` is absent. | Validate `training.<name>` and select an exact key; the factory does not infer aliases. |
| Phase checkpoints collide | Two phases compose to the same root-folder/phase-folder and root-prefix/phase-prefix pair, or a phase reuses an unsafe namespace. | Give each phase a distinct folder and prefix, keep overwrite disabled, and validate effective names before construction. |
| A later phase unexpectedly uses a modified checkpoint path | Conductor construction nests and prefixes the selected `TrainerConfig` in memory. | Treat parsed config objects as single-use for construction, or reload/copy them before selecting another phase. Record inherited root settings separately from phase overrides. |
| A phase with its own dataset conflicts with an injected dataset | The same source exclusivity rule applies inside each nested `TrainerConfig`. | Either retain the phase `dataset_config` or inject the phase dataset, not both. |

## Checkpoints and overwrite safety

| Symptom | Likely cause | Recovery |
|---|---|---|
| Periodic save refuses an existing file | `overwrite_checkpoints=False` or the explicit `save(..., overwrite=False)` guard found a path collision. | Use a new approved namespace or inspect the existing checkpoint. Enable overwrite only after explicit approval and a backup/retention decision. |
| Validator warns about unsafe overwrite | `overwrite_checkpoints: true` allows generated periodic saves to replace a same-named file. | Prefer `false` for diagnostics and production; if true is intentional, document the namespace, retention, and collision reason. The validator does not change the value. |
| Loading a folder chooses the wrong checkpoint | Directory loading matches files by prefix and sorts the numeric step extracted from names. | Supply the exact file or a unique prefix/folder. Do not rely on a shared folder with mixed experiments. |
| Resume changes or loses optimizer progress | `only_model=True` skips optimizer/scheduler restoration; `reset_steps=True` resets the step count. | Decide explicitly between model-only fine-tuning and full-state resume, then inspect `steps`, optimizer, and scheduler state. |
| A checkpoint is too large | Full trainer saves include model initialization metadata, optimizer, scheduler, step, and train ID. | Reduce checkpoint frequency only after defining recovery needs; keep model-only artifacts separate from full resume artifacts. |

## EMA, optimizer, and scheduler

| Symptom | Likely cause | Recovery |
|---|---|---|
| Optimizer selection asserts | More than one of `use_adam_atan2`, `use_adopt_atan2`, and `use_lion` is true. | Select one optimizer family or none for default Adam. Do not combine alternate flags. |
| Alternate optimizer rejects `eps` | The trainer removes `eps` for Adam-Atan2, Adopt-Atan2, and Lion; a custom kwargs dict may not match the installed optimizer. | Start with documented defaults, then verify the installed optimizer signature in a separate inspection step. |
| EMA consumes too much device memory or changes evaluation behavior | EMA is enabled by default and may be placed on the training device; validation/test uses EMA when available. | Disable EMA for a wiring check, or use `ema_on_cpu=True` with an explicit transfer-cost plan. Do not compare a no-EMA smoke loss to production quality. |
| EMA keyword is rejected | `ema_kwargs` is passed to the installed `ema_pytorch.EMA` implementation. | Check the installed EMA signature and remove unsupported options; keep the first run on default kwargs. |
| Learning rate starts at zero | The default lambda scheduler warms up over 1000 steps. | Expect the schedule, or inject a deliberate scheduler for a controlled experiment; do not mistake warmup for a dead optimizer. |
| No optimizer step occurs | `grad_accum_every` is zero/invalid or the run ends before a complete accumulation cycle. | Keep accumulation a positive integer and make the step budget large enough for the intended diagnostic. |

## Fabric, precision, and logging

| Symptom | Likely cause | Recovery |
|---|---|---|
| Fabric cannot select the accelerator | `'auto'` chose an unavailable backend or an explicit accelerator is not installed. | Start with `accelerator='cpu'`; inspect available hardware/dependencies, then retry a small check with one explicit verified backend. |
| `fp16` conflicts with Fabric kwargs | `fp16=True` injects `precision='16-mixed'`, while `fabric_kwargs` already contains `precision`. | Set precision in exactly one place. Confirm the device supports the selected mixed-precision mode. |
| Construction hangs or spawns unexpected processes | Fabric launch/distributed configuration is being exercised during construction. | Return to read-only validation or a single-process CPU check; inspect launcher/environment settings before retrying. |
| TensorBoard logger fails | TensorBoard is missing, the log path is unwritable, or logger kwargs are incompatible. | Set `use_tensorboard: false` for a wiring-only check or choose an approved writable log directory and verify the installed logger signature. |
| Validation/test results differ across ranks | `distributed_eval` and dataset visibility do not match the process layout, or EMA exists only on selected ranks. | Use `distributed_eval=False` for a main-rank diagnostic, or verify Fabric dataloader setup and reduction on a deliberately configured distributed run. |
| `use_torch_compile` fails immediately | The implementation requires runtime type checking to be disabled for compilation. | Treat compilation as an advanced, separately verified optimization; do not enable it in the first configuration check. |

## Resource stop conditions

Stop rather than “trying once” when any of these is true:

- a production-sized model, sequence, MSA/template bank, or diffusion
  augmentation count is being used for a CPU smoke check;
- a PDB-to-atom conversion or weighted sampler would process an unbounded data
  directory;
- checkpoint overwrite is enabled without a unique namespace and retention
  decision;
- the requested accelerator, mixed precision, distributed evaluation, logger,
  or optional optimizer is not verified;
- the run has no finite `num_train_steps`, batch, accumulation, validation, and
  checkpoint budget; or
- the failure is actually an input-feature or forward-shape problem owned by a
  sibling sub-skill.

A bounded configuration diagnostic can establish parse/type/cross-field and
wiring facts. It cannot establish biological quality, production throughput,
or full-dataset coverage.
