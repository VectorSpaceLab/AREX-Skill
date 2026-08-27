# Test Selection

Use the smallest test set that covers the changed behavior, then broaden only when the edit affects shared interfaces, duplicated trainer logic, or public commands.

## Fast Local Checks

- **Single trainer edit**: run the matching top-level trainer test, such as `pytest tests/test_grpo_trainer.py` or `pytest tests/test_rloo_trainer.py`.
- **Experimental trainer edit**: run the matching `tests/experimental/test_*_trainer.py` file.
- **Shared utility edit**: run the direct utility test file first, then trainer tests that exercise the changed utility.
- **CLI edit**: run `pytest tests/test_cli.py` or `pytest tests/test_cli_utils.py`; for skills CLI changes, run `pytest tests/test_skills.py tests/test_skills_cli.py`.
- **Docs-only edit**: run formatting or doc-build checks only if the repository task requires them; otherwise inspect links, snippets, and autodoc targets carefully.

## Trainer and Config Changes

Pick tests by touched behavior:

- **Config validation/defaults**: matching trainer/config test file plus CLI tests if command-line arguments changed.
- **Dataset preprocessing**: matching trainer test plus data utility tests when dataset conversion or chat-template behavior changed.
- **Reward computation**: trainer test and `tests/test_rewards.py` if shared reward helpers changed.
- **Generation path**: trainer tests for every trainer with the duplicated generation branch, not just the file edited first.
- **vLLM client/server behavior**: include `tests/test_vllm_client_server.py` when transport, server mode, colocate mode, or version checks change.
- **Distributed or accelerate behavior**: include `tests/distributed/` only when process topology, model wrapping, synchronization, or launch behavior changed.

## Duplicated Trainer Logic

When a repeated block changes, test at least one representative for each semantic family. For example, a vLLM generation edit affecting online trainers should cover GRPO and RLOO, and may need relevant experimental online trainers if their copied branch changed too.

Before running broader tests, compare the modified copies manually:

- Variable names and comments match where behavior matches.
- Branch order is the same.
- Metrics are logged under consistent keys.
- Intentional semantic differences are local and explainable from trainer purpose.

## Paper Trainer Additions

For a new paper-backed trainer or loss variant, combine tests that prove both integration and paper-specific behavior:

- Config defaults and argument validation.
- Minimal loss/reward computation on tiny synthetic tensors or examples.
- Dataset format acceptance and rejection paths.
- Trainer initialization and one short training/evaluation path when practical.
- Public imports and CLI/docs exposure if added.
- `docs/source/paper_index.md` coverage with a Hugging Face paper URL.

Do not rely only on a long end-to-end training run; add small deterministic tests for core behavior.

## Invariant Tests

`tests/invariant/` catches silent trajectory changes for selected CLI training configurations. It is opt-in, hardware-sensitive, and not part of ordinary narrow validation.

Use invariant tests when a change can alter numerical training trajectories without obvious unit-test failures, such as:

- Gradient accumulation behavior.
- Loss scaling or masking.
- Attention/kernel choices.
- CLI defaults that affect actual training.
- Trainer loop changes in SFT or DPO equivalence classes.

Run invariant tests only when the required hardware and reference context are available. Snapshot updates must be justified in the PR description; never refresh snapshots just to make a failure disappear.

## Quality and Formatting

TRL uses Ruff settings from `pyproject.toml` with Python 3.10+ target, 119-character line length, first-party imports under `trl`, and selected lint rules. Prefer repository-provided precommit targets for final PR hygiene when the environment is prepared.

Use `make precommit` for a full modified-file hygiene pass when appropriate. For quick iteration, run narrower `pytest` commands first so functional failures are easier to diagnose.

## When To Broaden

Broaden from a targeted test to additional suites when:

- A public import, CLI argument, or configuration default changed.
- A duplicated trainer block was edited in multiple trainers.
- A shared utility under `trl/` changed.
- The edit touches distributed, vLLM, or hardware-dependent paths.
- A test failure suggests a policy-level behavior changed rather than a local typo.

Avoid starting with the full suite unless the task is release-level validation or the change is broad across package boundaries.
