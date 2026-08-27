---
name: customization-and-development
description: "Extend ModelScope with custom pipelines, registered components,
  safe scaffolding, contributor workflow, test levels, and trust-boundary
  guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Customization and Development

Use this sub-skill when the user wants to extend ModelScope itself or create a
custom ModelScope-facing pipeline/model/preprocessor wrapper. Keep the workflow
safe by default: plan scaffolding before running it, avoid downloads and
training during design checks, and treat remote code/plugin execution as an
explicit trust decision.

## Route first

- Existing pipeline inference, `pipeline()`, `Model.from_pretrained()`, devices,
  batching, and output keys: use `../pipelines-and-models/SKILL.md`.
- Training or evaluating an existing model/trainer configuration: use
  `../training-and-evaluation/SKILL.md`.
- Generic repository maintenance unrelated to ModelScope extension points: do
  not use this sub-skill unless the user is editing a ModelScope checkout.

## Read the right reference

- Custom pipeline/model/preprocessor design, CLI template arguments,
  `configuration.json` shape, registration patterns, and trust gates:
  `references/extension-workflows.md`.
- Contributor workflow, test levels, focused test selection, linter/pre-commit,
  git-lfs/submodule data notes, and repository-development guardrails:
  `references/contributor-guidance.md`.
- Error diagnosis for template generation, registry misses, config trust gates,
  plugin loading, focused tests, and optional backend gaps:
  `references/troubleshooting.md`.

## Safe planner

Before running ModelScope's scaffold command, create a dry-run command plan:

```bash
python scripts/pipeline_template_plan.py \
  --task_name my-task \
  --model_name MyCustomModel \
  --preprocessor_name MyCustomPreprocessor \
  --pipeline_name MyCustomPipeline \
  --filename ms_wrapper.py \
  --save_file_path ./custom_pipeline \
  --configuration_path ./custom_pipeline
```

The bundled planner prints the `modelscope pipeline --action create ...` command
only. It validates that `--filename` ends with `.py`; it does not create files,
import ModelScope, contact the network, download models, train, or overwrite
anything.

## Operating guardrails

1. Import-time side effects matter. The stock template contains top-level code
   that writes `configuration.json` when the generated Python file is imported
   or run. Inspect and refactor generated code before using it as a package
   module.
2. Registration is import-driven. Decorators such as `@PIPELINES.register_module`
   run only after the wrapper/plugin module has been imported, or after a
   packaged ModelScope module has been indexed and lazily imported.
3. Match all routing keys: `task`/registry group, decorator `module_name`, and
   `configuration.json` `type` fields must agree.
4. Prefer JSON/YAML configuration for passive data. Python configs and remote
   model code execute Python and require an explicit trust decision.
5. Treat `plugins`, `allow_remote`, and `trust_remote_code=True` as code
   execution boundaries. Do not enable them merely to bypass an error.
6. CUDA/domain-specific execution is optional and unverified in this production
   scope. Provide CPU/local smoke checks first and record what remains
   unverified.
