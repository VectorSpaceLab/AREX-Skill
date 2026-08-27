---
name: training-configuration
description: "Configure AlphaFold 3 training datasets, Trainer/DataLoader
  construction, YAML/Pydantic factories, optimization, evaluation, and bounded
  diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training configuration

Use this sub-skill for `Trainer`, its wrapped `DataLoader`, dataset selection,
Pydantic/YAML configuration, conductor phases, checkpointing, optimizer/EMA
choices, Fabric setup, and bounded training preflight. Start with
[`scripts/validate_config.py`](scripts/validate_config.py); it parses and
validates a YAML document without constructing a model or trainer.

Read the smallest applicable reference:

- [`references/trainer-api.md`](references/trainer-api.md) for public classes,
  collation, lifecycle, optimizer/EMA, logging, evaluation, and checkpoints.
- [`references/configuration.md`](references/configuration.md) for model,
  trainer, dataset, weighted-sampler, conductor, extra-field, and dotpath
  contracts.
- [`references/workflows.md`](references/workflows.md) for safe preflight,
  direct-API, YAML, multi-phase, collation, resume, and bounded diagnostics.
- [`references/troubleshooting.md`](references/troubleshooting.md) for
  validation failures, backend/precision problems, checkpoint hazards, and
  resource stop conditions.

## Routing boundaries

- Route generic `Alphafold3Input`, atom feature semantics, and input conversion
  to [`input-representation`](../input-representation/SKILL.md).
- Route mmCIF/PDB/MSA/template preparation, cropping, and dataset-scale curation
  to [`data-pipeline`](../data-pipeline/SKILL.md).
- Route architecture, forward/loss versus sampling modes, and model shape or
  checkpoint internals to [`model-inference`](../model-inference/SKILL.md).
- Route Click, Gradio, and command construction to
  [`cli-serving`](../cli-serving/SKILL.md).

## Operating rules

1. Establish the model dimensions, training objective, dataset kind, train/valid
   /test split policy, accelerator, precision, checkpoint policy, and an explicit
   step/batch budget before construction.
2. Validate the selected YAML root and optional dotpath first. A successful
   parse is not a successful trainer plan: inspect warnings for missing paths,
   extra keys, conflicting dataset sources, unsafe overwrite, and unbounded
   resource settings.
3. Keep structure preparation separate from training. This skill consumes
   ready `PDBInput`/`AtomInput` datasets; it does not curate large databases or
   define molecule/atom feature semantics.
4. Construct `Trainer` only after a human-approved bounded plan. Construction
   launches Lightning Fabric and creates the checkpoint directory; the validator
   deliberately does neither. Never use a full production model or dataset for
   a smoke check.
5. Treat `use_ema`, `fp16`, `distributed_eval`, optimizer switches, and other
   extra trainer keys as runtime options, not as proof that a run is affordable
   or that a backend is available. Record the actual Fabric accelerator and
   precision selected at runtime.
6. For a conductor, validate every phase and the exact `training_order` before
   selecting a phase. Root checkpoint folder/prefix values are composed with
   each phase; do not reuse a phase output namespace accidentally.

The bundled validator is intentionally read-only: it does not instantiate
`Trainer`, call a factory's `create_instance`, call `Fabric.launch`, create
checkpoint/log directories, download data, train, or start a server.
