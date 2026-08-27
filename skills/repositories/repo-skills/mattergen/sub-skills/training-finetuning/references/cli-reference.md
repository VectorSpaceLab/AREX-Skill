# MatterGen training CLI reference

All commands assume the current directory is the MatterGen project root, the
package is installed in the active Python 3.10 environment, and the dataset
cache has already been prepared. Run the no-launch checker first; it accepts
the same override tokens but never invokes a console entry point.

## Dataset preparation handoff

For archive extraction, CIF/CSV conversion, cache layout, or adding labels,
route to [data preparation](../../data-preparation/SKILL.md). The training
configs expect cache directories below a project-relative dataset cache (unless
the user's config changes `data_module.root_dir`). Do not start a trainer to
diagnose a missing cache.

## Base training

MP-20, with W&B disabled as in the README:

```bash
mattergen-train data_module=mp_20 ~trainer.logger
```

Alex-MP-20, with the README's single-GPU accumulation adjustment:

```bash
mattergen-train data_module=alex_mp_20 ~trainer.logger trainer.accumulate_grad_batches=4
```

The README notes that a single GPU generally cannot hold the nominal batch size
of 512. Increase `trainer.accumulate_grad_batches` if the effective per-device
batch still exceeds VRAM. The data module computes its training batch from
512, accumulation, device count, and node count; do not confuse accumulation
with increasing the per-step memory footprint.

Apple Silicon follows the README override form:

```bash
mattergen-train data_module=mp_20 ~trainer.logger ~trainer.strategy trainer.accelerator=mps
```

`~trainer.strategy` removes the default DDP strategy before selecting MPS. The
same pair of overrides can be appended to Alex-MP-20 or fine-tuning commands.
The inspected environment had CUDA 11.8 wheels and an A100 smoke check, not an
Apple device; MPS remains a documented path and must be verified on the target
machine.

## CSP training

CSP is selected by the Hydra config name, not by a generation-only option:

```bash
mattergen-train --config-name=csp data_module=mp_20 ~trainer.logger
```

The installed `mattergen-train` entry point dispatches to the package's Hydra
training function with `--config-name=csp`. CSP's config uses the CSP
corruption/loss and does not denoise atom types. Generation from its checkpoint
belongs to [generation](../../generation/SKILL.md) and must use its matching
sampling config and target-composition syntax.

## Single-property fine-tuning

The documented example adds a magnetic-density adapter condition to the
published MatterGen base checkpoint:

```bash
export PROPERTY=dft_mag_density
mattergen-finetune \
  adapter.pretrained_name=mattergen_base \
  data_module=mp_20 \
  +lightning_module/diffusion_module/model/property_embeddings@adapter.adapter.property_embeddings_adapt.$PROPERTY=$PROPERTY \
  ~trainer.logger \
  data_module.properties=["$PROPERTY"]
```

The `+` is required because the adapter's `property_embeddings_adapt` mapping
starts empty. The `data_module.properties` list is separately required so the
cached property is loaded into each batch. Replacing only the source selector
with a local model is supported:

```bash
mattergen-finetune \
  adapter.model_path="$MODEL_PATH" \
  data_module=mp_20 \
  +lightning_module/diffusion_module/model/property_embeddings@adapter.adapter.property_embeddings_adapt.$PROPERTY=$PROPERTY \
  ~trainer.logger \
  data_module.properties=["$PROPERTY"]
```

When both `adapter.model_path` and `adapter.pretrained_name` are supplied, the
script warns and uses `model_path`; avoid the ambiguity. The local path must
contain a saved MatterGen config and a discoverable checkpoint. The adapter
selects `adapter.load_epoch=last` by default; `best` or an integer epoch can be
chosen only when the source output contains a matching checkpoint.

## Multi-property fine-tuning

The README's two-property form is:

```bash
export PROPERTY1=dft_mag_density
export PROPERTY2=dft_band_gap
export MODEL_NAME=mattergen_base
mattergen-finetune \
  adapter.pretrained_name=$MODEL_NAME \
  data_module=mp_20 \
  +lightning_module/diffusion_module/model/property_embeddings@adapter.adapter.property_embeddings_adapt.$PROPERTY1=$PROPERTY1 \
  +lightning_module/diffusion_module/model/property_embeddings@adapter.adapter.property_embeddings_adapt.$PROPERTY2=$PROPERTY2 \
  ~trainer.logger \
  data_module.properties=["$PROPERTY1","$PROPERTY2"]
```

For every additional property, add both one `+lightning_module/...@adapter...`
override and one item in `data_module.properties`. Missing either side is a
configuration/data mismatch, not a harmless omission. With the default
`dropout_fields_iid: false`, the diffusion pre-corruption transform exposes
joint conditional fields only when all requested fields are present for a
sample; sparse labels can therefore reduce conditional training coverage.

## Logger and device overrides

- Disable the default W&B logger with `~trainer.logger`.
- Opt in by removing that deletion and configuring `trainer.logger` in the
  config or via Hydra overrides. Credentials and project policy are user-owned.
- Select MPS with `~trainer.strategy trainer.accelerator=mps`.
- Select CPU only for an explicitly approved tiny smoke test, for example
  `trainer.accelerator=cpu trainer.max_epochs=1`; this is not a performance
  recommendation.
- Tune memory with `trainer.accumulate_grad_batches=N`, then preflight the
  resulting command. Do not silently lower model dimensions or epochs for a
  production run.

## Output and follow-on commands

Hydra's generic output pattern is
`outputs/singlerun/<YYYY-MM-DD>/<HH-MM-SS>` unless `OUTPUT_DIR` or a config
override changes it. The README calls this output `$MODEL_PATH` for later
sampling. Inspect the resolved config and checkpoint files, then route sampling
to [generation](../../generation/SKILL.md) and metrics/relaxation to
[evaluation](../../evaluation/SKILL.md).
