# Install, Docker, CI, docs, and e2e coverage

Use this reference when a new RLinf model, environment, reward flow, worker/runner, or task type is user-facing. Internal prototypes may defer some items only when the handoff explicitly records the gap.

## Install script coverage

RLinf's install surface is organized by target and hardware platform.

### Targets and options

- Targets: `embodied`, `agentic`, and `docs`.
- Hardware platform option: `--platform nvidia|amd|ascend|musa`.
- Agentic rollout engine option: `--engine sglang|vllm`.
- Embodied selectors: `--model <model>` and `--env <env>`.
- Common safety options include `--venv`, `--python`, `--torch`, `--no-root`, `--no-flash-attn`, `--no-apex`, and `--install-rlinf`.

### Adding a new embodied model

1. Add the user-facing install selector to the supported model list. Note that install names may use hyphens while runtime `model_type` strings often use underscores; document the mapping clearly.
2. Add model-specific requirements in the appropriate requirements subdirectory when needed.
3. Implement an `install_<model>_model`-style function or extend the relevant model dispatcher.
4. For each supported env, install the minimum common embodied dependencies, env dependencies, then model dependencies. Do not install all optional env/model stacks by default.
5. If the model needs cloned third-party code, support a user-provided path env var first and shallow clone only when absent.
6. Add platform gates for CUDA/ROCm/Ascend/MUSA when wheels or kernels differ. Respect `--no-flash-attn` and `--no-apex` opt-outs where relevant.
7. Add a smoke import/build check in tests or CI when feasible.

### Adding a new environment

1. Add the env selector to the supported env list.
2. Implement an env install function or add a branch to `install_env_only` for env-only installs.
3. Extend relevant model install functions only for model/env combinations that are supported.
4. Avoid broad installs. A new env should not force all model dependencies unless the task actually uses them.
5. Export activation-time environment variables only when needed and make them idempotent.
6. For simulator assets or external repos, prefer documented user-provided paths, shallow clones, and explicit asset download steps.

### Adding an agentic/reasoning dependency

1. Decide whether it belongs in the agentic target or a narrower workflow script.
2. Keep SGLang and vLLM version constraints separate when they conflict.
3. Verify Megatron, flash-attn, apex, and engine-specific requirements with the chosen platform.

## Docker coverage

Docker builds are selected by `BUILD_TARGET`. Existing patterns use:

- `reason` for agentic/reasoning images.
- `embodied-<env>` or `embodied-<env>-<model>` for embodied images.
- A platform base selected by `PLATFORM` and target-specific `base-image-...` stages.

Checklist for a new Docker target:

1. Add a base-image stage only if the target needs a special OS/base image. Otherwise derive from the common platform base.
2. Add a final target stage named consistently with `BUILD_TARGET`.
3. If one image installs multiple venvs or model/env combos, chain the install commands in a single `RUN` where possible. This preserves uv hardlink/cache behavior.
4. Add asset download or symlink steps deliberately; do not make image build depend on private credentials.
5. Set a default venv activation line for the image's intended primary environment.
6. Keep final target naming aligned with the CI docker-build job and documentation.

## CI coverage

CI is routed by workflow filters and reusable workflows. A public extension usually needs updates in several places.

### Unit and static checks

- Add unit tests for registry dispatch, config validation, model/env factories, parser behavior, reward edge cases, and worker/runner wiring that can run without heavyweight assets.
- The lint workflow runs pre-commit/Ruff. Code should already be formatted and lint-clean before CI.
- Unit workflows cover Linux plus accelerator-specific runners for some platforms. If a test needs hardware, skip cleanly with a specific reason.

### E2E tests

Pick the smallest public e2e that proves the new capability:

- Embodied env/model/algorithm: add a config under the embodied e2e area and wire an embodied e2e job when the capability is publicly supported.
- Reasoning/agentic: add a reasoning/agent e2e config or job that covers the new reward, parser, runner, rollout backend, or task loop.
- SFT/reward model: add an SFT or reward-training e2e config when the change affects training flows.
- Offline RL: add an offline e2e config when the change affects offline data/value/config pipelines.

Keep e2e configs minimal: tiny batch sizes, minimal rollout steps, one backend when alternatives are not part of the claim, and explicit hardware/dataset requirements.

### CI filters and jobs

When new files or directories should trigger CI:

1. Update the central change filters so relevant docs, tests, source, install, Docker, or config changes trigger the right downstream workflow.
2. Add or update docker-build jobs for new Docker targets.
3. Add or update e2e jobs for new model/env/task coverage.
4. Ensure workflow job names and config names are consistent with install/Docker docs.
5. If a job cannot run on every PR due to limited hardware, document the trigger label or manual-run expectation.

## Documentation coverage

Public extensions need docs that a user can follow without reading implementation internals.

### Extension docs

Add or update extension documentation when introducing a reusable mechanism, API, registry, or pattern. Include:

- What problem the extension solves.
- Supported task types, backends, environments, models, and hardware.
- Config fields and defaults.
- Minimal run command or API usage.
- Known limitations and troubleshooting.

### Example docs

For new examples, keep English and Chinese docs aligned.

Recommended structure:

1. Short overview: model/env/task/algorithm/backends.
2. Environment or dataset description: observation/action schema and task text.
3. Installation: exact target/model/env selectors and hardware notes.
4. Quick start: minimal run command and important config overrides.
5. Evaluation or resume, if applicable.
6. Troubleshooting and expected outputs.

For embodied examples, add the page to the correct category index and update both English and Chinese indexes. If the feature belongs in README news or feature tables, update both language variants.

## Test planning by extension kind

| Kind | Minimum useful tests | When to add e2e |
| --- | --- | --- |
| Advantage | Shape/mask/unit math, registry dispatch, config validation | New public algorithm or changed actor runner path |
| Policy loss | Numeric loss/metrics, mask edge cases, registry dispatch | New public loss used by actor workers |
| Rule-based reward | Batch order, malformed outputs, timeouts, registry dispatch | New agentic/reasoning workflow or expensive reward integration |
| VLM reward parser/input builder | Invalid model output, missing images/history, local/API parity | User-facing reward model pipeline |
| Embodied model | `register_model`/`get_model`, BasePolicy output contract, FSDP wrap policy | New model advertised in examples/install/docs |
| Environment | factory resolution, action conversion, reset/step smoke with dummy/minimal assets | New env advertised to users |
| Worker | launch shape, remote method result, logging/communication if CPU-feasible | New public distributed component |
| Runner/task | config validation, entrypoint wiring, checkpoint/eval cadence logic | New public task loop |

## Documentation and CI handoff checklist

Before considering a public extension complete, record:

- Install selector(s) and exact target/platform coverage.
- Docker target name or reason no Docker target is required.
- Unit tests added and any skipped hardware cases.
- E2E config/job added or the smallest feasible substitute.
- English and Chinese docs or explicit reason one side is not applicable.
- README/news update status for user-visible features.
- Known unsupported backends/platforms and validation messages that catch them.
