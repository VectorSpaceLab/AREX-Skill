# Config API and Model-Type Defaults

Use this reference when inspecting Protenix configuration dictionaries, composing overrides, or explaining why a model name changes cycles, diffusion steps, feature switches, or dimensions.

## Core Entry Points

Current config utilities are in `protenix.config.config`:

```python
from protenix.config.config import ConfigManager, load_config, parse_configs, save_config

parse_configs(configs, arg_str=None, fill_required_with_null=False)
load_config(path: str) -> dict
save_config(config, path: str) -> None
```

Important behavior:

- `parse_configs` accepts a nested Python dictionary and an optional shell-like override string such as `--model.N_cycle 4 --sample_diffusion.N_step 20`.
- `ConfigManager` flattens nested keys into dotted arguments. Source keys may not contain literal `.` characters.
- All parser inputs arrive as strings and are converted later to the default value type or declared wrapper type.
- Boolean overrides pass through Protenix's boolean parser; prefer explicit `true` or `false` strings when composing CLI snippets.
- Lists are comma-separated with no spaces, for example `--seeds 101,102` for list-backed values.
- `None`, `none`, and `null` are accepted only when a value wrapper allows `None` or when required values are filled with null.
- Missing required values raise unless `fill_required_with_null=True` is used for inspection or first-pass model-name parsing.
- `save_config` writes YAML and converts an `ml_collections.ConfigDict` to a plain dict first.

## Typical Inspection Pattern

For read-only config inspection, construct configs from bundled config modules, parse with required values filled, apply model-specific deltas, then parse or update user overrides deliberately.

```python
from ml_collections import ConfigDict
from configs.configs_base import configs_base, data_configs
from configs.configs_inference import inference_configs
from configs.configs_model_type import model_configs
from protenix.config.config import parse_configs

base = {**configs_base, "data": data_configs, **inference_configs}
cfg = parse_configs(base, fill_required_with_null=True)
cfg.update(ConfigDict(model_configs[cfg.model_name]))
```

Use this as an inspection pattern only. Prediction command construction belongs to `../../cli-and-inference/SKILL.md`.

## Override Syntax

Dotted keys mirror nested dictionaries:

```text
--model.N_cycle 4
--sample_diffusion.N_step 20
--triangle_attention torch
--triangle_multiplicative torch
--enable_tf32 false
--sample_diffusion.guidance.enable true
```

Parser failure triage:

- `unrecognized arguments`: the dotted key is not present in the config dictionary used for this parse pass.
- `config ... not allowed to be none`: a required value was not supplied and `fill_required_with_null` is false.
- Surprise string/list values: check whether the original default is a `ListValue`, list, bool, or wrapper; conversion follows that declared type.
- Model-specific keys missing on first pass: parse once with base configs to discover `model_name`, merge the model-specific section, then parse again with the original overrides.

## Base, Inference, and Training Defaults

Important base defaults from the config modules:

- `configs_base.model_name`: `protenix_base_default_v1.0.0` for training defaults.
- `configs_inference.model_name`: `protenix_base_default_v1.0.0` for inference defaults.
- `configs_base.triangle_multiplicative`: `cuequivariance`.
- `configs_base.triangle_attention`: `cuequivariance`.
- `configs_base.enable_tf32`: `False` for training defaults.
- `configs_inference.enable_tf32`: `True` for inference defaults.
- `configs_inference.enable_efficient_fusion`: `True`.
- `configs_inference.enable_diffusion_shared_vars_cache`: `True`.
- `configs_base.dtype`: `bf16` for training defaults.

The model class sets `torch.backends.cuda.matmul.allow_tf32` from `configs.enable_tf32`, so changing this flag affects global CUDA matmul behavior inside the running process.

## Model-Type Deltas

Supported model-name behavior is encoded in `configs.configs_model_type.model_configs` and summarized here:

| Model name | Key deltas |
| --- | --- |
| `protenix-v2` | Larger pair dimension (`c_z=256`), wider model submodules, `diffusion_batch_size=64`, `model.N_cycle=10`, `sample_diffusion.N_step=200`. |
| `protenix_base_default_v1.0.0` | `model.N_cycle=10`, template embedder blocks enabled, `sample_diffusion.N_step=200`. |
| `protenix_base_20250630_v1.0.0` | Same practical structure as v1.0.0 base with a newer training-data cutoff. |
| `protenix_base_default_v0.5.0` | `model.N_cycle=10`, `sample_diffusion.N_step=200`. |
| `protenix_base_constraint_v0.5.0` | Constraint embedders enabled, ESM enabled, `load_strict=False`, finetune parameter substrings for constraint modules. |
| `protenix_mini_default_v0.5.0` | `model.N_cycle=4`, fewer MSA/Pairformer/diffusion blocks, `sample_diffusion.N_step=5`, `load_strict=False`. |
| `protenix_tiny_default_v0.5.0` | `model.N_cycle=4`, even fewer Pairformer blocks, `sample_diffusion.N_step=5`, `load_strict=False`. |
| `protenix_mini_esm_v0.5.0` | Mini settings plus ESM enabled and `use_msa=False`. |
| `protenix_mini_ism_v0.5.0` | Mini settings plus ISM-flavored ESM model name and `use_msa=False`. |

Route model selection and CLI command assembly to `../../cli-and-inference/SKILL.md` once the internal meaning of the selected model is understood.

## Programmatic Runner Mutations

The batch inference runner parses base configs, applies model-specific configs, then directly sets high-level runtime values from function/CLI options:

- `configs.model.N_cycle = n_cycle`
- `configs.sample_diffusion.N_sample = n_sample`
- `configs.sample_diffusion.N_step = n_step`
- `configs.dtype = dtype`
- `configs.triangle_multiplicative = trimul_kernel`
- `configs.triangle_attention = triatt_kernel`
- `configs.enable_diffusion_shared_vars_cache = enable_cache`
- `configs.enable_efficient_fusion = enable_fusion`
- `configs.enable_tf32 = enable_tf32`
- `configs.sample_diffusion.guidance.enable = use_tfg_guidance`

Training reads `TRIANGLE_ATTENTION` and `TRIANGLE_MULTIPLICATIVE` from the environment before parsing, defaulting both to `cuequivariance`.

## Safe Save/Load Notes

- Use `save_config` only for generated config artifacts requested by the user; do not overwrite repo configs casually.
- Do not store machine-specific paths in reusable skill content or public examples.
- If a user asks for a persistent YAML override, prefer a minimal config fragment plus the exact `parse_configs` keys needed to reproduce it.
- If a user asks why a default changed, inspect the parse order: base defaults, model-specific deltas, then user overrides or runner mutations.
