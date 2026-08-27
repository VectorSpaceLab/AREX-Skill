# Configuration and Prompts Reference

This reference is self-contained for DiscoArt configuration and prompt work. It covers safe config validation, prompt planning, schedule strings, CLIP routing, and config helper APIs. It does not cover running diffusion generation or the command-line/service entry points.

## Public config helper signatures

| Helper | Runtime signature | Use |
| --- | --- | --- |
| `load_config` | `load_config(user_config: Union[Dict, str]) -> Dict` | Merge a user dict or YAML file path with defaults and return normalized keyword args for `create(...)`. |
| `save_config` | `save_config(docs: Union[DocumentArray, Document, Dict, str, SimpleNamespace], output: str) -> None` | Extract config tags from a local object or dict and write YAML. A string `docs` value is treated as a DocumentArray name to pull, not a local config path. |
| `show_config` | `show_config(docs: Union[DocumentArray, Document, Dict, str, SimpleNamespace], only_non_default: bool = True)` | Print a rich table of config values; by default only non-default values are shown. |
| `save_config_svg` | `save_config_svg(docs: Union[DocumentArray, Document, Dict, str, SimpleNamespace], output: Optional[str] = None, **kwargs) -> None` | Render the config table as SVG. If `output` is omitted, writes `{name_docarray}.svg`. |
| `export_python` | `export_python(docs: Union[DocumentArray, Document, Dict, str, SimpleNamespace], ignored_args: Tuple[str] = ('name_docarray',)) -> str` | Return a Python snippet containing `from discoart import create` and a `create(...)` call with non-default args. Private keys and ignored args are omitted. |
| `cheatsheet` | `cheatsheet()` | Print the supported parameter list, defaults, and distilled descriptions. |

`load_config("my.yml")` loads a YAML config file. In contrast, `show_config("name")`, `save_config("name", ...)`, `save_config_svg("name", ...)`, and `export_python("name")` use `DocumentArray.pull("name")` semantics and may require the named result to be reachable; pass a dict, `Document`, `DocumentArray`, or `SimpleNamespace` to avoid pulling.

## Config loading and normalization

`load_config` starts from the default parameters, checks and filters user keys, applies any cut-schedule group, merges user overrides, then normalizes selected values.

Important runtime rules:

- Unknown top-level keys raise `AttributeError: unknown argument `name`, misspelled?` unless the key starts with `_` or is a legacy key.
- Legacy keys `clip_sequential_evaluation`, `fuzzy_prompt`, and `skip_augs` are accepted and then removed. Keys beginning with `_` are also removed.
- If `cut_schedules_group` is present, the named group is applied before user overrides. Explicit user values such as `cut_overview` or `cut_innercut` take precedence over the group.
- `width_height` is coerced element-by-element to `int`.
- Default integer-like keys, plus `seed`, `cut_overview`, and `cut_innercut`, are coerced to `int` when the supplied value is neither `int` nor `str` and is not `None`.
- `seed` becomes `int(seed or random_uint32)`. A missing seed produces a random seed; a literal `0` is falsy and is also replaced by a random seed in this version.
- If `name_docarray` is missing, DiscoArt uses `discoart-{uuid}` or `discoart-{batch_name}-{uuid}`. If it is provided, it is formatted with `name_docarray.format(**cfg)`, so placeholders such as `{steps}` or `{perlin_init}` can refer to any config key.

## Accepted top-level config keys

These keys are accepted by the default config schema. Any other public key is an unknown argument unless it is one of the legacy/private exceptions above.

