# Cross-Cutting Troubleshooting

## Import or Install Fails

Symptoms:
- `ModuleNotFoundError: No module named 'trl'`
- `PackageNotFoundError: trl`
- `pip check` reports incompatible dependencies

Actions:
1. Confirm Python is `>=3.10`.
2. Install the base package with `pip install trl` or source checkout with `pip install -e .`.
3. Run `python -c "import trl; print(trl.__file__)"` and `trl --help`.
4. If a backend-specific import fails, install only the extra for that workflow instead of broad `dev` extras.

## CLI Command Fails

Symptoms:
- Unknown argument errors.
- Boolean flags behave unexpectedly.
- YAML config keys are ignored.
- `dataset_name` conflicts with dataset mixtures.

Actions:
1. Use [cli-and-configs](../sub-skills/cli-and-configs/SKILL.md) for command/config construction.
2. Run `trl <command> --help` for the exact command, because each command exposes a different trainer config.
3. Keep Accelerate launcher flags, TRL subcommand, and script/trainer flags in the expected order.
4. Prefer a YAML config when the command has many trainer/model/dataset fields.

## Dataset or Reward Setup Fails

Symptoms:
- Missing `prompt`, `chosen`, `rejected`, `messages`, `completion`, or `solution` columns.
- Chat template output is empty or masks the wrong text.
- Reward functions return `None` or mismatched list lengths.

Actions:
1. Use [data-and-rewards](../sub-skills/data-and-rewards/SKILL.md) to classify the dataset shape.
2. Run `sub-skills/data-and-rewards/scripts/validate_trl_dataset.py --help` and validate a small JSONL fixture.
3. For GRPO/RLOO, make reward functions accept all required dataset columns as keyword arguments and return one value per completion.

## Backend or Hardware Fails

Symptoms:
- `ImportError: vLLM is required`.
- CUDA unavailable or out of memory.
- DeepSpeed/FSDP config errors.
- vLLM server URL timeout.

Actions:
1. Use [scaling-and-backends](../sub-skills/scaling-and-backends/SKILL.md) before changing trainer code.
2. Run `sub-skills/scaling-and-backends/scripts/check_optional_backends.py --help` for safe diagnostics.
3. Install the minimal extra needed for the selected backend.
4. Do not start services, distributed jobs, or training runs until devices, ports, and optional packages are confirmed.

## Experimental or Environment Training Fails

Symptoms:
- `TRLExperimentalWarning`.
- Missing OpenReward, Harbor, Docker, sandbox, vLLM, or credentials.
- `environment_factory` tools are not discovered.
- Environment servers reject concurrent sessions.

Actions:
1. Use [experimental-and-environments](../sub-skills/experimental-and-environments/SKILL.md).
2. Treat experimental APIs as unstable and verify exact signatures in the installed package.
3. Validate environment classes with the bundled checker before launching training.
4. Record credential, network, Docker, and service requirements explicitly instead of hiding them in a training script.

## Repository Development Fails

Symptoms:
- A trainer fix is applied to one duplicate block but not siblings.
- A paper-backed method lacks `docs/source/paper_index.md` coverage.
- Docstrings fail style review.
- Tests are too broad or skip the changed area.

Actions:
1. Use [repo-development](../sub-skills/repo-development/SKILL.md).
2. Follow the repository policy that trainer duplication is intentional and consistency is mandatory.
3. Update the paper index for paper implementations using Hugging Face paper URLs.
4. Run the narrow tests for the changed surface before broader suites.
