# Training and fine-tuning troubleshooting

Diagnose the earliest failing layer. Do not turn an import, config, or dataset
error into a full training trial.

## Install and import failures

**Symptoms:** `mattergen-train` or `mattergen-finetune` is not found,
`ModuleNotFoundError`, or an extension import fails.

- Confirm the active environment and `python --version` (the inspected package
  targets Python 3.10).
- Verify the installed package is MatterGen 1.0.3 and that the console entry
  points resolve to `mattergen.scripts.run:mattergen_main` and
  `mattergen.scripts.finetune:mattergen_finetune`.
- Check the backend-aware PyTorch Geometric extension set together: torch,
  `torch_geometric`, `torch_cluster`, `torch_scatter`, and `torch_sparse` must
  be compatible with the selected CPU/CUDA platform. The inspected environment
  had torch 2.2.1+cu118, torch_geometric 2.8.0.post1, CUDA extension wheels,
  and the other documented dependencies, but do not copy that environment as
  a requirement for every machine.
- Run console `--help`/import probes rather than training. If the error is only
  a missing optional logger, keep `~trainer.logger` for a local no-W&B run.
- On MPS, set `PYTORCH_ENABLE_MPS_FALLBACK=1` as README instructs and remove
  the default DDP strategy. MPS behavior still needs target-device validation.

## Hydra and override failures

**Symptoms:** `LexerNoViableAltException`, `ConfigCompositionException`,
`KeyError`, an override is ignored, or the preflight reports an error.

- Use `key=value` for existing fields, `+key=value` for a new mapping/group,
  and `~key` to delete an existing node such as `~trainer.logger`.
- Quote list/dict values and property-embedding group overrides in the shell.
  Verify shell variables expanded to non-empty names.
- Use `--config-name=csp` only with the training root config. A sampler's
  `--sampling-config-name=csp` is a separate command-line option.
- For an adapter property, preserve the full destination:
  `...property_embeddings@adapter.adapter.property_embeddings_adapt.<p>=<p>`.
  The base-model destination is different.
- Do not use `+` to add a field that already exists if Hydra should update it;
  use a normal assignment for existing values.
- Run the bundled parser with `--config-root <mattergen-config-root>`. It is
  deliberately conservative and cannot prove all Hydra interpolation; a pass
  is necessary, not sufficient. Use the installed package resource or an
  explicit user-controlled config copy, not a source-checkout path.

## Data and property validation failures

**Symptoms:** missing `pos.npy`, `dft_*.json`, `Property ... is not valid`,
length assertions, or empty/filtered batches.

- Confirm the selected `data_module` matches the cache dataset name and
  `data_module.root_dir` resolves to the cache's `train`, `val`, and optional
  `test` directories.
- Confirm preprocessing completed and each expected split has core arrays.
- Confirm every requested property has a JSON cache file with one entry per
  structure. The loader reports available property filenames when one is absent.
- For a new property, update the source allow-list, regenerate cache, and add
  an embedding YAML. A CLI override alone cannot register a new source id.
- Check units, missing values, and categorical representation. Sparse labels
  are filtered and, for joint multi-property conditioning with the default
  embedding dropout mode, missing one field prevents the joint conditional
  state for that sample.
- If the property exists in the source allow-list but not the selected data
  module's documented list, treat availability as unverified until the cache
  is inspected.

## Checkpoint and adapter failures

**Symptoms:** no checkpoint found, no `last.ckpt`, `Epoch ... not found`,
strict state-dict mismatch, or a duplicate adapter condition assertion.

- `adapter.pretrained_name` resolves a published model via the Hugging Face
  checkpoint metadata. It needs network/cache access; use `adapter.model_path`
  for a local output.
- A local path must contain the config and recursively discoverable `.ckpt`
  files. `load_epoch=last` requires `last.ckpt`; `best` selects the lowest
  validation-loss filename; an integer needs a matching epoch filename.
- Do not supply both source selectors. If both appear, the source code warns
  and ignores `pretrained_name` in favor of `model_path`.
- If an adapter property already exists in the source model's base property
  embedding, remove it from `property_embeddings_adapt` instead of duplicating
  it.
- If code and checkpoint configs diverged, preserve the checkpoint and use the
  source-provided config path; investigate `load_from_checkpoint_and_config`
  only as an intentional compatibility operation.
- A fine-tune output is not a base-training resume. Use the adapter source
  selector and its `load_epoch`, not `checkpoint_path`/`auto_resume` semantics.

## Device and optional-backend failures

**Symptoms:** CUDA unavailable, MPS operation errors, PyG kernel errors,
DDP initialization issues, or device OOM.

- Confirm `torch.cuda.is_available()`/MPS availability and a minimal tensor
  operation before launching. The package helper chooses CUDA, then MPS, then
  CPU for some utilities, but the trainer config defaults to GPU.
- On one GPU, use `trainer.accumulate_grad_batches=4` or a larger approved
  value for Alex-MP-20; preflight and inspect the derived data-module batch.
  Accumulation reduces each microbatch, while the nominal total batch remains
  controlled by the config expression.
- If a distributed strategy is inappropriate for one device or MPS, delete it
  with `~trainer.strategy` and select the accelerator explicitly.
- Do not claim that CPU or MPS is equivalent to CUDA performance. Check the
  selected backend's PyG operations and memory behavior separately.
- An OOM is a stop condition for the current launch. Do not repeatedly retry
  unchanged settings; change accumulation/device policy deliberately.

## W&B and logging failures

**Symptoms:** authentication prompts, network failures, logger import errors,
or a run starts but logging is unavailable.

- The README's local commands explicitly use `~trainer.logger`; use that only
  when W&B is not required.
- To opt in, remove the deletion and configure project/credentials in the
  trainer config or approved overrides. Keep secrets out of configs and logs
  shared with this skill.
- A logger-disabled run can still save Lightning checkpoints and configs. Do
  not infer a missing W&B dashboard means training failed if the trainer output
  says otherwise.

## Workflow and resume failures

**Symptoms:** job resumes an unexpected run, output is overwritten, or a run
stops after a partial epoch.

- Record the concrete Hydra output directory and resolved config before
  restarting. Use a new output directory if the previous run's identity is
  unclear.
- Base/CSP `auto_resume` searches the trainer-root checkpoint directory; a
  manually set `checkpoint_path` together with auto-resume is ambiguous and
  rejected by source code.
- Fine-tuning calls `trainer.fit(..., ckpt_path=None)` after loading its source
  model; do not treat `adapter.model_path` as a trainer resume path.
- Preserve partial checkpoints and consult the saved config. Resume only after
  confirming dataset, properties, source model, and hyperparameters match the
  intended run.
- If a failure is reproducible during config composition or data loading,
  return to preflight/data preparation. Do not use full training as a smoke
  test.