| Area | Keys |
| --- | --- |
| Prompts and images | `text_prompts`, `init_image`, `init_scale`, `on_misspelled_token`, `truncate_overlength_prompt` |
| Size and diffusion loop | `width_height`, `skip_steps`, `steps`, `diffusion_model`, `diffusion_sampling_mode`, `diffusion_model_config`, `use_secondary_model`, `eta`, `seed` |
| Guidance/loss scales | `clip_guidance_scale`, `tv_scale`, `range_scale`, `sat_scale`, `clamp_grad`, `clamp_max`, `clip_denoised`, `randomize_class`, `rand_mag` |
| Cut scheduling | `cut_overview`, `cut_innercut`, `cut_icgray_p`, `cut_ic_pow`, `cutn_batches`, `cut_schedules_group`, `visualize_cuts` |
| Output and batches | `save_rate`, `gif_fps`, `gif_size_ratio`, `n_batches`, `batch_size`, `batch_name`, `name_docarray`, `image_output`, `display_rate` |
| CLIP models | `clip_models`, `clip_models_schedules`, `text_clip_on_cpu` |
| Symmetry/transform | `use_vertical_symmetry`, `use_horizontal_symmetry`, `transformation_percent` |
| Runtime controls | `perlin_init`, `perlin_mode`, `skip_event`, `stop_event` |

Selected defaults:

```yaml
text_prompts:
  - A beautiful painting of a singular lighthouse, shining its light across a tumultuous sea of blood by greg rutkowski and thomas kinkade, Trending on artstation.
  - yellow color scheme
width_height: [1280, 768]
steps: 250
skip_steps: 0
init_scale: 1000
clip_guidance_scale: 5000
tv_scale: 0
range_scale: 150
sat_scale: 0
cutn_batches: 4
diffusion_model: 512x512_diffusion_uncond_finetune_008100
diffusion_sampling_mode: ddim
use_secondary_model: true
seed: null
eta: 0.8
clamp_grad: true
clamp_max: 0.05
cut_overview: "[12]*400+[4]*600"
cut_innercut: "[4]*400+[12]*600"
cut_icgray_p: "[0.2]*400+[0]*600"
cut_ic_pow: 1.0
save_rate: 20
gif_fps: 20
gif_size_ratio: 0.5
n_batches: 4
batch_size: 1
clip_models:
  - ViT-B-32::openai
  - ViT-B-16::openai
  - RN50::openai
on_misspelled_token: ignore
text_clip_on_cpu: false
image_output: true
display_rate: 1
```

## Cut schedule groups

`cut_schedules_group` can be one of `default`, `pad_or_pulp`, `watercolor`, or `han_fav`. Group values are just config overrides applied before explicit user values.

| Group | Distilled values |
| --- | --- |
| `default` | `cut_overview: "[12]*400+[4]*600"`; `cut_innercut: "[4]*400+[12]*600"`; `cut_ic_pow: "[1]*1000"`; `cut_icgray_p: "[0.2]*400+[0]*600"` |
| `pad_or_pulp` | Overview starts high and tapers: `15,15,12,12,6,4,2,0` over blocks summing to 1000; inner cuts rise from `1` to `10`; `cut_ic_pow` mostly `12` then `10`; grayscale probability decays from `0.87` to `0`. |
| `watercolor` | Overview `14,12,4,0` over `200,200,400,200`; inner cuts `2,4,12,12`; `cut_ic_pow` mostly `12` then `10`; grayscale probability decays `0.7,0.6,0.45,0.3,0`. |
| `han_fav` | Adds stronger style settings: `tv_scale: 60000`, `sat_scale: 10000`, `range_scale: 10000`, `cutn_batches: 8`, `clip_guidance_scale: 12000`, `clamp_max: 0.1`, five OpenAI CLIP models, plus 1000-step cut schedules. |

## Schedule grammar and 1000-step expansion

DiscoArt schedules are expanded by `_eval_scheduling_str` to exactly 1000 entries. This internal 1000-step schedule is independent of the user-facing `steps` value; the runner indexes the 1000-step table as diffusion progresses.

Accepted schedule inputs:

- `int`, `float`, or `bool`: repeated 1000 times.
- A Python `list` or `tuple`: accepted only when length is exactly 1000.
- A string that passes the safe grammar, then evaluates to a scalar or list/tuple of length 1000.

