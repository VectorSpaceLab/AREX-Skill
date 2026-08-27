# Compliance Tests

PettingZoo exposes validation helpers through `pettingzoo.test`. They return normally on success, raise assertions or exceptions on contract failures, and may emit warnings for suspicious but not always fatal behavior. Prefer small cycle counts while developing and raise them only after the environment passes focused checks.

## Safe Validation Order

1. Import and construct the target factory without rendering.
2. Run API compliance with a low cycle budget such as `25` or `50`.
3. Run deterministic seed checks with the same low cycle budget.
4. Run render checks only for non-GUI modes in headless CI; run `human` mode only when a display is intentionally available.
5. Run `max_cycles` only for modules that expose both `env(max_cycles=...)` and `parallel_env(max_cycles=...)`.
6. Run save-observation and performance checks only as explicit manual checks because they write image files or benchmark for wall-clock time.

## Helper Matrix

| Helper | Signature | Pass signal | Safe default | Common failure signal |
| --- | --- | --- | --- | --- |
| AEC API | `api_test(env, num_cycles=1000, verbose_progress=False)` | Prints `Passed API test` | `num_cycles=25` during development | Wrong reset signature, spaces not cached, bad reward/termination/truncation dict keys, non-`None` AEC `step()` return, out-of-space observations |
| Parallel API | `parallel_api_test(par_env, num_cycles=1000)` | Prints `Passed Parallel API test` | `num_cycles=25` during development | Returned dict keys do not match live agents, dead agents are revived, spaces are recreated, `agents` is not updated after termination/truncation |
| AEC seed | `seed_test(env_constructor, num_cycles=500)` | Returns without output | `num_cycles=25` during development | Mismatched observations, rewards, terminations, truncations, infos, action masks, or sampled actions between identical seeds |
| Parallel seed | `parallel_seed_test(parallel_env_fn, num_cycles=500)` | Returns without output | `num_cycles=25` during development | Mismatched action-space seeding, observations, rewards, terminations, truncations, or infos |
| Render | `render_test(env_fn, custom_tests={})` | Returns without output | Opt-in; skip `human` in headless CI | Missing `metadata["render_modes"]`, `rgb_array` not `uint8` HxWx3, `ansi` not string, `human` not `None` |
| Max cycles | `max_cycles_test(mod)` | Returns without output | Opt-in for modules with both factories | Off-by-one cycle count, missing `max_cycles` constructor argument, mismatch between AEC and Parallel episode length |
| Performance | `performance_benchmark(env)` | Prints turns/cycles per second after about five seconds | Manual only | No assertion; output needs human interpretation |
| Save observation | `test_save_obs(env)` | Saves observations or prints why it skipped | Manual only | Observations not Box, not 0..255, not 2D/3D image-like, or unsupported channel count |

## CLI Wrapper

Use the bundled helper for installed package or custom module validation. It imports a `module:factory`, runs selected checks, caps cycle counts, avoids render by default, and prints likely fixes for common failures.

```bash
python scripts/run_compliance_checks.py \
  --target my_pkg.my_parallel_env_v0:parallel_env \
  --api parallel \
  --checks api,seed \
  --cycles 50
```

For AEC environments:

```bash
python scripts/run_compliance_checks.py \
  --target my_pkg.my_aec_env_v0:env \
  --api aec \
  --checks api,seed \
  --cycles 50
```

For non-GUI render validation, opt in explicitly:

```bash
python scripts/run_compliance_checks.py \
  --target my_pkg.my_aec_env_v0:env \
  --api aec \
  --checks render \
  --no-render-human
```

For `max_cycles`, pass any factory on the module; the helper validates the module itself because PettingZoo's `max_cycles_test` expects both `env` and `parallel_env` to exist:

```bash
python scripts/run_compliance_checks.py \
  --target my_pkg.my_env_v0:parallel_env \
  --api parallel \
  --checks max-cycles
```

## Direct Python Usage

AEC API compliance:

```python
from pettingzoo.test import api_test
from my_pkg import my_aec_env_v0

env = my_aec_env_v0.env()
try:
    api_test(env, num_cycles=50, verbose_progress=True)
finally:
    env.close()
```

Parallel API compliance:

```python
from pettingzoo.test import parallel_api_test
from my_pkg import my_parallel_env_v0

env = my_parallel_env_v0.parallel_env()
try:
    parallel_api_test(env, num_cycles=50)
finally:
    env.close()
```

Seed checks pass constructors, not already-created env instances:

```python
from pettingzoo.test import parallel_seed_test, seed_test

seed_test(my_aec_env_v0.env, num_cycles=50)
parallel_seed_test(my_parallel_env_v0.parallel_env, num_cycles=50)
```

## CI Selection

- Use `api,seed` as the default CI set for custom environments; these are headless and deterministic when the env has no hidden external state.
- Keep `--cycles` low in pull-request CI, then run larger explicit stress checks after API failures are fixed.
- Avoid `render` in CI unless using `--no-render-human` and the env supports `ansi` or `rgb_array` without display access.
- Avoid `max-cycles` unless the module intentionally supports `max_cycles` in both AEC and Parallel factories.
- Do not include performance benchmarks, long training examples, network-backed examples, ROM-backed Atari environments, or GUI-only checks in default CI.

## Interpreting Warnings

Warnings from PettingZoo helpers often flag portability issues rather than immediate API failure: non-string agent names, unusual observation spaces, all-zero observations, or missing optional attributes such as `possible_agents`. Treat warnings as review items, but prioritize assertion failures because they usually break downstream agents or wrappers.
