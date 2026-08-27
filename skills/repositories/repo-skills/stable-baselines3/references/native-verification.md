# Native Verification Candidates

This skill was built from SB3 source, docs, and test evidence. Original repo tests are verification candidates, not runtime dependencies for the generated skill.

## Safe Native Candidates

| Candidate | Capability | Expected signal | Skill owner |
| --- | --- | --- | --- |
| `tests/test_run.py::test_a2c` | on-policy short training | A2C learns briefly on CartPole/Pendulum | `training-and-algorithms` |
| `tests/test_run.py::test_dqn` | off-policy/discrete training | DQN short learn succeeds | `training-and-algorithms` |
| selected `tests/test_env_checker.py` cases | custom env validation | warnings/errors match unsupported spaces | `environments-and-vectorization` |
| selected `tests/test_vec_envs.py` cases | VecEnv behavior | reset/step/wrapper behavior is stable | `environments-and-vectorization` |
| selected `tests/test_callbacks.py` cases | callbacks | save/eval/stop callbacks trigger correctly | `evaluation-and-persistence` |
| selected `tests/test_save_load.py` parametrizations | persistence | save/load preserves parameters/actions | `evaluation-and-persistence` |
| selected `tests/test_custom_policy.py` cases | policy customization | policy kwargs/custom modules behave | `policies-and-customization` |
| selected `tests/test_her.py` and `tests/test_sde.py` cases | HER/gSDE | replay buffer and exploration constraints hold | `policies-and-customization` |

## Source Script Decisions

- `scripts/run_tests.sh` is reference-only because it is a repo-maintainer test command, not reusable SB3 user runtime logic.
- Docker scripts are excluded because they require host-specific Docker/GPU setup and broad side effects.
- Runtime helpers in this skill are safe adaptations from docs/tests and use public SB3 APIs.
