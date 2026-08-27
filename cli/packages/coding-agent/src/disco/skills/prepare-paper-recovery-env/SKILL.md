---
name: prepare-paper-recovery-env
description: "Inspect, prepare, and document an isolated runtime environment for Paper2Skills recovery experiments, including package probes, model/cache checks, GPU status, bounded benchmark acquisition, and a runtime handoff for recover-paper-result."
metadata:
  disco-role: meta
---

# Prepare Paper Recovery Env

Use this skill after `create-paper-module-skill` validation and before `recover-paper-result` whenever recovery needs models, packages, datasets, GPUs, API keys, benchmark code, or any nontrivial runtime setup. It adapts the environment-inspection discipline from repo-skill creation to Paper2Skills recovery, where the goal is an auditable recovery runtime rather than a public repo skill.

All artifacts must be in English.

## Purpose

Create a current-attempt runtime handoff that tells `recover-paper-result` exactly what is usable, what was prepared, what failed, and what fallback is allowed. This is an active environment-preparation stage, not a passive inventory. Missing packages, datasets, model caches, or benchmark files are setup tasks to attempt within the user's constraints before they become blockers. Do not spend recovery time guessing package state, performing broad filesystem scans, or mutating shared environments without permission.

## Inputs

- `attempt_dir` containing `run_manifest.json`.
- `module_plan.json` and generated skills root.
- Runtime constraints from the user or run prompt:
  - preferred model id/path and fallback model id/path
  - GPU ids or CPU-only permission
  - network permissions and setup commands
  - package mutation rules
  - isolated environment prefix, if the user wants one
  - benchmark/dataset URLs or local paths
  - whether reduced training is allowed

## Outputs

Write these files under the attempt directory:

```text
environment/
  runtime_handoff.json
  logs/
    package_probe.json
    gpu_probe.json
    model_cache_probe.json
    benchmark_probe.json
    command_log.json
```

Also update `run_manifest.json.stages.prepare_environment` to `complete` or `blocked`.
Recovery validation treats a missing or still-pending prepare stage as a
contract failure.

## Workflow

1. Read `run_manifest.json` and runtime constraints. If constraints are missing, infer only low-risk defaults and record them.
2. Run bounded probes before any installation or download:
   - Python executable and version.
   - Import availability for packages required by the recovery target.
   - GPU visibility with `nvidia-smi` if available.
   - Model cache roots from user-supplied paths, `$HF_HOME`, `$TRANSFORMERS_CACHE`, `~/.cache/huggingface`, and the workspace only.
   - Benchmark or dataset source availability.
3. Do not scan broad roots such as `/share/project` recursively. Search only explicit allowlists, known cache roots, and the workspace with timeouts.
4. If packages are missing:
   - Prefer an existing compatible environment supplied by the user.
   - If mutation is allowed, create or use an isolated environment. Prefer
     conda when available and fall back to venv, mirroring
     `prepare-repo-skill-env`.
   - Use the
     same default location policy as `prepare-repo-skill-env`: when the user
     does not provide a prefix, put recovery environments under
     `$DISCO_CODING_AGENT_DIR/envs/`; if that variable is unset, use
     `~/.disco/agent/envs/`. Name the environment
     `paper-recovery-<run_name>`. Do not install into conda `base`, a shared
     conda env, or the active environment unless the user explicitly authorized
     that exact mutation. If runtime constraints say isolated env only, use this
     private environment even when the active Python already has the requested
     imports.
   - Install the smallest missing package set needed by the selected recovery
     target. For import/package name mismatches, pass explicit specs such as
     `--pip-package sklearn=scikit-learn`.
   - Put timeouts around installs. Record command, elapsed time, stdout/stderr tail, exit code, and whether environment was modified.
   - If installs stall or fail, try the user-provided network/VPN setup, a safe
     pip index/mirror, or a narrower package set when appropriate. Only then
     record a blocker, with the failed command and the next concrete fix.
5. If benchmark/data acquisition is needed:
   - Try the requested fresh source with a timeout.
   - Treat a timed-out or partial checkout as unusable until it validates as a real worktree and the requested resource files exist. A directory containing only `.git` is not a usable benchmark source.
   - If fresh acquisition fails, reuse a local immutable checkout only when allowed or when the run prompt permits it. Record the fresh-fetch blocker, reused path, commit/version, exact files used, and copy/snapshot concrete resource files into the current attempt.
   - Prefer resource files that can ground an actual example: task JSON/PDDL/TWL2/problem files, environment config, split manifests, prompts, expert plans, or benchmark metadata. For ALFWorld-style reduced recovery, prefer concrete task/game/config resources when available; if only README/API files are available, record why and require the generated data item to identify which fields came from those files.
   - If the paper needs a public dataset such as AIME2024 and no local path is
     supplied, attempt bounded acquisition from the user-supplied URL or a
     direct public source when source acquisition permits network access. A
     missing local dataset is not a blocker until bounded download or an
     explicit user question has been attempted and logged.
