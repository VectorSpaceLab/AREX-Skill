# Workflow map

Use this page to decide which route to open first for a natural user request.

## Common workflows

| User intent | Start here | Why |
| --- | --- | --- |
| Build a causal decoder, seq2seq model, or vision wrapper | `sub-skills/core-models/SKILL.md` | This route owns the base constructors and attention-feature choices. |
| Turn token ids into autoregressive generation or beam search | `sub-skills/sequence-workflows/SKILL.md` | Wrapper selection, caching, and generation semantics live there. |
| Work with continuous values, xVal, XL recurrence, latent objectives, or preference optimization | `sub-skills/sequence-workflows/SKILL.md` | Those are wrapper-level workflows rather than base constructor choices. |
| Understand or adapt a `train_*.py` file | `sub-skills/training-recipes/SKILL.md` | Recipe dependencies, dataset assumptions, and smoke guidance live there. |
| Only verify that the installed package works | `scripts/probe_backend.py` and `scripts/smoke_models.py` | These are the fastest cross-cutting checks. |

## Quick examples

### Text generation / encoder-decoder
- Choose `core-models` for `TransformerWrapper`, `Encoder`, `Decoder`, `PrefixDecoder`, or `XTransformer`.
- Switch to `sequence-workflows` when you need `AutoregressiveWrapper`, `XLAutoregressiveWrapper`, or a generation API.

### Vision wrapper
- Choose `core-models` for `ViTransformerWrapper`, patch geometry, and image-to-logits/image-to-embedding behavior.

### Continuous or mixed discrete/continuous data
- Choose `sequence-workflows` for `ContinuousTransformerWrapper`, `ContinuousAutoregressiveWrapper`, `XValTransformerWrapper`, and `XValAutoregressiveWrapper`.

### Recipe or smoke run
- Choose `training-recipes` for enwik8 scripts, copy-task smoke, or dependency cataloging.
- Prefer the bundled copy-task smoke before any long recipe.

## Cross-skill reminders

- `core-models` picks the base stack first; `sequence-workflows` adds higher-level objectives and generation rules.
- `training-recipes` should be treated as long-running examples, not importable libraries.
- If a request mixes constructor choices with a wrapper objective, settle the constructor in `core-models` first, then finish the objective in `sequence-workflows`.
