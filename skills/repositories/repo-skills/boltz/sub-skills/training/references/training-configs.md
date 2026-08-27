# Training Configs

Boltz training configs are Hydra/OmegaConf YAML files consumed by the training launcher. The public templates cover Boltz-1-style structure and confidence training. The repository documentation explicitly says updated Boltz-2 training information is coming soon, so only use Boltz-2 source facts when diagnosing code-level config fields; do not invent Boltz-2 templates.

## Top-Level Fields

| Field | Meaning | Guidance |
| --- | --- | --- |
| `trainer` | PyTorch Lightning trainer settings | Start with one GPU, then scale. Debug mode overrides devices to one. |
| `output` | Training output/root directory | Must not remain `SET_PATH_HERE`; checkpoints and logs are written here. |
| `pretrained` | Weight initialization checkpoint | Used only when `resume` is empty. Can be `null` for from-scratch if the model/config supports it. |
| `resume` | Lightning checkpoint for continuing/validating | Use for interrupted runs and `validation_only`. |
| `disable_checkpoint` | Disables Lightning checkpoint callback | Keep `false` for real runs unless storage policy says otherwise. |
| `save_top_k` | Checkpoint callback `save_top_k` | Templates use `-1` to keep all; consider storage limits. |
| `matmul_precision` | Optional `torch.set_float32_matmul_precision` value | Leave `null` unless the user has a precision policy. |
| `find_unused_parameters` | DDP strategy flag | Enable only when DDP reports unused parameters. |
| `validation_only` | Run validation instead of fit | Requires `resume` checkpoint and validation data. |
| `debug` | Single-process smoke test mode | Prefer CLI override `debug=1` for initial runs. |
| `strict_loading` | Lightning module strict loading toggle | Default dataclass value is `true`; set `false` only to tolerate intentional checkpoint mismatch. |

## Template Variants

| Template intent | Key model flags | Data symmetry returns | Notes |
| --- | --- | --- | --- |
| Structure | `confidence_prediction: false` | train `false`, val `true` | Structure-only Boltz1-style template. |
| Confidence | `structure_prediction_training: false`, `confidence_prediction: true`, `confidence_imitate_trunk: true`, `alpha_pae: 1` | train `true`, val `true` | Source comment says `load_confidence_from_trunk: true` only when starting from scratch, not from a pretrained confidence model. |
| Full | `structure_prediction_training: true`, `confidence_prediction: true`, `confidence_imitate_trunk: true`, `alpha_pae: 1` | train `true`, val `true` | Joint structure/confidence template. |

The source templates use `_target_: boltz.model.model.Boltz1`. In the visible source tree, model classes live under `boltz.model.models.boltz1.Boltz1` and `boltz.model.models.boltz2.Boltz2`. If Hydra cannot import the template target in the installed package, verify the installed package version and the import path before changing model architecture.

## Data Block Requirements

The training data module expects this shape after Hydra instantiation:

```yaml
data:
  datasets:
    - _target_: boltz.data.module.training.DatasetConfig
      target_dir: /path/to/processed_targets
      msa_dir: /path/to/processed_msa
      prob: 1.0
      sampler:
        _target_: boltz.data.sample.cluster.ClusterSampler
      cropper:
        _target_: boltz.data.crop.boltz.BoltzCropper
        min_neighborhood: 0
        max_neighborhood: 40
      split: /path/to/validation_ids.txt
  filters:
    - _target_: boltz.data.filter.dynamic.size.SizeFilter
      min_chains: 1
      max_chains: 300
  tokenizer:
    _target_: boltz.data.tokenize.boltz.BoltzTokenizer
  featurizer:
    _target_: boltz.data.feature.featurizer.BoltzFeaturizer
  symmetries: /path/to/symmetry.pkl
```

Important data-module facts:

- `target_dir/manifest.json` is loaded unless `manifest_path` is supplied for that dataset.
- Structures are loaded from `target_dir/structures/<record.id>.npz`.
- MSA files are loaded from `msa_dir/<msa_id>.npz` for non-empty, non-`-1` chain MSA ids.
- `data.symmetries` is loaded before datasets are built; missing symmetry files fail early.
- `split` is a newline-delimited record-id file. IDs in the split are validation records; all other manifest records stay in training.
- If `split` is omitted, validation records are empty unless `overfit` redirects validation to training records.
- `val_batch_size` must be `1`; the data module asserts this.
- Dataset probabilities in `data.datasets[*].prob` are used directly by `numpy.random.choice`, so they should sum to about `1.0`.

The repository split assets are example semantics, not reusable runtime dependencies: `validation_ids.txt` and `test_ids.txt` contain hundreds of PDB-like IDs, and `casp15_ids.txt` contains CASP target IDs. In a portable config, copy or create your own split file and reference that path.

## Resource Knobs

| Field | Template default | Why it matters |
| --- | --- | --- |
| `data.max_tokens` | `512` | Crop token budget; reduce for memory. Docs suggest `256` or `384` alternatives. |
| `data.max_atoms` | `4608` | Crop atom budget; reduce with tokens, e.g. `2304` or `3456`. |
| `data.max_seqs` | `2048` | MSA depth budget and padding target. |
| `data.batch_size` | `1` | Per-device batch size. Keep small for large crops. |
| `trainer.accumulate_grad_batches` | `128` | Effective batch accumulation; adjust with device count. |
| `data.num_workers` | `4` | DataLoader workers; debug mode sets `0`. |
| `data.pad_to_max_*` | `true` | Pads crops to maxima, improving shape stability but increasing memory. |
| `model.*activation_checkpointing` | `true` in major blocks | Saves memory at compute cost. |
| `model.*offload_to_cpu` | `false` | Possible memory lever if supported by the block, but slower. |
| `model.compile_*` | mostly `false` | Compilation can be faster after warmup but complicates debugging. |

For a debug-safe single-GPU smoke test, prefer temporary CLI-style overrides in the user's Boltz training environment instead of permanently mutating the template. A conservative override set is:

```text
debug=1 data.max_tokens=256 data.max_atoms=2304 data.samples_per_epoch=8 trainer.max_epochs=1 disable_checkpoint=true
```

## Optimizer And Loss Fields

The model training args use Adam/AdamW-style fields and an `af3` scheduler:

- `adam_beta_1`, `adam_beta_2`, `adam_eps`, `base_lr`, `max_lr`.
- `lr_scheduler: af3` uses linear warmup, plateau, then exponential decay.
- `lr_warmup_no_steps` must not exceed `lr_start_decay_after_n_steps` in the scheduler implementation.
- `diffusion_loss_weight`, `distogram_loss_weight`, and `confidence_loss_weight` combine the training losses.
- Confidence/full templates set `symmetry_correction` and `run_confidence_sequentially` in training/validation args.

## Boltz-2 Boundaries

The source tree contains `Boltz2` with additional constructor fields such as affinity prediction, templates, validators, token-level confidence, b-factor prediction, cyclic position encoding, and template compilation. However, the public training page marks updated Boltz-2 training docs as coming soon and the assigned templates are Boltz1-style. If a user asks for Boltz-2 training:

- Say the repo does not yet provide updated public Boltz-2 training instructions in the inspected docs.
- Validate only general Hydra/data/trainer/checkpoint mechanics that are shared with the launcher.
- Ask for an existing Boltz-2 config or upstream release notes before proposing architecture-specific changes.
- Do not convert a Boltz1 config to Boltz2 by guessing constructor fields.