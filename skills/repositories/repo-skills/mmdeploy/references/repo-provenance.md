# Repo Provenance

```yaml
schema: disco.repo-provenance.v1
skill_id: mmdeploy
source_repository: https://github.com/open-mmlab/mmdeploy.git
source_commit: 3f8604bd72e8e15d06b2e0552fe2fdb8f8de33c4
source_branch: main
package_name: mmdeploy
package_version: 1.3.1
source_state: tracked source files clean at extraction; generated skills/ artifacts are not part of the source-evidence baseline
created_for: repo-specific DisCo operating skill, do-not-import policy
```

## Evidence baseline

The skill distills public repository evidence from these relative paths:

- `README.md`, `docs/en/get_started.md`, and `demo/README.md` for the high-level deployment and SDK story.
- `docs/en/02-how-to-run/convert_model.md`, `quantize_model.md`, `profile_model.md`, and `useful_tools.md` for conversion, quantization, profiling, and CLI behavior.
- `docs/en/05-supported-backends/*.md` for backend installation, runtime, custom-op, and platform guidance.
- `docs/en/06-custom-ops/*.md` and `docs/en/07-developer-guide/*.md` for custom ops, rewriters, partitioning, new backend/codebase support, tests, and regression workflows.
- `docs/en/sdk_usage/*`, `mmdeploy/backend/sdk/*`, and `mmdeploy/apis/sdk/*` for SDK model-directory and runtime patterns.
- `mmdeploy/apis/*`, `mmdeploy/backend/*`, `mmdeploy/utils/*`, `mmdeploy/core/*`, `mmdeploy/pytorch/*`, and `mmdeploy/mmcv/*` for public APIs, backend managers, config utilities, and rewriter/operation behavior.
- `tools/deploy.py`, `tools/check_env.py`, `tools/test.py`, `tools/profiler.py`, `tools/regression_test.py`, `tools/generate_md_table.py`, `tools/sdk_analyze.py`, and quantization helpers for bundled script decisions.
- `tests/test_apis/*`, `tests/test_core/*`, `tests/test_backend/*`, `tests/test_mmcv/*`, `tests/test_ops/*`, `tests/test_pytorch/*`, and `tests/test_utils/*` for native verification candidates and failure-mode evidence.

## Installed-package inspection baseline

The production inspection verified the installed package surface for `mmdeploy` 1.3.1 with `mmengine`, `mmcv`, `torch`, `torchvision`, `onnx`, and repository runtime/build dependencies. CPU TorchScript backend-manager availability was verified. Optional vendor backends and SDK runtime packages were not installed for the selected minimum inspection scope.

## Refresh guidance

Refresh this skill when any of these change:

- MMDeploy package version, backend manager availability, backend config schema, or public APIs under `mmdeploy/apis`, `mmdeploy/backend`, or `mmdeploy/utils`.
- Deployment config naming or expected work-directory artifact names.
- SDK runtime model-directory JSON schema or task-class mapping.
- Rewriter, symbolic, custom-op, partition, or test helper behavior.
- Validation/profiler/regression CLI flags or report formats.

When refreshing, compare the current repository commit and package version against this provenance file before trusting the existing routes.
