# Troubleshooting execution

Diagnose from the resolved config, preflight output, persisted result, and
artifact manifest before changing an experiment. Never hide a setup or
provider error with `--disable-verification`, a public-network fallback, or a
larger timeout unless the user explicitly approves the changed semantics.

## Command and config failures

| Symptom | Likely cause | Safe recovery |
| --- | --- | --- |
| `harbor: command not found` | Harbor is not on `PATH`, or the wrong environment is active. | Ask how Harbor was installed; activate that environment or use its documented runner (for example a project-managed `uv run` invocation). Do not guess a local source location. |
| `harbor run --help` lacks an option documented elsewhere | Installed CLI and reference docs are different versions. | Prefer live help and installed Pydantic models. Remove/replace unsupported flags and record the version. |
| `--path`, `--task`, and `--dataset` conflict | More than one primary input mode was supplied. | Choose exactly one. Use a config file only when its `tasks`/`datasets` sources are intentional. |
| `--print-config` rejects `JobConfig` | Invalid field type, task source, concurrency relationship, deprecated schema, or conflicting mode. | Read the validation message; correct the YAML/JSON, then rerun `--print-config`. Do not start a partial plan. |
| A dataset resolves to no tasks | Include/exclude glob, `n_tasks`, registry ref, or cache is wrong. | Print/inspect the selected dataset metadata, loosen one filter, or pin a valid ref. Route dataset authoring/registry problems to `author-benchmarks`. |
| Config flags appear ignored | A loaded config was mutated by later flags, or a list-valued flag replaced rather than merged. | Compare the printed resolved config with the file. Put the desired complete list in the config or pass the complete CLI override. |
| A trial says `--path` or `--config` is required | `trial start` was invoked without a task path or complete config. | Provide one local task path or a YAML/JSON `TrialConfig` with `task`. |
| A task path is a dataset directory but behaves as one task | The path shape or task manifest is not recognized. | Confirm each child is a valid Harbor task and use dataset input intentionally; task creation/validation belongs to `author-benchmarks`. |

## Agent and model failures

| Symptom | Likely cause | Safe recovery |
| --- | --- | --- |
| Unknown agent name | The name is not in the installed `AgentName`/factory registry. | Use live help for installed names, install the optional agent extra, or pass a valid custom import path. For implementation/registration, route to `integrations`. |
| Custom agent import fails | Import path, package environment, constructor, or required dependency is wrong. | Test the import in the same runtime, check `module.path:ClassName`, and run `--install-only` if setup is the target. Do not claim the class is supported from its spelling alone. |
| Agent/model starts but rejects kwargs/model | Agent-specific constructor or endpoint contract differs. | Remove the suspect kwarg, inspect the agent's installed contract, and verify model/provider naming and credential. Keep one change per smoke run. |
| Missing API key/secret or authentication error | Model credential is absent, wrong, expired, or not passed to the agent phase. | Export/pass the variable through `--agent-env` or the approved hosted secret mechanism; redact it from YAML/logs. Do not retry authentication errors by default. |
| Agent timeout or safety refusal repeats | The configured timeout is too small, model behavior is incompatible, or the task is not suitable. | Inspect agent logs and task instruction. Increase a timeout only as an approved experiment; do not use retries to mask a deterministic refusal. |
| `--load-trajectory` rejected before start | File missing/invalid or selected agent lacks native/ATIF load support. | Check extension and ATIF validity, preserve native filename, choose a supported agent, or omit loading intentionally. The old environment files are not restored by loading. |
| `--resume-trajectory` rejected on multi-step task | Selected agent lacks `SUPPORTS_RESUME`, or the flag is being used with an unsupported bridge. | Use fresh per-step sessions or select an agent with native resume support; do not describe fresh sessions as context continuation. |

## Environment, resources, and network

| Symptom | Likely cause | Safe recovery |
| --- | --- | --- |
| Provider extra/import error | Optional SDK is not installed. | Install the selected Harbor provider extra in the same runtime or choose an approved provider. Do not silently fall back if provider choice affects the experiment. |
| Provider preflight lacks credentials/quota | API key, account, region, Docker daemon, or hosted quota is unavailable. | Stop before job creation; provision the approved credential/daemon, use `--launch --dry-run` for hosted validation, or ask to change providers. |
| Environment build/start failure | Dockerfile, private image, OS mode, compose layout, or provider capability is invalid. | Inspect task/environment logs and validate the task with `author-benchmarks`; check Windows container mode and compose support. Do not treat an agent failure as the diagnosis. |
| CPU/memory policy rejected | Provider does not advertise the requested policy, or a non-auto policy has no task/run value. | Use `--print-config`, inspect task resources, and choose a supported policy/value. Preserve the requested semantics rather than using `auto` silently. |
| GPU/TPU/storage request rejected | Provider/backend lacks the accelerator or task combines unsupported resources. | Check provider capabilities and task OS/compose restrictions; select a compatible environment or revise the task with approval. |
| Network mode rejected at trial start | Provider cannot enforce `no-network`, allowlist entry type, dynamic phase switch, or compose combination. | Pick a provider that supports the exact policy, use a separate verifier baseline when appropriate, or revise the task policy explicitly. Never fall back to public access silently. |
| Agent cannot reach API but setup can | The `[agent]` phase allowlist omitted the endpoint, or `--allow-agent-host` was not passed. | Add exact supported hosts to the task/approved run override; use `--allow-environment-host` only for setup/start requirements. Check DNS/ports are not incorrectly written as allowlist entries. |
| Verifier cannot reach a required service | Shared/separate verifier mode or verifier-phase network differs from the intended policy. | Inspect task verifier mode and phase policy. Declare a separate verifier baseline or explicit verifier allowlist as the task requires; route task edits to `author-benchmarks`. |

