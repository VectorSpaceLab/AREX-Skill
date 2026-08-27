# AIMET repository provenance

## Source snapshot

- Repository: AIMET / AI Model Efficiency Toolkit
- VCS: git
- Commit: `35ce986de4413128a618ae6161ffe9e7e42cd0ab`
- Branch: `develop`
- Exact tag: none detected during production
- Package version: `2.37.0` from package metadata
- Working tree state during production: dirty only because the generated `skills/` tree was untracked
- Remote URL: omitted-private-or-unknown

## Included evidence

The skill was distilled from these repository-relative evidence areas:

- `README.md`
- `pyproject.toml`
- `CMakeLists.txt`
- `packaging/version.txt`
- `packaging/dependencies/README.md`
- `packaging/dependencies/*`
- `TrainingExtensions/common/src/python/aimet_common/`
- `TrainingExtensions/torch/src/python/aimet_torch/`
- `TrainingExtensions/onnx/src/python/aimet_onnx/`
- `TrainingExtensions/torch/test/python/`
- `TrainingExtensions/onnx/test/python/`
- `Docs/overview/install/`
- `Docs/apiref/`
- `Docs/snippets/`
- `Docs/techniques/`
- `Docs/ptq_techniques/`
- `Docs/tutorials/`
- `Examples/README.md`
- `Examples/torch/`
- `Examples/onnx/`
- `scripts/README.md`
- `scripts/all/build_and_test.py`
- `scripts/environment/build_aimet.sh`
- `scripts/environment/setup_genai.sh`
- `GenAILab/README.md`
- `GenAILab/CONFIG.md`
- `GenAILab/__main__.py`
- `GenAILab/conftest.py`
- `GenAILab/bench/yaml_config_parser.py`
- `GenAILab/bench/summary.py`
- `GenAILab/bench/torch/test_genai.py`
- `GenAILab/bench/onnx/test_genai.py`
- `.github/workflows/genai-scorecard.yaml`
- `.github/actions/genai-test/action.yml`
- `scripts/all/download_genai_checkpoint.sh`
- `scripts/all/resolve_genai_config.sh`
- `scripts/kube/launch_pod.sh`
- `scripts/kube/sync_pod.sh`
- `scripts/kube/stop_pod.sh`
- `scripts/kube/install_deps.sh`
- `scripts/kube/dev.sh`
- `scripts/kube/kubectl_rsync.sh`
- `Docs/tutorials/on_target_inference.rst`
- `AIMETRegression/evaluation/eval_qnn.py`

## Excluded or bounded evidence

- `NightlyTests/`, `Jenkins/`, and broad `AIMETRegression/` suites remain CI/regression-scale assets; this skill uses only the QNN evaluation utility as operating evidence.
- GenAILab, cluster/Pod, model-download, GitHub Actions, AWS/S3, SAML, and Qualcomm SDK workflows are now covered as self-contained runtime guidance and helper entry points, but real execution is bounded by external credentials, datasets, remote quota, SDK installation, and user approval.
- Build outputs, caches, generated docs output, environments, and `skills/tests/` review artifacts are not source evidence for this public runtime skill.

## Refresh triggers

Refresh this skill when AIMET changes package names, major `QuantizationSimModel` signatures, encoding file formats, source-build flags, dependency files, ONNX Runtime provider behavior, model-preparer requirements, compression APIs, GenAILab CLI/config/registry semantics, GitHub scorecard workflow inputs, cluster script contracts, S3 checkpoint layout, QNN/QAIRT command expectations, or AI Hub helper APIs.
