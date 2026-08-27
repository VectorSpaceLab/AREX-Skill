# Harbor cross-cutting troubleshooting

Use this reference before retrying a failed command. Classify the failure first;
do not solve an environment, verifier, credential, or task-definition problem
by blindly increasing timeouts or disabling verification.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `harbor: command not found` | Harbor is not installed in the active Python/tool environment | Install the published package with `python -m pip install harbor` or use the environment's documented tool installation, then run `harbor --version`. |
| Import fails or version is unexpected | Wrong Python on `PATH`, stale installation, incompatible Python, or package shadowing | Run `python -c 'import sys; print(sys.executable)'`, `python -m pip show harbor`, and `harbor --version`; use Python `>=3.12` for the inspected release and reinstall in an isolated environment if needed. |
| A command/flag is unknown | CLI version differs from the reference | Read the live command's `--help`; do not copy flags from another release. Check the repository provenance or refresh the skill when the public surface changed. |
| Pydantic/TOML validation rejects a config | Wrong nesting, deprecated field, invalid enum, missing package name, or config for a different layer | Validate through `--print-config` or the installed model. Keep task-side `task.toml`, job config, trial config, and `ExecConfig` distinct; inspect the first validation error. |
| Task or dataset cannot be resolved | Path is not a task/dataset, registry ref lacks access/version, git source is incomplete, or manifest digest is stale | Confirm the exact local path and required files; use a package name with an explicit ref when reproducibility matters; route malformed manifests to `author-benchmarks`. |
| Docker build/start fails | Docker daemon, image, Dockerfile, compose service, resource, OS, or network policy is unsupported | Run a tiny task or `--install-only` preflight; check daemon/provider capability and task environment files. Do not claim a cloud/GPU/Windows fix from a CPU import. |
| Cloud provider import/preflight fails | The provider extra, SDK version, account key, quota, region, or provider capability is absent | Install only the selected provider extra, set credentials through the supported environment mechanism, run its read-only preflight, or fall back to local Docker if the experiment permits. |
| Model authentication or endpoint error | Model key, provider prefix, endpoint, region, or agent-specific environment variable is missing | Keep secrets out of configs/logs; pass them through the agent environment or provider's credential mechanism and verify the model endpoint with a minimal approved call. |
| Agent import path fails | `module.path:ClassName` is not importable in the Harbor process, constructor signature is incompatible, or optional import is eager | Test the import in the same Python as Harbor, inspect `AgentFactory`, preserve factory kwargs, and route implementation changes to `integrations`. |
| Agent cannot run Windows or resume/load | Capability flags are false or the selected agent lacks the required native format | Choose an agent advertising the capability, remove the unsupported task mode, or use a fresh session/portable ATIF path when supported. |
| Verifier returns no reward | Test entrypoint did not write `/logs/verifier/reward.txt` or `reward.json`, path/user is wrong, or verifier crashed | Inspect verifier stdout/stderr and artifact paths. Ensure one numeric reward or a numeric JSON object and correct OS-specific entrypoint; route task fixes to `author-benchmarks`. |
| Reward keys or multi-step gate fail | `min_reward` names a missing key, step aggregation strategy is wrong, or a separate verifier lacks transferred artifacts | Compare verifier output with the declared gate and strategy; use `mean`/`final` deliberately and declare absolute artifact sources. |
| Artifact collection fails | Source is absent, destination escapes/overlaps, service is unsupported, or collect hook ran too late | Use `--print-config`, keep destinations relative and non-reserved, use absolute sidecar paths on compose providers, and test collection with a tiny fixture. |
| Job resumes unexpectedly or refuses to resume | Job is completed, config/lock changed, cancellation/error filter differs, or output directory is wrong | Point `job resume` at the original job directory, inspect `config.json`/`lock.json`, and preserve the original execution contract. Start a new job only when a changed experiment is intentional. |
| A score differs after regrade | The new verifier sees different files, regrade is unsupported for multi-step, or the original artifact manifest is incomplete | Confirm regrade prerequisites and separate verifier mode; inspect raw artifacts and trajectory before interpreting the score. |
| `harbor exec` reducer cannot start | Map artifacts are missing/empty, reducer instruction is absent, or map/reduce flags were mixed with a config | Run `harbor exec --print-config`, specify map artifacts explicitly, provide reducer instruction, and choose flags or complete config mode. |
| Publish/upload/share/auth is denied | Credential, organization permission, visibility, tag, registry version, or remote service issue | Treat remote mutations as a separate approved workflow; run status/read-only checks first and never paste keys into command output. |

## Escalation order

1. Capture the exact command, Harbor version, selected input, and first error.
2. Run the command's live `--help` and, where available, `--print-config`.
3. Classify local config/task, package/import, provider/backend, credential,
   verifier/artifact, or model failure.
4. Use the owning sub-skill's troubleshooting reference and a tiny fixture.
5. Only then retry. Preserve failed job artifacts for analysis; do not delete
   partial evidence unless the user explicitly requests cleanup.
