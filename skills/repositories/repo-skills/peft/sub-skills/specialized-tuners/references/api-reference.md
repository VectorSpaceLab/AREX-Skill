# Specialized Tuner API Reference

Use public imports from `peft` when available:

```python
from peft import get_peft_model, TaskType
from peft import IA3Config, BOFTConfig, VeraConfig
```

PEFT package facts for this skill: install with `pip install peft` for normal use, or use a source editable install for PEFT contributors; Python support starts at Python 3.10; there are no PEFT console entry points for these tuners.

## Common construction pattern

```python
config = SomeTunerConfig(task_type=TaskType.CAUSAL_LM, target_modules=["q_proj", "v_proj"])
model = get_peft_model(base_model, config)
model.print_trainable_parameters()
```

`PeftConfig` accepts common metadata such as `task_type`, `peft_type`, `base_model_name_or_path`, `revision`, and `inference_mode`. `PeftModel(model, peft_config, adapter_name="default", autocast_adapter_dtype=True, low_cpu_mem_usage=False)` and `get_peft_model(model, peft_config, adapter_name="default", mixed=False, autocast_adapter_dtype=True, revision=None, low_cpu_mem_usage=False)` are the normal integration surfaces.

## Config and model class map

| Method id / `PeftType` | Public config class | Model class pattern | Notes |
| --- | --- | --- | --- |
| `IA3` | `IA3Config` | `IA3Model` | Needs `target_modules`; often needs `feedforward_modules`. |
| `BOFT` | `BOFTConfig` | `BOFTModel` | Orthogonal butterfly tuner. |
| `OFT` | `OFTConfig` | `OFTModel` | Orthogonal fine-tuning; layer support can include linear/conv and some backend-specific linear classes. |
| `LOHA` | `LoHaConfig` | `LoHaModel` | LyCORIS Hadamard decomposition; registered prefix is `hada_`. |
| `LOKR` | `LoKrConfig` | `LoKrModel` | LyCORIS Kronecker decomposition. |
| `POLY` | `PolyConfig` | `PolyModel` | Multitask adapter inventory/routing. |
| `VERA` | `VeraConfig` | `VeraModel` | Shared random projections plus trainable scaling vectors. |
| `PVERA` | `PveraConfig` | `PveraModel` | Probabilistic VeRA; note lowercase `Pvera`, not `PVera`. |
| `VBLORA` | `VBLoRAConfig` | `VBLoRAModel` | Vector-bank LoRA-style sharing; class uses capital `VBLoRA`. |
| `XLORA` | `XLoraConfig` | `XLoraModel` | Expert-gating over LoRA adapters; class uses `XLora`, not `XLoRA`. |
| `LN_TUNING` | `LNTuningConfig` | `LNTuningModel` | LayerNorm tuning; docs call it LN tuning. |
| `FOURIERFT` | `FourierFTConfig` | `FourierFTModel` | Spectral coefficient update. |
| `FROD` | `FrodConfig` | `FrodModel` | Full-rank diagonalization-style update; class uses `Frod`. |
| `HRA` | `HRAConfig` | `HRAModel` | Householder reflection adaptation. |
| `HIRA` | `HiraConfig` | `HiraModel` | Hadamard high-rank adaptation; class uses `Hira`. |
| `SHIRA` | `ShiraConfig` | `ShiraModel` | Sparse high-rank adapters; class uses `Shira`. |
| `RANDLORA` | `RandLoraConfig` | `RandLoraModel` | Full-rank random-basis adaptation; class uses `RandLora`. |
| `ROAD` | `RoadConfig` | `RoadModel` | Rotation adapter; mixed-batch serving oriented. |
| `WAVEFT` | `WaveFTConfig` | `WaveFTModel` | Wavelet/spectral update; class uses `WaveFT`. |
| `OSF` | `OSFConfig` | `OSFModel` | Orthogonal subspace fine-tuning for continual learning. |
| `DELORA` | `DeloraConfig` | `DeloraModel` | Decoupled low-rank adaptation; class uses `Delora`. |
| `GRALORA` | `GraloraConfig` | `GraloraModel` | Gradient/rank-adaptive LoRA-family method; route here unless task is ordinary LoRA setup. |
| `ADAMSS` | `AdamssConfig` | `AdamssModel` | Adaptive multi-subspace approach; class uses `Adamss`. |
| `BEFT` | `BeftConfig` | `BeftModel` | Bias-efficient fine-tuning. |
| `C3A` | `C3AConfig` | `C3AModel` | Circular convolution adaptation. |
| `LILY` | `LilyConfig` | `LilyModel` | Structured shared-factor tuner. |
| `MISS` | `MissConfig` | `MissModel` | Matrix shard sharing. |
| `PSOFT` | `PsoftConfig` | `PsoftModel` | Principal subspace orthogonal fine-tuning; class uses `Psoft`. |
| `PEANUT` | `PeanutConfig` | `PeanutModel` | Weight-aware neural tweaker. |
| `TINYLORA` | `TinyLoraConfig` | `TinyLoraModel` | Extremely small LoRA-like parametrization; class name uses `TinyLora`. |

## Field patterns to check

### Targeting fields

Many specialized configs accept:

- `target_modules`: suffix list, regex string, or method-specific shorthand for the modules to wrap.
- `exclude_modules`: suffix list or regex to leave modules untouched.
- `layers_to_transform` and `layers_pattern`: restrict injection to certain layer indices and layer-name patterns.
- `modules_to_save`: extra non-adapter modules that stay trainable and are saved with the adapter.

Common validation rule: if `target_modules` is a regex string, methods often reject `layers_to_transform` and sometimes `layers_pattern`; if `layers_pattern` is set, `layers_to_transform` usually must also be set.

### Projection persistence fields

VeRA-like and random-basis methods often expose `projection_prng_key`, `projection_seed`, `save_projection`, `init_weights`, or related fields. Use saved projections for reproducible, resumable training; use regenerated projections only for storage-sensitive inference or when exact cross-version reproducibility is not required.

### Rank and shape fields

Rank-like fields include `r`, `rank`, `rank_pattern`, `effective_rank`, `vector_length`, `num_vectors`, block sizes, subspace counts, and method-specific factors. Always align these with target weight shapes. For custom models, start with one or two small target modules and inspect injected modules before broadening.

### Task type

Use `TaskType.CAUSAL_LM`, `TaskType.SEQ_2_SEQ_LM`, `TaskType.SEQ_CLS`, `TaskType.TOKEN_CLS`, or the relevant PEFT task enum when the method or base model wrapper needs task-specific behavior. If a config accepts `task_type=None`, PEFT may still wrap the base model, but generation/classification helpers can behave differently.

## Introspection helper

Run the bundled script against the active Python environment:

```bash
python skills/peft/sub-skills/specialized-tuners/scripts/list_peft_methods.py --filter vera
```

The script imports `peft`, lists `PeftType` values, and reports public `*Config` classes that appear in the installed package. It does not require the source checkout.
