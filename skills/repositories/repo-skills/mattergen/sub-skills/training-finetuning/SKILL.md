---
name: training-finetuning
description: "Route MatterGen Hydra base training, CSP training, property
  fine-tuning, custom-property setup, resource controls, checkpoints, and safe
  no-launch validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training and fine-tuning

Use this route when the task is to train MatterGen from scratch, train its
crystal-structure-prediction (CSP) variant, or fine-tune a checkpoint on one or
more properties. This route is procedural: it selects a dataset and config,
preflights overrides, then asks for an explicit decision before launching a
long-running job. It does **not** launch training as a default check.

## Route boundaries

- Use [data preparation](../data-preparation/SKILL.md) first when the requested
  dataset has not been unpacked, converted, or property-enriched.
- Use [generation](../generation/SKILL.md) after a checkpoint exists and the
  task is sampling, including CSP composition conditioning.
- Use [evaluation](../evaluation/SKILL.md) after structures or energies exist;
  this route does not establish paper-level metrics.
- Use [cli-reference.md](references/cli-reference.md) for copyable commands.
- Use [workflows.md](references/workflows.md) for the ordered runbook.
- Use [configuration.md](references/configuration.md) for config-group and
  resource details.
- Use [custom-properties.md](references/custom-properties.md) for labels,
  embedding configs, and the limits of config-only customization.
- Use [troubleshooting.md](references/troubleshooting.md) when a preflight,
  import, backend, dataset, checkpoint, or launcher step fails.
- Run the bundled [Hydra preflight](scripts/validate_hydra_overrides.py) before
  any expensive command. It only parses and checks files; it never starts a
  MatterGen process. Use the installed package's config resource when you want
  file-existence checks.

## Choose the operation

1. **Base training** uses `mattergen-train` with `default.yaml`. It constructs a
   new unconditional diffusion model from the selected data module.
2. **CSP training** uses the `csp` config name. CSP omits atomic-number
   denoising, so it is a distinct model/config, not a sampling-only flag.
3. **Fine-tuning** uses `mattergen-finetune` with `finetune.yaml` and an
   adapter. It loads `adapter.pretrained_name` from the published checkpoint
   registry, or `adapter.model_path` from a locally trained model, then adds
   the requested conditions under `property_embeddings_adapt`.
4. **Conditional base training** is possible by adding property embeddings to
   the base model, but the README's supported, lower-risk path is adapter
   fine-tuning. Do not silently turn an unconditional training request into a
   conditional one.

If the user has not chosen between base training and fine-tuning, stop after
preflight and ask. Fine-tuning is not a resume operation: it creates an adapter
model from a source checkpoint, whereas base training can auto-resume its own
output directory.

## Safe preflight, then explicit launch

From the installed skill directory, syntax-check a command without starting it:

```bash
python <mattergen-skill-root>/sub-skills/training-finetuning/scripts/validate_hydra_overrides.py \
  --config-root <mattergen-config-root> \
  data_module=mp_20 '~trainer.logger'
```

For CSP or fine-tuning, include the intended config and all property names:

```bash
python <mattergen-skill-root>/sub-skills/training-finetuning/scripts/validate_hydra_overrides.py \
  --config-root <mattergen-config-root> --config-name csp data_module=mp_20
python <mattergen-skill-root>/sub-skills/training-finetuning/scripts/validate_hydra_overrides.py \
  --config-root <mattergen-config-root> data_module=mp_20 \
  '+lightning_module/diffusion_module/model/property_embeddings@adapter.adapter.property_embeddings_adapt.dft_mag_density=dft_mag_density' \
  'data_module.properties=["dft_mag_density"]'
```

`<mattergen-config-root>` is the installed package's `conf` resource or an
explicit project copy that the user controls; it is not a path back to the
source repository. The preflight checks override shape, config-group files,
and property-embedding files when the config root is supplied. A passing
result is not a model instantiation or a data-read test. It is safe to run
repeatedly. Fix every `error`; review `warning` messages before launching.

Only after confirming dataset cache, backend/device, output location, and
checkpoint choice should the user run a command from [cli-reference.md](references/cli-reference.md).
Quote list/dict overrides in shells that interpret brackets, braces, or `$`.
Do not paste a literal `$PROPERTY` unless it is intentionally left for the
shell to expand.

## Resource and output controls

The default trainer is one device with float32 precision and a nominal total
training batch size of 512; the data-module batch expression divides this by
`trainer.accumulate_grad_batches`, devices, and nodes. Alex-MP-20 commonly needs
`trainer.accumulate_grad_batches=4` or more on one GPU. Start with a reduced
batch/limited epoch smoke test only when the user explicitly approves a launch;
the normal route is the no-launch preflight above. See [configuration.md](references/configuration.md)
for safe override patterns.

The default run directory is the generic pattern
`outputs/singlerun/<date>/<time>` (the config uses Hydra's `${now:...}` values).
A user may set `OUTPUT_DIR` before launch; preserve a dedicated, writable output
location and do not overwrite an unrelated run. Base training has
`auto_resume: True` and stores a resume checkpoint directory below the run;
CSP also enables auto-resume. Fine-tuning uses its own output directory and
loads the source checkpoint through the adapter rather than `checkpoint_path`.

W&B is configured as the default trainer logger, but README commands opt out
with `~trainer.logger`. Keep that opt-out for local checks and offline work.
Remove it only when the user has deliberately configured W&B credentials/project
settings or another logger. Do not claim that logging or full training metrics
were verified merely because a command was assembled.

## Expected observations and stop conditions

- A resolved config should show the selected `data_module`, trainer device,
  accumulation, logger state, and all requested properties.
- A train/fine-tune launch should print/save a resolved config and write
  Lightning checkpoints under the run output; the exact checkpoint filename is
  data- and epoch-dependent.
- README reports `loss_val` reaching about `0.4` for its MP-20 base-training
  example after 360 epochs, but this repository inspection did not reproduce
  that claim. Treat it as a documented reference, not a verification result.
- Stop before launch when the requested property is absent from every split,
  its embedding config is absent, the adapter source checkpoint cannot be
  located, the backend is unavailable, or the effective batch is unsafe.
- Stop and preserve the output directory when a job fails; inspect the saved
  config and checkpoint state before deciding whether to resume or start a new
  run. Use [troubleshooting.md](references/troubleshooting.md).
