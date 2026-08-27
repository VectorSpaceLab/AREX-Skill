# Repository provenance

schema: `disco.repo-provenance.v1`

- source repository: SOLO (`mmdet` distribution; PyTorch/MMDetection v1-era)
- source commit: `f4cd03b9404e3bd84ca0be45966fb61d20d2efe6`
- source branch: `master`
- exact tag: none observed at the source commit
- source checkout state: clean at inspection time except for generated skill/artifact files created by this run under `skills/`
- package version evidence: `mmdet.__version__ == 1.0.0+f4cd03b`; `short_version == 1.0.0`
- documented dependency anchor: `mmcv==0.2.16`; PyTorch 1.1+ documented, with versions >=1.5 not tested by the source project
- public evidence paths used: `README.md`, `setup.py`, `requirements/runtime.txt`, `requirements/build.txt`, `requirements/optional.txt`, `docs/INSTALL.md`, `docs/GETTING_STARTED.md`, `docs/TECHNICAL_DETAILS.md`, `docs/MODEL_ZOO.md`, `docs/ROBUSTNESS_BENCHMARKING.md`, `mmdet/apis/`, `mmdet/core/`, `mmdet/datasets/`, `mmdet/models/`, `mmdet/ops/`, `mmdet/utils/`, `configs/`, `demo/`, `tools/`, and selected `tests/`
- excluded evidence: `.git/`, generated/cache/build outputs, downloaded weights/data, CI/release scaffolding, and the separate `paddlepaddle/` implementation
- refresh signal: refresh this skill when public APIs, config conventions, custom operators, dependency anchors, or the repository's major workflow scripts change; do not infer freshness from the generated skill alone
- runtime self-containment: generated references and helpers are distilled/adapted into this skill tree and do not require the original checkout
