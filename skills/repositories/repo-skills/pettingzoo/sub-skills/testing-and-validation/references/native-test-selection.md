# Native Test Selection

Use native PettingZoo tests and examples only when the task is explicitly about validating a PettingZoo source checkout or comparing generated guidance against repo behavior. For ordinary installed-package use or custom downstream environments, prefer the bundled compliance helper and direct `pettingzoo.test` APIs.

## Safety Classes

| Class | When to run | When to skip | Expected signal |
| --- | --- | --- | --- |
| Bundled compliance helper | Default for custom envs, installed modules, and CI smoke validation | Skip only when PettingZoo itself is not installed | Pass banners for API helpers; no output for seed/render/max-cycles helpers |
| Source-checkout doc example tests | After the runtime skill is integrated and the current task intentionally validates a PettingZoo checkout | Skip outside a PettingZoo checkout or when base test dependencies are absent | Rock-paper-scissors AEC and Parallel examples pass low-cycle API tests |
| Wrapper and action-mask native tests | Only when the matching optional extras and test fixtures are available and wrapper behavior is in scope | Skip in base installs, minimal CI, or when Classic/Butterfly/GUI dependencies are missing | Wrapper episode counts, illegal-action termination, and action-mask determinism pass |
| Optional family environment tests | Only after installing the smallest matching extra for the selected family | Skip if the task does not need that family, if optional dependencies are missing, or if install would be too broad | Import, reset, and selected low-cycle API checks pass for the target family |
| Atari or ROM-backed tests | Only when ROM acquisition is explicitly authorized and already configured | Skip in default CI, offline validation, or when ROM files are absent | Import and constructor checks pass without ROM lookup errors |
| Render or GUI checks | Only with a display or with non-GUI render modes such as `ansi` or `rgb_array` | Skip `human` render mode in headless CI | Render result types match metadata |
| Training/tutorial examples | Only for explicit integration work with bounded user-approved runtime | Skip by default because they may require frameworks, network access, credentials, GPU, long training, or display | Manual metric or smoke signal defined by the user |

## Selection Ladder

1. **Custom environment development**: run `api,seed` with low cycles through the bundled helper.
2. **Headless CI**: run only API and seed checks, plus non-GUI render checks if the environment supports `ansi` or `rgb_array`.
3. **PettingZoo source-checkout verification**: add the safe doc-example pytest target after integration, because it exercises compact AEC and Parallel examples with base dependencies.
4. **Wrapper or mask changes**: add wrapper/action-mask native tests only when optional extras and fixtures are installed.
5. **Family-specific changes**: add the smallest family-specific native checks for the affected family; do not install `[all]` just to broaden validation.
6. **Release or maintainer validation**: run broader native suites only with explicit runtime, display, ROM, and dependency approval.

## Native Candidate Notes

- The compact docs-example tests are the safest native candidates after integration because they validate small AEC and Parallel custom examples through PettingZoo API helpers.
- Wrapper native tests are useful for `MultiEpisodeEnv`, `MultiEpisodeParallelEnv`, and `TerminateIllegalWrapper`, but some referenced environments require optional Classic or Butterfly dependencies.
- Action-mask native tests validate both observation-carried and info-carried masks, but should be treated as optional-extra or fixture-gated rather than default runtime validation.
- Render tests should be split by mode: `ansi` and `rgb_array` are CI-friendly when implemented without display access; `human` is an interactive/display check.
- Performance benchmark output is informational. It is not a pass/fail compliance gate and should not block ordinary custom-env CI without an explicit threshold.
- Save-observation checks are manual visual checks. They may write image files and require image-like Box observations, so keep them out of default automated validation.

## Skip Rules

Skip or defer native execution when any of these apply:

- The candidate imports optional packages not installed for the current task.
- The candidate requires Atari ROMs, external assets, a display, keyboard input, network access, API credentials, GPU, or long-running training.
- The candidate mutates generated docs/assets, writes large files, or has no bounded completion signal.
- The user asked for installed-package usage rather than source-checkout maintainer validation.
- A smaller direct compliance helper can validate the same contract with fewer dependencies.

## CI-Friendly Command Shape

Use a narrow matrix keyed by API flavor and skip render by default:

```bash
python scripts/run_compliance_checks.py --target my_pkg.my_aec_env_v0:env --api aec --checks api,seed --cycles 50
python scripts/run_compliance_checks.py --target my_pkg.my_parallel_env_v0:parallel_env --api parallel --checks api,seed --cycles 50
```

Add non-GUI render only when supported:

```bash
python scripts/run_compliance_checks.py --target my_pkg.my_aec_env_v0:env --api aec --checks render --no-render-human
```
