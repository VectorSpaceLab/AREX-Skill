# TorchRL Cross-cutting Troubleshooting

## Install/import/version failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: torchrl` | Package not installed in the active Python | Run the import/version check from `SKILL.md`; install `torchrl` into the same interpreter used by the task. |
| `PackageNotFoundError: torchrl` but `import torchrl` works | Import came from a checkout or `PYTHONPATH`, not an installed distribution | Use `python -I` from outside the checkout, or install editable/non-editable package intentionally. |
| `ImportError` from `tensordict` or `torch` | Version mismatch across TorchRL, TensorDict, PyTorch | Match release families; reinstall the trio together rather than upgrading one package blindly. |
| C++ extension import/build error | Stale build artifacts, compiler/toolchain mismatch, PyTorch ABI change | Clean/rebuild in a fresh environment; for source installs, ensure PyTorch is installed first. |
| CUDA extension expected but unavailable | CPU PyTorch wheel, missing `nvcc`, or CUDA tag/toolkit mismatch | Read `backend-compatibility.md`; verify CUDA separately before claiming GPU support. |

## Optional dependency failures

TorchRL keeps many integrations optional. Do not install every extra to fix a single import. Identify the owning workflow first:

- Environment wrappers and simulators: `envs-and-transforms`.
- Distributed collectors/replay: `collectors-and-replay`.
- LLM/VLA serving, Ray services, render/video: `llm-vla-and-services`.
- Maintainer optional-dependency CI policy: `development-and-testing`.

If the task is CPU-verifiable, report the optional backend as unverified rather than blocking the base workflow.

## TensorDict/key-contract failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Loss or module raises missing key | `in_keys`, `out_keys`, `set_keys`, or replay sample schema does not match | Print `td.keys(True)`, inspect the owning module/loss key contract, and use `NestedKey` tuples for nested data. |
| Environment rollout has unexpected `next` layout | Confusion between root keys and `("next", ...)` transition keys | Use `envs-and-transforms` and `step_mdp` guidance before feeding data to modules/losses. |
| Multi-agent loss shape mismatch | Agent dimension, group key, reward/done expansion, or advantage normalization dims inconsistent | Keep group layout consistent from env specs through modules, collectors, replay, and loss. |
| Recurrent training silently uses wrong hidden state | Missing primers, reset/is_init keys, or sequence burn-in/bootstrap masks | Combine `modules-and-policies` recurrent guidance with `collectors-and-replay` sequence sampling notes. |

## CLI/render failures

- Start with `rlrender --help` and `--validate-only`/`--dry-run` before creating artifacts.
- Check factory import specs, checkpoint payload keys, output suffix/format, observation/action/done/reward key overrides, and optional codec/display packages.
- If rendering a simulator, first prove the environment can produce pixels or render frames without the policy.

## When to stop

Stop and request a narrower scope or a prepared environment when:

- The user's requested behavior requires GPU/simulator/LLM serving/dataset credentials and no compatible backend is available.
- A native example would download models/data, start services, run long training, or mutate external state.
- A source contribution touches optional-dependency integrations but the corresponding CI label/environment is unavailable; document `ci/optdeps`, `ci/olddeps`, or GPU-runner needs.

## Helpful built-in checks

- Root environment smoke: `scripts/check_torchrl_env.py`.
- Environment rollout/spec smoke: `sub-skills/envs-and-transforms/scripts/smoke_env_rollout.py`.
- Collector/replay smokes: `sub-skills/collectors-and-replay/scripts/smoke_collector.py` and `smoke_replay_buffer.py`.
- Actor/recurrent smokes: `sub-skills/modules-and-policies/scripts/smoke_actor.py` and `smoke_recurrent_actor.py`.
- Loss introspection: `sub-skills/objectives-and-training/scripts/inspect_loss_keys.py`.
- VLA/service smokes: `sub-skills/llm-vla-and-services/scripts/check_vla_schema.py` and `smoke_services.py`.
- Contributor helpers: `sub-skills/development-and-testing/scripts/list_relevant_tests.py` and `check_gpu_marker_policy.py`.