## Artifacts, verifier, and multi-step failures

| Symptom | Likely cause | Safe recovery |
| --- | --- | --- |
| Expected output is absent from the trial | The agent/test did not write to `/logs/artifacts/`, the path was not declared, or remote download failed. | Inspect `artifacts/manifest.json`, agent/verifier logs, and source path. Add a task/trial artifact entry or fix the producer; collection is best-effort and a missing entry is not a score. |
| Artifact manifest has `failed` or `skipped` | Source could not be read, provider/service is unsupported, or flat host paths collided. | Correct the source/service, avoid equal/nested paths, and rerun. Do not use the bytes for a regrade. |
| Sidecar artifact/collect hook fails | Provider is not compose-capable, service name/path is wrong, or collect command uses unavailable shell syntax. | Verify provider and service, use POSIX `sh` for arbitrary sidecars, and place tamper-sensitive evidence on the final separate-verifier step. Route task changes to `author-benchmarks`. |
| Separate verifier cannot see a generated file | The file was not declared as an artifact, or the verifier expects the host destination instead of the original source path. | Declare the absolute in-container source; Harbor rematerializes it at that source path. A host `destination` only controls local placement. |
| Reward file missing/empty or verifier parse fails | The verifier failed, wrote the wrong reward contract, or its logs are incomplete. | Inspect verifier stdout/stderr and task verifier contract; repair the task/verifier through `author-benchmarks`. Do not use `--disable-verification` to manufacture a score. |
| Multi-step later step did not run | Setup/healthcheck/agent/verifier failure or `min_reward` gate aborted the sequence. | Inspect per-step results and `exception_info`; fix the first failing step or intended threshold. The trial-level reward includes only steps that ran. |
| Multi-step artifact is in the wrong directory | Step collection is per-step and may use mounted/non-mounted layout. | Inspect `steps/<name>/artifacts/` and its manifest; distinguish task/trial artifacts from step artifacts. |

## Resume, handoff, and regrade failures

| Symptom | Likely cause | Safe recovery |
| --- | --- | --- |
| `job resume` reports changed config/lock | The job input or resolved task/agent/environment identity changed, or the path now points at different content. | Restore the original config/locked task or start a new job with a new name. Do not overwrite the source result. |
| Resume removes more trials than expected | Default filter removes `CancelledError`, or additional `--filter-error-type` values were supplied. | Re-run only after reviewing the command; pass the exact desired repeated filter set and preserve the original directory if uncertain. |
| No generic trial resume exists | Trial recovery was mistaken for job recovery. | Use `--load-trajectory` for a new trial, `trial handoff` for a supported local CLI, or start a fresh trial. |
| `trial handoff` rejects a directory | Target is a job rather than child trial, lacks `config.json`, agent lacks handoff support, or the trial has multiple sessions. | Pass the child trial directory, verify agent support and session count, and remember that files are not restored to the local working tree. |
| Regrade refuses a source | Source is incomplete/multi-step, manifest/result is unreadable, verifier is shared, or declared artifact bytes are absent/failed/skipped. | Stop and repair/choose a valid source or verifier task. Regrade never reruns the agent and does not modify the source. |
| Regrade changes the original result | This should not happen for the supported command. | Stop, preserve all directories, and treat it as a runtime bug; do not continue publishing or comparing the output. |

## Final diagnostic discipline

Before relaunching, capture:

1. Harbor version and live help relevant to the command.
2. Resolved config from `--print-config` (without secrets).
3. Provider/agent preflight result and the exact missing capability.
4. Job/trial `result.json`, exception type/message, and relevant logs.
5. Artifact `manifest.json` and the intended source/destination mapping.
6. Whether the next action is a new evaluation, job resume, trajectory load,
   handoff, or regrade.

Then route task definition changes to `author-benchmarks`, result/trajectory
interpretation to `analyze-publish`, and provider/agent implementation to
`integrations`.
