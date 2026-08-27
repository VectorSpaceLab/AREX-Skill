# Ray Repo Provenance

This repo skill was generated from repository evidence for Ray and is intended to help future agents decide when the skill may be stale.

## Source Snapshot

| Field | Value |
| --- | --- |
| Repository | Ray |
| VCS | git |
| Branch | `master` |
| Commit | `8167734e17610eab6e2e782a3a77a0e848542a64` |
| Exact tag | none detected |
| Working tree state | dirty: generated `skills/` content present |
| Source package version | `3.0.0.dev0` from `python/ray/_version.py` |
| Installed inspection package | `ray` 2.55.1 used only for live API/CLI signature checks |
| Remote URL | https://github.com/ray-project/ray |

The generated skill uses current source files and documentation for Ray 3.0.0.dev0 intent, packaging, submodule coverage, and provenance. A private installed Ray 2.55.1 environment was used only to verify stable public imports, selected signatures, optional-extra behavior, and CLI help surfaces. Local environment paths and Python executable paths are intentionally omitted.

## Evidence Paths

| Evidence path | Purpose |
| --- | --- |
| `README.rst` | Ray overview, library list, install surface, user-facing positioning |
| `pyproject.toml`, `python/setup.py`, `python/ray/_version.py` | Python support, distribution name, extras, console scripts, version |
| `python/ray/__init__.py`, `python/ray/_private/worker.py`, `python/ray/scripts/`, `python/ray/runtime_env/`, `python/ray/job_submission/`, `python/ray/util/state/` | Core APIs, CLI entry points, jobs, runtime environment, state/observability surfaces |
| `doc/source/ray-core/`, `doc/source/cluster/`, `doc/source/ray-observability/` | Core workflows, cluster operations, jobs, state APIs, dashboard, debugging |
| `python/ray/data/`, `doc/source/data/`, `python/ray/data/tests/` | Ray Data APIs, IO, transforms, performance, test-backed behavior |
| `python/ray/train/`, `python/ray/tune/`, `doc/source/train/`, `doc/source/tune/` | Train/Tune configs, checkpoints, storage, tuning, resources, results |
| `python/ray/serve/`, `doc/source/serve/`, `python/ray/serve/tests/` | Serve APIs, CLI, YAML config, deployment lifecycle, troubleshooting |
| `rllib/`, `doc/source/rllib/`, `rllib/examples/` | RLlib AlgorithmConfig/PPOConfig workflows, Gymnasium envs, Tune integration |

## Explicitly Out Of Default Scope

- Java and C++ Ray APIs.
- `ray[llm]` and heavy LLM Serve tutorials.
- Release, CI, Docker, and Bazel build-maintainer workflows.
- Provider-specific cloud autoscaler internals, Kubernetes credential provisioning, and production network/security setup.
- Long-running benchmarks, chaos tests, GPU tests, service-dependent examples, and large downloads.

Refresh this skill when the Ray checkout commit, source package version, public API signatures, CLI command surface, extras definitions, or the evidence paths above change materially.
