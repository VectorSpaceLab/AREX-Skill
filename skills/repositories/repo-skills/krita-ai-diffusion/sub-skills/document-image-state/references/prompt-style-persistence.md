# Prompt, Style, Metadata, and Persistence Reference

## Prompt text helpers

`ai_diffusion.text` provides behavior used before workflow payload creation:

- `strip_prompt_comments(prompt)`: removes `#` comments.
- `merge_prompt(prompt, style_prompt, language="")`: inserts prompt into style
  prompt templates such as `cinematic {prompt}`.
- `extract_loras(prompt, file_collection)`: finds `<lora:name:weight>` tokens,
  resolves names against available files/metadata, removes tags from prompt,
  and returns LoRA inputs.
- `eval_wildcards(text, seed)`: deterministically chooses from `{a|b|c}` using
  seed.
- `extract_layers` / `replace_layers`: handles `<layer:name>` prompt tokens and
  replaces them with image-reference text after layer collection.
- attention selection/edit helpers for prompt editor UI.
- `create_img_metadata(params)`: builds generation metadata text for saved PNGs
  and history.

## LoRA behavior

LoRAs can come from:

- Prompt tags: `<lora:PINK_UNICORNS:0.77>`.
- Prompt tags without weights, using file metadata default strength.
- Style-defined LoRAs in style JSON.
- Server/discovered model files and remote file library entries.

A LoRA not appearing in final generation may be a prompt parsing issue, a style
configuration issue, or a server model-discovery issue. Use this sub-skill for
parsing and `server-resources` for availability.

## Wildcards and determinism

Wildcard expressions such as `{apple|banana}` are evaluated with the job seed.
When `fixed_seed` is true and `batch_count` is greater than one, tests show the
plugin can produce deterministic but varied batch prompts by evaluating per job
seed. Preserve seed information when debugging prompt reproducibility.

## Style objects

`Style` and `Styles` manage style JSON files. Important settings include:

- checkpoint list and preferred checkpoint selection,
- positive style prompt and negative prompt templates,
- sampler preset, live sampler, CFG, live CFG, steps, live steps,
- VAE/clip skip/performance flags,
- style LoRA list and strengths,
- whether a style is builtin or user-created.

`SamplerPresets` maps sampler preset names to sampler, scheduler, steps, and CFG
settings. If a sampler name is missing, check user preset files and stub/default
preset behavior.

## Metadata

Generated metadata includes positive/negative prompt, evaluated wildcard text,
final style-merged prompt, seed, size, model/checkpoint info, sampler/CFG/steps,
and region prompt metadata when present. PNG metadata writing is handled by
`Image.save_png_with_metadata`/related helpers.

When sharing diagnostics, avoid embedding private image data. A sanitized
metadata summary plus request field names is usually enough.

## Persistence

Persistence modules store selected UI/model state in settings files or Krita
document data. Treat persisted properties as user preferences/document state;
transient properties such as current progress, errors, and connection state
should not be saved as durable workflow facts.

If a setting appears reset:

1. Check whether the property is marked persisted.
2. Check whether the document or global settings file is the owner.
3. Check enum string parsing; invalid enum names fall back to defaults.
4. Check whether a style/workflow ID changed and invalidated associated params.
