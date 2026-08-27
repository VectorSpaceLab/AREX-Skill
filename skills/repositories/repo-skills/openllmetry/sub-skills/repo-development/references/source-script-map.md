# Source Script Map

This sub-skill does not copy maintainer scripts into the runtime tree unless they are safe to reuse locally.
The source scripts below are kept as reference-only because they are release-only, generate code, or mutate files.

| Source script | Decision | Reason | Runtime treatment |
| --- | --- | --- | --- |
| `scripts/build-release.sh` | reference-only | Removes `tool.uv.sources` from the current `pyproject.toml` and then builds. That is a release-only mutation and is risky as a general checkout-local helper. | Keep the caveat in troubleshooting; do not call it as a routine maintenance step. |
| `scripts/generate-models.sh` | reference-only | Thin wrapper around evaluator-model code generation. It requires an external Swagger file and writes generated SDK files. | Describe the maintenance caveat and the required inputs; do not bundle it as a normal runtime helper. |
| `scripts/codegen/generate_evaluator_models.py` | reference-only | Uses `datamodel-code-generator`, a temporary schema, and generated output directories. It is a mutating codegen utility, not a safe generic helper. | Keep the codegen prerequisites and output contract in docs only. |

## Bundled helper added here

- `scripts/list_openllmetry_projects.py` is a new safe metadata-only helper for this sub-skill.
- It is not copied from a source script.
- It reads package metadata, source roots, tests, entry points, and local source mappings only.

## Why nothing else was bundled

- The maintainer scripts above either change package files, depend on external Swagger/codegen tools, or are too specific to release maintenance.
- The rest of the repo's scripts are either unrelated to package maintenance or are better represented as command patterns in the references.
