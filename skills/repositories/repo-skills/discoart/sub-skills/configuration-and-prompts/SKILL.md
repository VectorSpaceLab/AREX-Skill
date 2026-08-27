---
name: configuration-and-prompts
description: "Use this sub-skill for DiscoArt config files, prompt schema v1,
  schedule strings, CLIP guidance routing, cheatsheets, and config import/export
  helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# DiscoArt Configuration and Prompts

Use this sub-skill when the user needs to inspect, validate, write, normalize, or explain DiscoArt configuration and prompt behavior without starting an artwork generation run.

## Triggers

- Validate or repair a DiscoArt YAML/dict config.
- Write `text_prompts` using schema version `"1"` or legacy `"text:weight"` strings.
- Explain prompt schedules, prompt weights, `clip_guidance`, or which prompts are active at selected steps.
- Diagnose `unknown argument`, unsupported prompt schema/type, unsafe scheduling string, wrong 1000-step schedule length, or CLIP guidance mismatch errors.
- Use `load_config`, `save_config`, `show_config`, `save_config_svg`, `export_python`, or `cheatsheet`.
- Convert a config between YAML-like dict form and Python `create(...)` keyword arguments while preserving DiscoArt semantics.

## Quick workflow

1. **Classify the request.** Stay here for config/prompt validation and conversion. Route actual diffusion/image creation to sibling `artwork-generation`; route `python -m discoart config`, `python -m discoart create`, service, Docker, or endpoint usage to sibling `cli-and-serving`.
2. **Load normalized facts.** Use `references/configuration-and-prompts.md` for helper signatures, accepted keys, default values, cut schedule groups, prompt schema, schedule grammar, and active-prompt rules.
3. **Validate safely.** Prefer `scripts/validate_discoart_config.py --config CONFIG.yml --check-prompts --show-non-default` for a no-generation check. Add `--json` when another tool needs structured output.
4. **Explain errors with fixes.** Use `references/troubleshooting.md` to map runtime errors to likely config, schedule, prompt schema, spellcheck, or CLIP-model causes.
5. **Hand off if execution is requested.** A valid config can be passed to Python `create(**load_config(path))` under `artwork-generation`, or to CLI/service workflows under `cli-and-serving`; do not start generation from this sub-skill.

## Owned capabilities

- Config API helpers: `load_config`, `save_config`, `show_config`, `save_config_svg`, `export_python`, `cheatsheet`.
- Default YAML facts, cut schedule groups, selected parameter docstring facts, and config normalization rules.
- Prompt schema version `"1"`, legacy prompt strings, scalar and scheduled prompt weights, per-prompt schedules, per-prompt spellcheck, and `clip_guidance` subset validation.
- Safe schedule-string grammar and expansion to exactly 1000 steps for schedules used by cuts, guidance scales, secondary model use, prompt weights/schedules, and CLIP model schedules.

## Boundaries and sibling routing

- **Actual diffusion generation:** use sibling `artwork-generation` for `create()`, model/cache/CUDA behavior, output images, `DocumentArray` results, `go_big()`, skip/stop events during a run, or W&B result logging.
- **CLI and serving:** use sibling `cli-and-serving` for `python -m discoart config`, `python -m discoart create`, `python -m discoart serve`, Jina Flow, service endpoints, Docker, or persistent server behavior.
- **Reference-only source tooling:** do not bundle or run the upstream docstring generator as a runtime helper; the distilled docstring facts in this sub-skill are sufficient.