Safe schedule strings allow only these tokens: exact `True`, exact `False`, digits, decimal points, comma, space, parentheses, brackets, `*`, `+`, and `-`. Names, underscores, quotes, function calls, lowercase booleans such as `true`, and arbitrary code are rejected before `eval`.

Examples:

| String | Meaning |
| --- | --- |
| `"1"` | scalar `1`, repeated for all 1000 steps |
| `"True"` / `"False"` | boolean scalar repeated for all 1000 steps |
| `"[12]*400+[4]*600"` | 400 steps at `12`, then 600 steps at `4` |
| `"[True]*500+[False]*500"` | on for the first 500 internal steps, off for the last 500 |
| `"([1]+[2])*500"` | alternates `1,2` until exactly 1000 entries |

Config fields expanded through the cut/scheduler table are:

```text
cut_overview, cut_innercut, cut_icgray_p, cut_ic_pow,
use_secondary_model, cutn_batches, clip_guidance_scale,
tv_scale, range_scale, sat_scale, init_scale,
clamp_grad, clamp_max
```

Additional scheduled values are supported for schema-v1 prompt `weight`, schema-v1 prompt `schedule`, and each `clip_models_schedules[model_name]` value.

## Prompt inputs

### Legacy prompt strings

`text_prompts` may be a single string or a list of strings. Each string is parsed as legacy prompt text plus an optional trailing numeric weight:

```yaml
text_prompts:
  - "lighthouse at stormy sea:2.5"
  - "oversaturated, blurry:-1"
```

The split uses the last colon. If no colon is present, the weight is `1`. The legacy suffix must convert with `float(...)`; schedule strings such as `prompt:[1]*1000` are not supported in legacy form. Use schema v1 when the weight needs a schedule.

### Schema version `"1"`

For prompt scheduling, use a dict with `version` and `prompts`. Runtime comparison checks the string value `"1"`; quote it in YAML to avoid accidental integer parsing.

```yaml
text_prompts:
  version: "1"
  prompts:
    - text: the main prompt
      weight: 10
      spellcheck: ignore
    - text: details appear later
      weight: 7
      schedule: "[False]*500+[True]*500"
    - text: model-specific positive modifier
      weight: "[1]*100+[2]*300+[8]*600"
      clip_guidance: ["RN50::openai"]
    - text: unwanted artifact
      weight: -4
width_height: [512, 512]
```

Prompt item fields:

| Field | Required | Runtime behavior |
| --- | --- | --- |
| `text` | Yes | Parsed, normalized, tokenized, and spellchecked. A trailing `:weight` can supply the default weight if `weight` is absent. |
| `weight` | No | Positive, negative, zero, or scheduled. If absent, uses the weight parsed from `text`, usually `1`. Expanded to 1000 entries. A zero value deactivates the prompt at that step. |
| `schedule` | No | Boolean/scalar/list schedule. If absent, `True` is expanded to active for all 1000 steps. |
| `clip_guidance` | No | List/set of CLIP model names allowed to use this prompt. If absent, all configured `clip_models` are allowed. Must be a subset of `clip_models`. |
| `spellcheck` | No | Per-prompt override for `on_misspelled_token`: `ignore`, `correct`, or `raise`. |

`PromptPlanner(args)` rejects empty prompt lists, unsupported prompt types, unsupported schema versions, and `clip_guidance` values outside `args.clip_models`.

## Active-prompt routing

For each CLIP model and internal step, a prompt is active only when all of these are true:

1. The model itself is active according to `clip_models_schedules` if that model has a schedule; otherwise the model is always on.
2. The prompt weight at that step is truthy. Negative weights are active; zero weights are inactive.
3. The prompt `schedule` at that step is truthy.
4. The active CLIP model name is in the prompt's `clip_guidance` set.

