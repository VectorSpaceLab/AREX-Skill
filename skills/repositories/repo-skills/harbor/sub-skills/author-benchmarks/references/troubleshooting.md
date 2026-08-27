# Benchmark authoring troubleshooting

Use this table before escalating to execution or publishing workflows. Commands
shown are safe only when pointed at disposable local paths unless marked as
credentialed.

| Symptom | Likely cause | Recovery / boundary |
|---|---|---|
| `harbor task check` is unknown or says removed | Current CLI moved quality checks to the root command | Use `harbor check <task-dir>`; it may launch an evaluator, so keep it outside parser-only checks and gate its agent/model cost. |
| Generated task cannot be added or published because its name is missing | `[task]` section or `[task].name` was omitted, often by an adapter template | Set a stable `org/name` in adapter generation code; regenerate, then parse every generated task. Do not hand-edit a large generated set. |
| Name validation rejects dots or separators | Invalid `org/name`, leading dot, `..`, or unsanitized upstream ID | Lowercase/sanitize deterministically, preserve the org/name separator, and avoid leading/trailing separators and `..`. |
| Adapter validator reports `parity_experiments.json` | Wrong plural spelling | Rename/use singular `parity_experiment.json`; rerun the bundled validator. |
| Validator reports legacy flat layout | Adapter has root `adapter.py`/`run_adapter.py` instead of `src/<package>/adapter.py` and `main.py` | It is a migration warning. Prefer src layout; do not suppress the warning without documenting compatibility. |
| Validator reports missing `[task].authors` in template | Template cannot credit benchmark authors | Add the field in the template and render actual author metadata; do not rely on arbitrary metadata only. |
| `test.sh` exits successfully but reward is zero or missing | Script did not create `/logs/verifier/reward.txt`/`reward.json`, used a relative path, or wrote non-numeric JSON | Use absolute paths, create `/logs/verifier`, write numeric scalar/object output, and return the test status. Check JSON before execution. |
| Both reward files exist and the wrong one is read | Harbor gives `reward.json` precedence | Remove stale output or make JSON the intentional source of truth. Keep dimensions numeric. |
| RewardKit command not found | Package/executable names were confused or package is not installed in the verifier image | Use `uvx --from 'harbor-rewardkit==0.1.*' rewardkit /tests`, or install it in the image. `uvx harbor-rewardkit` is not the executable form. Offline images need a preinstalled package. |
| RewardKit judge fails before grading | Missing model/provider package, key, network, or separate verifier env | First run only a local criteria parse. Then classify import, credential, network, and rubric failures separately; never substitute an unverified judge score. |
| RewardKit score dimensions do not match `min_reward` | Root aggregation name or criteria directory differs from the gate | Decide the reward keys first. Use `reward` for scalar gates or a dict gate with exact keys; test missing-key behavior. |
| Multi-step task skips later steps | `min_reward` threshold was not met, verifier result/key was missing, or setup/healthcheck failed | Inspect the step contract and gate. A scalar gates `reward`; a mapping gates every named key. Keep execution analysis in `run-evaluate`. |
| `final` multi-step reward is surprising | Trial aborted early; the aborted step is now the final result | Use `mean` for progress aggregation or redesign thresholds; do not infer that a later step ran. |
| Separate verifier cannot find `/tests/test.sh` | Tests are not uploaded into a separate verifier at runtime | Put a Dockerfile and `test.sh`/`test.bat` in the effective verifier build context. Validate the image contract before running. |
| Separate verifier cannot see agent output | Output was not declared as an artifact | Add an artifact with the original absolute source path; remember `/logs/artifacts` and configured artifacts are the transfer boundary. |
| Artifact rejected for destination | Absolute path, backslash, `..`, reserved `manifest.json`, or collision | Use a relative forward-slash destination under the artifact root. Avoid equal/nested sources across main and sidecars. |
| Sidecar artifact rejected or empty | Source is not absolute, provider lacks Compose support, or state was not snapshotted | Use `{source = "/...", service = "name"}` and a POSIX-compatible `[[verifier.collect]]` hook. Put tamper-sensitive evidence on a final/separate verification step. |
| Network allowlist validation fails | URL/port/path used as a host, unsupported wildcard/IP/CIDR, or invalid phase override | Use exact hosts/IPs/CIDRs supported by the provider. Set the baseline under `[environment]`; only use phase overrides with `dynamic_network_policy`, or isolate verifier baselines. |
| No-network/allowlist works in config but not on host | Docker Linux kernel/sidecar capability, Windows container, macOS VM, or provider mode mismatch | Treat as optional backend evidence. Do not claim network enforcement from a TOML parse; use a compatible provider or leave capability unverified. |
| Compose task works locally but not in hosted provider | Many hosted environments support Dockerfiles but not Compose | Keep a Dockerfile-compatible path or document the provider restriction. Do not silently flatten sidecar semantics. |
| Task uses `environment.docker_image` and build fails | Image tag is unavailable or Dockerfile/image assumptions conflict | Parse the config first, then verify image availability only in an approved environment smoke test. Do not install a solution into a fallback image. |
| Agent/verifier network modes conflict | Phase override differs from start baseline but provider cannot switch dynamically | Match the baseline or use a separate verifier environment with its own baseline. A different `[verifier]` mode is not a start-time policy. |
| Metric script rejects rewards | Input has `null`/multi-key shapes that the recipe does not support, or paths were swapped | Use the required `-i`/`-o` flags, define null/multi-key policy explicitly, and write one JSON object of numeric metrics. |
| Dataset digest changes unexpectedly | Task/metric content changed, ignored-file rules differ, or remote refs upgraded | Run `harbor sync` locally, inspect file diffs and manifest entries, and pin remote refs. Do not publish until the change is intentional. |
| Dataset task count includes duplicates | Same `(name, digest)` or same task name with a new digest was added repeatedly | Inspect `task_count` versus unique references; remove stale references or intentionally retain versions with clear rationale. |
| Adapter parity scores do not overlap | Adaptation asymmetry, verifier/environment issue, agent wrapper difference, or variance | Resolve errors first, compare task-level outcomes, then trajectories/configuration. Use symmetric 5–10 → 1 → 3 run order; do not rerun blindly. |
| Parity uncertainty is too wide or reported as std | Too few runs or wrong statistic | Require 2+ runs, prefer 3+, retain raw arrays, and report sample SEM `sqrt(sum((x-mean)^2)/(n*(n-1)))`. |
| Publish refuses a task without environment | Task package preflight requires `environment/` | Supply a Dockerfile, Compose definition, pre-built image, or supported runtime files; parse with the task model before remote operations. |
| Publish returns permission/auth error | Not logged in, org unavailable, or package ownership missing | Stop. Ask for explicit auth/org approval; do not retry destructive/credentialed operations automatically. |
| A local command starts downloading huge dependencies | Wrong environment wrapper or an optional all/cloud dependency path | Use the verified project environment's direct executable for help/import probes. Avoid broad `uv run` resolution when it triggers unrelated extras; record the optional dependency as unverified. |
| A generated runtime file contains checkout/private paths | Source path copied verbatim into a skill or recipe | Replace with generic placeholders and self-contained instructions. Runtime skills must not point at original repository files or private environments. |

## Escalation rules

A parser/schema or tiny fixture failure is a blocking authoring issue. Missing
Docker, Compose, GPU, Windows, provider credentials, model keys, or network is
an explicit optional-backend omission, not proof that the task is invalid. A
remote mutation failure must remain gated and should be handed to the publishing
workflow with the exact command and error class. Completed-job score or
trajectory diagnosis belongs to `analyze-publish`, not this skill.
