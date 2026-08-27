# Configuration and Prompt Troubleshooting

Use this guide for DiscoArt config and prompt failures that occur before image generation. If the problem requires running diffusion, model downloads, CUDA memory, output files, or service endpoints, route to the owning sibling sub-skill.

## `AttributeError: unknown argument `name`, misspelled?`

Cause: `load_config` rejects public top-level keys that are not in DiscoArt's default config. The check runs before generation.

Fix checklist:

1. Compare the key to the accepted config-key table in `configuration-and-prompts.md`.
2. Correct common spelling/casing mistakes such as `widthHeight` -> `width_height`, `clip_model` -> `clip_models`, or `prompt` -> `text_prompts`.
3. Move prompt item fields under `text_prompts.prompts[]`; fields such as `text`, `weight`, `schedule`, `clip_guidance`, and `spellcheck` are not top-level config keys.
4. Remove old Disco Diffusion fields that DiscoArt does not own. `clip_sequential_evaluation`, `fuzzy_prompt`, and `skip_augs` are legacy exceptions: `load_config` accepts them but silently removes them.
5. Private keys beginning with `_` are also removed and should not be used for runtime behavior.

If the user intended to use CLI syntax such as `python -m discoart create my.yml`, route command usage to `cli-and-serving`; the config key rules stay the same.

## Bad `cut_schedules_group`

Cause: a group name is looked up directly. Misspelling or unsupported names can raise a key error when `load_config` tries to apply the group.

Valid groups are `default`, `pad_or_pulp`, `watercolor`, and `han_fav`. If the user also supplies `cut_overview`, `cut_innercut`, `cut_ic_pow`, or `cut_icgray_p`, those explicit fields override group values.

## `ValueError: invalid scheduling string: ..., it contains unsafe code`

Cause: schedule strings are filtered by a strict grammar before evaluation. Lowercase booleans, identifiers, quotes, function calls, imports, variables, and arbitrary Python code are not allowed.

Allowed schedule-string ingredients:

- Exact `True` and `False`.
- Digits and decimal points.
- Comma and space.
- Parentheses `()`, brackets `[]`, multiplication `*`, addition `+`, subtraction `-`.

Examples:

| Problem | Fix |
| --- | --- |
| `true` or `false` | Use `True` or `False`. |
| `[hello]*1000` | Use numbers/booleans only; names are unsafe. |
| `np.ones(1000)` | Write an explicit safe expression such as `[1]*1000`. |
| `del a` or `__import__(...)` | Not supported and intentionally rejected. |
| YAML parsed the value oddly | Quote schedule expressions: `"[True]*500+[False]*500"`. |

## `ValueError: ... the schedule steps should be exactly 1000`

Cause: after safe evaluation, a list/tuple schedule must have exactly 1000 entries. The internal scheduler is always length 1000 even when `steps` is smaller or larger.

Fix examples:

- `"[True]*500+[False]*400"` has length 900; change to `"[True]*500+[False]*500"`.
- `"([1]+[2])*50"` passes the safe-string grammar but expands to length 100; change to `"([1]+[2])*500"`.
- A scalar such as `"1"`, `1`, `"True"`, or `True` is okay because it is repeated to 1000 entries.
- Prompt `weight`, prompt `schedule`, cut schedule fields, guidance-scale schedule fields, and `clip_models_schedules` all follow the same 1000-entry rule.

## Unsupported prompt schema or YAML `version` mismatch

Symptoms:

- `ValueError: unsupported text prompts schema: 1`
- `ValueError: unsupported text prompts schema: None`
- `TypeError: unsupported text prompts type: ...`

Causes and fixes:

1. Schema-v1 prompts must be a dict containing `version` and `prompts`.
2. In this runtime, `PromptPlanner` compares the version to the string `'1'`; use `version: "1"` in YAML.
3. `prompts` must be a non-empty list of prompt dictionaries.
4. Each prompt dictionary needs `text`; optional fields are `weight`, `schedule`, `clip_guidance`, and `spellcheck`.
5. A single string or list of strings is legacy prompt syntax, not schema-v1 syntax.

Correct schema-v1 YAML:

```yaml
text_prompts:
  version: "1"
  prompts:
    - text: broad composition first
      weight: 4
      schedule: "[True]*500+[False]*500"
    - text: fine details later
      weight: "[0]*500+[6]*500"
      clip_guidance: ["RN50::openai"]
```

Correct legacy YAML:

```yaml
text_prompts:
  - "broad composition:2"
  - "bad anatomy:-1"
```

## Legacy prompt colon mistakes

Legacy strings split on the last colon and convert the suffix with `float(...)`.

- Good: `"lighthouse at sea:2.5"`.
- Good: `"oversaturated, blurry:-1"`.
- Bad: `"prompt:[1]*1000"` because the suffix is not a float. Use schema v1 with `weight: "[1]*1000"`.
- Risky: raw prompt text ending with a colon expression that is not meant as weight. Remove the trailing colon or use schema v1 with explicit `text`.