`PromptPlanner.get_prompt_ids(active_clip, num_step)` returns `((prompt_id, ...), (weight, ...))` for active prompts, or an empty tuple when none are active.

Example with three prompts and three CLIP labels:

```python
text_prompts = {
    'version': '1',
    'prompts': [
        {'text': 'hello', 'clip_guidance': ['a', 'b', 'c'], 'schedule': '[True]*500+[False]*500'},
        {'text': 'bye', 'clip_guidance': ['a'], 'schedule': '[True]*1000'},
        {'text': 'world', 'clip_guidance': ['c'], 'schedule': '[True]*400+[False]*300+[True]*300'},
    ],
}
```

- Step `0`, CLIP `a`: prompts `0` and `1` with weights `1.0, 1.0`.
- Step `0`, CLIP `b`: prompt `0` only.
- Step `450`, CLIP `c`: prompt `0` only because prompt `2` is off between steps `400` and `699`.
- Step `700`, CLIP `c`: prompt `2` only because prompt `0` is off after step `499`.
- Step `700`, CLIP `b`: no active prompts.

## CLIP model schedules versus prompt `clip_guidance`

`clip_models_schedules` controls whether a configured CLIP model runs at a step:

```yaml
clip_models:
  - RN50::openai
  - ViT-B-32::openai
clip_models_schedules:
  RN50::openai: "[True]*400+[False]*600"
```

A schedule key for a model not present in `clip_models` is not used by the runner. A prompt-level `clip_guidance` list is stricter: every listed model must be present in `clip_models`, or `PromptPlanner` raises `ValueError: `clip_guidance` contains unknown clip models`.

## Spellcheck behavior

Prompt text is normalized with CLIP tokenizer preprocessing and checked against a spellchecker loaded with DiscoArt's vocabulary whitelist. Supported strategies are:

- `ignore`: keep the token and log a warning about likely misspellings.
- `correct`: replace each misspelled token with the suggested correction and log a warning.
- `raise`: raise `ValueError` with the suggestions.

A schema-v1 prompt can set `spellcheck` to override global `on_misspelled_token` for that prompt only.

## Config export/import recipes

Load and validate a YAML file for Python API use:

```python
from discoart import load_config

cfg = load_config('my.yml')
# Generation belongs to the artwork-generation sub-skill:
# da = create(**cfg)
```

Save or show a config from a returned `DocumentArray`, a single `Document`, a config `dict`, or a `SimpleNamespace`:

```python
from discoart import save_config, show_config
from discoart.config import save_config_svg, export_python

show_config(cfg, only_non_default=True)
save_config(cfg, 'normalized.yml')
save_config_svg(cfg, 'config.svg')
python_snippet = export_python(cfg)
```

`export_python` includes only non-default arguments, excludes private keys, and ignores `name_docarray` unless you change `ignored_args`.

## Safe validator helper

Use the bundled helper for no-generation checks:

From this sub-skill directory:

```bash
python scripts/validate_discoart_config.py \
  --config my.yml \
  --check-prompts \
  --show-non-default
```

Structured output:

From this sub-skill directory:

```bash
python scripts/validate_discoart_config.py \
  --config my.yml --check-prompts --json
```

The validator imports DiscoArt with remote model lookup disabled and stubs package import-time URL opening to avoid network access. It calls `load_config`, validates schedules, optionally builds `PromptPlanner`, and never calls `create()`.

## Verification candidates for this area

After integration, the owning verification should run the safe native subsets for config schedules, prompt planning, and helper display/export behavior. Good focused signals are:

- Config round-trip and schedule validation pass for `load_config`, `save_config`, `export_python`, `_is_valid_schedule_str`, and `_eval_scheduling_str`.
- Prompt planner tests prove active prompt ids/weights across step ranges, CLIP guidance subsets, and scheduled weights.
- Cheatsheet/config SVG helpers run without model loading.
