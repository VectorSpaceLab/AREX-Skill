# Megatron-LM testing reference

This reference distills the repo's unit-test, functional-test, and recipe conventions. Use it to choose the smallest test that matches a code change, reproduce a failure with CI parity, or add/modify recipe YAML without relying on repository docs.

## Test layout and responsibilities

| Area | Purpose | Typical owner task | CI/runtime shape |
|---|---|---|---|
| `tests/unit_tests/` | Pytest-based API and behavior tests for Megatron Core, training helpers, checkpointing, inference, RL, and utilities. | Add or update fast unit coverage for code behavior. | Launched through `python -m torch.distributed.run`; many tests initialize distributed state and expect GPUs. |
| `tests/functional_tests/test_cases/<model>/<case>/` | End-to-end training/inference validation cases. Each case has `model_config.yaml`; numerical cases also have `golden_values_<environment>_<platform>.json`. | Add or update a complete training/inference recipe and its golden values. | Shell runner trains for configured steps, extracts metrics, then rank 0 validates actual values against goldens. |
| `tests/test_utils/recipes/<platform>/*.yaml` | CI workload expansion. Recipes select test cases by scope, environment, platform, cadence, repeat count, nodes, GPUs, and build image. | Wire unit/functional cases into H100/GB200/A100 CI lanes. | Parsed into individual workloads by a YAML recipe parser; GitHub and GitLab use different scope vocabularies in some lanes. |
| `tests/test_utils/python_scripts/` | CI orchestration helpers: recipe expansion, golden download/compare, GitHub/GitLab job launch, notifications, and dashboards. | Use through workflows; do not copy large CI helpers into ad hoc scripts. | Some helpers require GitHub/GitLab tokens or CI-only environment variables. |

## Unit-test invocation

CI-parity unit-test runs use `torch.distributed.run`, not bare `pytest`, because the unit suite can initialize process groups and rank-aware fixtures.

```bash
# Full unit suite on 8 GPUs.
uv run python -m torch.distributed.run --nproc-per-node 8 -m pytest -q tests/unit_tests

# One file.
uv run python -m torch.distributed.run --nproc-per-node 8 -m pytest -q \
  tests/unit_tests/models/test_gpt_model.py

# One node id.
uv run python -m torch.distributed.run --nproc-per-node 8 -m pytest -q \
  tests/unit_tests/models/test_gpt_model.py::TestGPTModel::test_constructor

# Name filter.
uv run python -m torch.distributed.run --nproc-per-node 8 -m pytest -q \
  tests/unit_tests -k optimizer
```

For CI-bucket parity, use the same runner shape the CI bucket uses:

```bash
bash tests/unit_tests/run_ci_test.sh \
  --tag latest \
  --environment dev \
  --bucket 'tests/unit_tests/transformer/**/*.py' \
  --log-dir ./assets_dir/logs/1/
```

Important pytest markers:

| Marker | Meaning | CI effect |
|---|---|---|
| `internal` | Exercises private/internal behavior. | Skipped for legacy-tag tests. |
| `flaky_in_dev` | Flaky in dev container. | Excluded from the default dev environment. |
| `flaky` | Flaky in LTS container. | Excluded from the LTS environment. |
| `experimental` | Requires experimental flag. | Run separately with `--experimental`. |
| `launch_on_gb200` | Unit test is allowed on GB200. | GB200 unit recipe uses a catch-all bucket and filters to this marker. |

When adding a unit test:

1. Place it under an existing `tests/unit_tests/<area>/` bucket when possible.
2. Use markers to express environment/platform behavior rather than deleting coverage.
3. Run a focused distributed command locally or in a suitable container.
4. If a new CI bucket is required, add a recipe entry to the relevant unit-test recipe.

## Functional-test workflow

Functional tests are heavier than unit tests. A typical case includes:

- a case directory `tests/functional_tests/test_cases/<model>/<test_case>/`;
- `model_config.yaml` with `MODEL_ARGS`, `ENV_VARS`, `TEST_TYPE`, and optional `MODE`/`TEST_EVALUATION`;
- golden JSONs named by environment and platform, for example `golden_values_dev_dgx_h100.json` or `golden_values_dev_dgx_gb200.json`;
- one or more recipe entries that place the case into H100, GB200, A100, MR, nightly, or weekly lanes.

Functional runner behavior to remember:

- Lightweight mode changes short training runs to a few steps and skips golden comparison. It is useful for fast feedback but does not validate numerical correctness.
- Normal functional runs repeat the case (`n_repeat`, usually 5) and compare 100-step or configured trajectories against golden values.
- For checkpoint-resume and frozen-resume cases, the runner writes and reloads checkpoints between phases before validating trajectories.
- Only rank 0 performs the pytest golden comparison; inspect rank 0 first, then other ranks for distributed failures.

When adding a functional test:

1. Create the case directory and `model_config.yaml`.
2. Choose model owner path (`gpt`, `moe`, `mamba`, `hybrid`, `bert`, `t5`, inference, RL, or multimodal) based on the runner and model config, not the PR title alone.
3. Add a recipe entry under the platform directory. Use `Run functional tests` on the PR to generate full-run goldens.
4. Download generated goldens from the successful CI run, validate they contain only finite values, and commit the golden JSON files.