Schema-v1 `text` is also parsed for a trailing `:weight`, but an explicit `weight` field overrides that parsed weight.

## `ValueError: `clip_guidance` contains unknown clip models: ...`

Cause: a schema-v1 prompt lists a `clip_guidance` model that is not included in `clip_models`.

Fix checklist:

1. Use exact model selector strings, e.g. `RN50::openai`, `ViT-B-32::openai`, `ViT-B-16::openai`.
2. Add every prompt-level `clip_guidance` model to top-level `clip_models`.
3. Do not assume short aliases are accepted for CLIP selectors; prefix matching is for diffusion model names, not prompt `clip_guidance` subset checks.
4. Remember that `clip_models_schedules` only controls whether a configured model runs at a step. It does not add that model to `clip_models`.

## A `clip_models_schedules` entry seems ignored

Cause: the runner only checks `clip_models_schedules[model_name]` while iterating configured `clip_models`. A schedule for a model that is not in `clip_models` is ignored.

Fix:

```yaml
clip_models:
  - RN50::openai
clip_models_schedules:
  RN50::openai: "[True]*400+[False]*600"
```

Then ensure each prompt's `clip_guidance` either omits the field or lists only configured CLIP models.

## Prompt is unexpectedly inactive

Use the active-prompt rule: a prompt contributes at a step only when the CLIP model is active, the prompt weight is nonzero, the prompt schedule is true, and the active CLIP model is in the prompt's `clip_guidance`.

Common causes:

- The prompt `weight` schedule is `0` at that step.
- The prompt `schedule` is `False` at that step.
- The requested CLIP model is not in the prompt's `clip_guidance`.
- The CLIP model's own `clip_models_schedules` entry is `False` at that step.
- The step index is the internal 0-based schedule index, not an arbitrary user-facing frame id.

Run the bundled validator with `--check-prompts --prompt-steps 0,500,999` and, if needed, `--clip-model MODEL` to summarize active prompt ids and weights without generation.

## Spellcheck warnings or failures

Symptoms:

- Warning: `Found misspelled tokens in the prompt`.
- Warning: `auto-corrected the following tokens`.
- `ValueError` with `Misspelled ... do you mean ...?`.

Behavior:

- Global `on_misspelled_token` defaults to `ignore`, which keeps tokens and warns.
- `correct` replaces tokens with the spellcheck suggestion and warns.
- `raise` fails fast with suggestions.
- Schema-v1 prompt field `spellcheck` overrides the global strategy for that prompt.
- The vocabulary includes common art/modifier words to reduce false positives, but unusual names can still be flagged.

Fixes:

- Use `spellcheck: ignore` for intentional names, invented words, or specialized terms.
- Use `spellcheck: raise` when validating a production prompt file and typos should block the run.
- Avoid unsupported strategy names. Runtime values other than `raise` or `correct` behave like warning/ignore, but the documented strategies are `ignore`, `correct`, and `raise`.

## `name_docarray` formatting errors or surprising names

Cause: `load_config` formats `name_docarray` with the full normalized config dict.

Examples:

```yaml
name_docarray: "study-{steps}-{perlin_init}"
```

This becomes something like `study-250-False`. If a placeholder references a missing key, formatting raises an error. Use accepted config keys only. If `name_docarray` is omitted, DiscoArt generates `discoart-{uuid}` or `discoart-{batch_name}-{uuid}`.

## `width_height` surprises

`load_config` coerces both `width_height` elements to integers:

```yaml
width_height: ["512", "768"]
```

normalizes to `[512, 768]`. Later generation code uses multiples of 64 internally; if the user is planning actual image dimensions or model-size quality tradeoffs, route to `artwork-generation`.

## `export_python` output misses an argument

`export_python` emits only non-default public args. It skips private keys and, by default, ignores `name_docarray` via `ignored_args=('name_docarray',)`. Pass a different `ignored_args` tuple if the generated snippet must preserve `name_docarray`.

If a value equals the default after normalization, it will not be shown. Use `show_config(..., only_non_default=False)` when the user wants a complete config table.

## String argument pulls a DocumentArray instead of reading a file

`load_config("path.yml")` reads a local YAML file. However, `show_config`, `save_config`, `save_config_svg`, and `export_python` treat a string input as a DocumentArray name and call pull semantics. If the user's intent is local-only and no network/cloud lookup, load the YAML path first:

```python
from discoart import load_config, show_config
cfg = load_config('path.yml')
show_config(cfg)
```

## Validator import or dependency failure

The bundled validator does not run diffusion, but it still imports DiscoArt config and prompt modules. If it fails before config validation:

1. Confirm the DiscoArt package is installed in the active Python environment.
2. Confirm runtime dependencies for config/prompt imports are installed, including YAML, DocArray, CLIP tokenizer dependencies, and spellchecker.
3. Disable remote model lookup with `DISCOART_DISABLE_REMOTE_MODELS=1` if running a custom wrapper; the bundled validator already does this.
4. Do not treat CUDA/model-cache failures as config validation failures; generation backend checks belong to `artwork-generation`.
