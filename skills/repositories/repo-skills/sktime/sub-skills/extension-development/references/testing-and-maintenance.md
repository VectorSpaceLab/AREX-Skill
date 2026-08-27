# Testing and Maintenance

## `check_estimator`

Verified signature:

`check_estimator(estimator, raise_exceptions=False, tests_to_run=None, fixtures_to_run=None, verbose=True, tests_to_exclude=None, fixtures_to_exclude=None)`

Start with narrow checks such as `tests_to_run="test_constructor"`. Use `raise_exceptions=True` only when you need the first traceback. A full check may need the developer testing dependency surface.

## Test scenarios

Generic tests use scenarios that provide method arguments and sequences. If a new estimator fails only one scenario, inspect the scenario's scitype/mtype, capability tags, and method sequence before changing estimator logic.

## Soft dependencies

Import soft dependencies inside estimator methods or `__post_init__`, not module level. Set `python_dependencies`, optional Python markers, and `tests:vm=True` for estimators that need a dependency-specific test environment.

## Focused pytest

When contributing inside a checkout, run focused checks such as `pytest -k "EstimatorName"` only after `check_estimator` gives a clear target. Broad test suites and release scripts are intentionally outside this runtime skill.
