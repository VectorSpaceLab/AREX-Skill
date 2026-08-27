---
name: model-porting
summary: Add or adapt FastVideo model families, model configs, pipeline wiring,
  checkpoint converters, and local parity tests.
description: "Use when a task asks to port a model, add a model family, update
  configs/presets/registries, write checkpoint conversion, or extend local model
  parity tests in FastVideo."
license: Apache 2.0
metadata:
  disco-role: operating
disable-model-invocation: true
---

# FastVideo Model Porting

## Activate this subskill for

- New or changed files under `fastvideo/models/`.
- Model or architecture config changes under `fastvideo/configs/models/`.
- Pipeline config or preset changes under `fastvideo/configs/pipelines/` or
  `fastvideo/pipelines/basic/`.
- Registry updates in `fastvideo/registry.py`.
- New or changed checkpoint converters under `scripts/checkpoint_conversion/`.
- Local model-family smoke/parity tests under `tests/local_tests/`.

Do not use this subskill for pure server/API work unless the public API change is
required by a model port. Load `../inference-serving/SKILL.md` for serving
contract changes.

## Read first

Read all nearest `AGENTS.md` files before editing. Model ports commonly require:

- `fastvideo/AGENTS.md`
- `fastvideo/models/AGENTS.md`
- `fastvideo/configs/AGENTS.md`
- `fastvideo/pipelines/AGENTS.md`
- `fastvideo/tests/AGENTS.md`
- `fastvideo/tests/ssim/AGENTS.md` if output quality is part of acceptance
- `scripts/checkpoint_conversion/AGENTS.md` for converters

Useful source evidence and docs:

- `docs/inference/configuration.md`
- `docs/inference/support_matrix.md`
- `docs/contributing/coding_agents.md`
- `examples/inference/basic/README.md`
- `scripts/checkpoint_conversion/*.py`
- Existing model-family packages under `fastvideo/models/` and
  `fastvideo/pipelines/basic/`.
- Existing local-test READMEs under `tests/local_tests/*/README.md`.

Existing `.agents/skills/add-model*` files in this checkout are evidence for
prior local workflow expectations only; they are not the output target for this
DisCo skill.

## Code map

- Model implementations: `fastvideo/models/`.
- Model config dataclasses and mapping rules: `fastvideo/configs/models/`.
- Pipeline config dataclasses: `fastvideo/configs/pipelines/`.
- Pipeline composition and model-family runtime: `fastvideo/pipelines/basic/`.
- Registry detection/resolution: `fastvideo/registry.py`.
- Public generation parameter surfaces: `fastvideo/api/` and
  `fastvideo/fastvideo_args.py`.
- Checkpoint conversion: `scripts/checkpoint_conversion/`.
- Regression and parity suites:
  - `tests/local_tests/*/README.md`
  - `fastvideo/tests/golden_gate/`
  - `fastvideo/tests/train/models/`
  - relevant inference/SSIM tests when output behavior changes.

## Porting workflow

1. Identify the source model family, target task type, modalities, official
   checkpoint layout, and expected output contract.
2. Decide which FastVideo layers are affected:
   - model module only;
   - model config only;
   - pipeline config/preset;
   - basic pipeline runtime;
   - registry detection;
   - checkpoint conversion;
   - public API/schema fields.
3. Compare against a nearby supported family before adding new abstractions.
   Prefer existing naming, loader, dtype, config, registry, and test patterns.
4. For config dataclasses, preserve `param_names_mapping` and checkpoint/config
   key compatibility. Do not add fields only to examples; make the schema and
   parser path understand them.
5. For pipeline wiring, verify that `model_index.json` class names and required
   modules resolve to registered pipeline classes. Loader-time changes must live
   in the load path, not in a post-load hook that runs too late.
6. For converters, map official names/shapes/dtypes explicitly. Add a bounded
   smoke that can validate key coverage or shape translation without a full
   model run when possible.
7. Add or update local tests/READMEs for the model family. If a test needs model
   assets, credentials, or large downloads, document those preconditions and
   provide a smaller import/config/converter check.
8. Escalate to GPU generation, SSIM, or training parity only when the target port
   requires numeric/output evidence and the user accepts the runtime budget.

## Registry and pipeline pitfalls

- Runtime pipeline resolution is exact. A `model_index.json` `_class_name` must
  match a registered `EntryClass.__name__` or a supported wrapper/alias.
- Registry detection helps locate support; it does not automatically make a
  pipeline class executable.
- New generation kwargs should be declared in the API/schema/sampling path before
  presets or examples rely on them.
- Do not migrate a shipped legacy training pipeline to the modular trainer while
  porting a model unless explicitly asked.
- Keep model tests and local tests scoped to the family being added; broad
  repository test sweeps are expensive and often unnecessary.

## Suggested verification ladder

Start narrow:

```bash
python -m pip check
python - <<'PY'
import fastvideo
from fastvideo import PipelineConfig, SamplingParam, VideoGenerator
print(fastvideo.__version__, PipelineConfig, SamplingParam, VideoGenerator)
PY
python skills/disco/fastvideo/scripts/select_fastvideo_tests.py model-porting
```

Then choose target-specific tests:

```bash
pytest fastvideo/tests/api/test_cli_translation.py -q
pytest fastvideo/tests/contract/test_ci_test_collection.py -q
pytest fastvideo/tests/golden_gate/ -q
pytest fastvideo/tests/train/models/ -q
```

For checkpoint converters, prefer a converter-specific smoke first. Examples to
adapt from current repository style:

```bash
python scripts/checkpoint_conversion/wan_to_diffusers.py --help
python scripts/checkpoint_conversion/convert_ltx2_weights.py --help
```

For local parity, read the exact model README before running anything:

```bash
find tests/local_tests -maxdepth 2 -name README.md -print
# then run only the README command matching the target model/backend
```

Escalate only after confirming assets and budget:

```bash
pytest fastvideo/tests/ssim/ -vs
pytest fastvideo/tests/inference/ -q
fastvideo generate --config <model-smoke-config.yaml>
```

## Handoff checklist

When finishing a model-porting task, report:

- model family and source checkpoint evidence;
- files changed in models/configs/pipelines/registry/converters/tests;
- conversion mapping or why no converter was needed;
- config and public API fields added or intentionally unchanged;
- exact tests run and any heavy tests skipped with reason;
- backend and model asset assumptions for follow-up verification.