## Recipe YAML schema and scope vocabulary

A functional recipe has a top-level `spec` template plus a nested `products` list. The parser expands list-valued fields into individual workload specs.

Minimal pattern:

```yaml
type: basic
format_version: 1
maintainers: [mcore]
loggers: [stdout]
spec:
  name: "{test_case}_{environment}_{platforms}"
  model: gpt
  build: mcore-pyt-{environment}
  nodes: 1
  gpus: 8
  n_repeat: 5
  platforms: dgx_h100
  script: |-
    # runner invocation templated with {test_case}, {environment}, {platforms}, {n_repeat}
products:
  - test_case: [my_case]
    products:
      - environment: [dev]
        scope: [mr-github]
        platforms: [dgx_h100]
```

Common fields:

| Field | Meaning | Notes |
|---|---|---|
| `environment` | `dev` or `lts`. | `dev` is default for PR work; LTS must be explicit. |
| `scope` | Suite/cost/trigger label. | May include legacy values (`mr`, `mr-github`) or L-tier values (`L0`, `L1`, `L2`, `L3`). |
| `cadence` | Trigger filter: `pr`, `nightly`, `mergegroup`, or `weekly`. | If omitted, most recipe rows default to PR + nightly + mergegroup; labels can bypass cadence filtering. |
| `platforms` | Target hardware label, e.g. `dgx_h100` or `dgx_gb200`. | Use exact spelling; the summarizer script can catch typos. |
| `nodes`, `gpus` | Cluster shape. | H100 recipes typically use 8 GPUs per node; GB200 1-node recipes use 4 GPUs per node. |
| `n_repeat` | Number of repeats. | Full functional PR tests usually use 5; lightweight label path uses 1. |
| `time_limit` | Per-workload time budget. | Increase only when the workload genuinely needs it. |

Scope conventions:

| Scope | Meaning | Use |
|---|---|---|
| `mr-github-slim` or alias `L0` | Slim default PR subset. | Default unlabeled PR coverage. Keep this small. |
| `mr-github` or alias `L1` | Full GitHub PR functional scope. | Add for normal PR functional validation. |
| `mr` | Internal GitLab MR scope. | Use for internal full functional lanes, not as a GitHub alias. |
| `L0-smoke` | Lightweight smoke scope. | Used to gate functional H100/GB200 jobs quickly. |
| `nightly` or alias `L2` | Nightly suite. | For broad coverage that should not block every PR. |
| `weekly` or alias `L3` | Weekly/release-scale suite. | Long-running or release-like tests. |
| `*-broken`, `*-disabled`, `mr-github-temp-disabled` | Discoverable disabled scopes. | Prefer suffixing/marking scope over deleting recipe entries. Include an issue reference when disabling a real regression. |

Use bundled `scripts/summarize_recipe_scopes.py` before and after recipe edits to confirm that expected scopes/platforms changed and no accidental typo appeared.

## H100 and GB200 recipe distinctions

- H100 functional recipes live under the H100 recipe directory and commonly specify `gpus: 8`, `platforms: dgx_h100`, and golden files with `dgx_h100` in the filename.
- GB200 one-node recipes use `gpus: 4`, `platforms: dgx_gb200`, and `_1node` test-case names when adapting an 8-GPU case to a 4-GPU node.
- For GB200 unit tests, the unit recipe uses one catch-all bucket narrowed by `launch_on_gb200`; adding a GB200 unit test usually means marking the test, not creating many new buckets.
- For GB200 functional 1-node variants, preserve global batch size when possible and adjust parallelism so the world-size formula fits 4 GPUs. Typical adaptations: reduce pipeline parallel size when `TP × PP > 4`; reduce expert parallel size from 8 to 4 when EP exceeds the one-node GPU count.
- H100/GB200 FP8 or Blackwell-specific behavior should not be claimed as locally verified unless the actual matching hardware ran the test. Static recipe review is not runtime validation.

## Test-selection decision table

| Change type | Minimum local/PR validation | Notes |
|---|---|---|
| Docs-only or comment-only | No label unless requested. | Keep PR small; CI may still run lint. |
| Python import reorder or style-only in `megatron/core`/`tests` | Formatter/isort plus targeted unit if behavior could change. | Run isort on edited Python imports. |
| Unit-test-only change | Targeted distributed pytest; PR label `Run tests` if CI parity is needed. | If adding GB200 marker, verify recipe selection. |
| New functional case or re-enabled broken case | `Run functional tests`. | Full run is needed to produce/validate goldens. |
| Model, optimizer, parallelism, checkpointing, MoE, or numerics change | `Run functional tests`. | Golden drift can be expected but must be explained. |
| Container/dependency/lockfile change | `Run tests` by default; `Run functional tests` if runtime numerics may shift or goldens are refreshed. | `container::lts` only if explicitly requested. |
| MBridge integration touch | Add `Run MBridge tests` in addition to the relevant Megatron label. | MBridge job is off by default for PR pushes. |