6. If model loading is requested:
   - First verify required packages and local/cache files.
   - If no local/cache hit exists, ask for or use explicit permission before
     downloading multi-GB models. Use a time budget and download into the
     attempt-scoped or DisCo-private cache, not a shared mutable cache unless
     the user requested it.
   - If loading is blocked, keep required-model success booleans false and
     write the exact blocker plus what was tried. A missing QwQ/Qwen cache is
     not a blocker until local cache probing and permitted bounded download or
     user clarification have happened.
7. If web search or API credentials are needed:
   - Check configured env vars or user-provided credential paths first.
   - Try an allowed keyless/public alternative when the method permits it.
   - If credentials are truly required and absent, ask the user for them or
     record the credential request as a pending user input. Do not present
     missing credentials as if the agent had exhausted setup work.
8. Write `environment/runtime_handoff.json` with a concise decision:
   - `runtime_ready`: true only when the requested runtime is genuinely ready.
   - `reduced_recovery_recommended`: true only when full runtime is blocked and the user permits reduced recovery.
   - `blockers`: exact actionable blockers.
   - `allowed_sources_for_recovery`: paths/URLs recover-paper-result may use.
   - `environment_modified`: whether any environment was changed.
9. Write `environment/logs/command_log.json` with every subprocess command executed by the environment probe, including GPU probes, benchmark clone attempts, version/commit checks, environment creation, installs, downloads, or killed commands. Commands that are only in terminal output are not auditable. If the probe is rerun, append to the existing command log instead of overwriting it.
10. Pass the handoff path to `recover-paper-result`. Recovery must include it in `recovery/source_manifest.json`.

## Runtime Handoff Schema

```json
{
  "schema_version": 1,
  "attempt_dir": "...",
  "python": {"executable": "...", "version": "..."},
  "packages": {"torch": false, "transformers": false},
  "environment": {
    "manager": "venv",
    "prefix": "~/.disco/agent/envs/paper-recovery-search_o1",
    "python": ".../bin/python",
    "setup": {"actions": [], "blockers": []}
  },
  "gpu": {"nvidia_smi_available": true, "visible_devices": []},
  "models": {
    "preferred": "Qwen/Qwen3-4B-Instruct-2507",
    "preferred_ready": false,
    "cache_hits": [],
    "blockers": []
  },
  "benchmarks": {
    "alfworld": {
      "fresh_attempted": true,
      "fresh_ok": false,
      "reused_local_source": "",
      "snapshot_dir": "",
      "resource_files": []
    }
  },
  "datasets": {},
  "runtime_ready": false,
  "reduced_recovery_recommended": true,
  "environment_modified": false,
  "allowed_sources_for_recovery": [],
  "blockers": []
}
```

## Acceptance Criteria

- `environment/runtime_handoff.json` exists and is valid JSON.
- `environment/logs/command_log.json` exists, is valid JSON, and contains a `commands` list.
- `run_manifest.json.stages.prepare_environment` is `complete` when the
  requested runtime is ready, or `blocked` when exact blockers are recorded.
- If packages were missing and environment mutation was allowed, the command log
  shows an isolated environment creation/reuse and install attempts before the
  stage is marked blocked.
- If runtime constraints require isolated environments, the handoff's
  `python.executable` points to the private recovery environment Python, not the
  host/shared conda Python, unless private environment creation failed and the
  failure is logged as a blocker.
- Probes are bounded and logged.
- Shared environments are not mutated unless explicitly permitted.
- Any reused benchmark source has a current-attempt snapshot of concrete resource files.
- Partial clone directories are rejected unless they validate as complete worktrees containing the requested resource files.
- Repeated environment probes preserve earlier command-log entries.
- Full runtime booleans remain false unless the requested model/package stack is actually importable and ready.
- The handoff gives `recover-paper-result` enough information to choose between full recovery and an honest reduced fallback without repeating expensive discovery.

## Script

Use `scripts/probe_runtime.py` for deterministic probes, bounded repair, and handoff generation. It can create/reuse an isolated conda env or venv at the DisCo-private default prefix, install explicitly requested missing packages, try bounded dataset/model downloads when flags permit them, inspect GPU/model cache hints, and validate benchmark source state. It must not perform unbounded downloads or broad scans.

Example for a Paper2Skills recovery that may need torch/transformers/vLLM/nltk,
a QwQ/Qwen model, and a public benchmark:

```bash
python <skills_root>/prepare-paper-recovery-env/scripts/probe_runtime.py \
  --attempt-dir <attempt_dir> \
  --preferred-model Qwen/QwQ-32B \
  --package torch --package transformers --package vllm --package nltk \
  --env-manager auto \
  --pip-package torch \
  --pip-package transformers \
  --pip-package vllm \
  --pip-package nltk \
  --allow-env-mutation \
  --use-isolated-env \
  --attempt-model-download \
  --dataset-name AIME2024 \
  --dataset-url <direct-public-or-user-supplied-url> \
  --attempt-dataset-download \
  --network-timeout 300 \
  --install-timeout 900
```
