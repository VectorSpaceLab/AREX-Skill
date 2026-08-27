# Contributor workflows for pgmpy extensions

Use this reference after selecting the extension category. It translates pgmpy's contributor guidance into a focused developer loop for public extension work.

## Before coding

1. Confirm the user-facing scope: new algorithm/test/score/metric/dataset/model, expected public API, data type, optional dependencies, and acceptance tests.
2. Check existing implementations in the same canonical package and reuse their naming, tag, error-message, progress, and test patterns.
3. Start from the matching extension template. If the task changes a base-class API or a tag contract, update the corresponding template and focused tests in the same change.
4. Preserve backwards compatibility unless the user or maintainer explicitly accepts a breaking change. New canonical implementation can coexist with legacy compatibility imports; do not move new functionality into deprecated `pgmpy.estimators`.
5. For significant algorithms, compare against at least one external reference implementation or convention when practical, such as causal-learn/DoWhy/scikit-learn APIs or bnlearn/pcalg/dagitty behavior, and use that comparison to inform tests and examples.

## TDD loop

1. Write the smallest meaningful failing test first when the change affects behavior.
2. Implement the extension in the canonical package.
3. Run the focused test file or selected test method.
4. Add registration/listing/lookup tests so users can discover the object through the public factory/listing API.
5. Add docstrings and docs/examples only for the public surface. Keep examples tiny enough for doctests or mark expensive/network cases appropriately.
6. Run formatting/linting through pre-commit when available.

Avoid broad refactors, redundant type checks, and catch-all `try`/`except` blocks. Prefer direct code that follows existing package style and can be read top to bottom.

## Focused validation commands

Run from a pgmpy checkout unless a command explicitly imports an installed package. Replace names with the new extension's names.

| Extension | First focused checks |
|---|---|
| Causal discovery | `pytest -q pgmpy/tests/test_causal_discovery/test_MyAlgorithm.py`; include a tiny deterministic data fixture and graph-attribute assertions. |
| CI test | `pytest -q pgmpy/tests/test_ci_tests/test_my_ci_test.py`; check independent/dependent examples, conditioning validation, cache/symmetry, and `get_ci_test("name", data=...)`. |
| Structure score | `pytest -q pgmpy/tests/test_structure_score/test_my_score.py`; check `local_score`, `score(model)`, caching behavior if relevant, and `get_scoring_method("name", data)`. |
| Metric | `pytest -q pgmpy/tests/test_metrics/test_my_metric.py`; check `evaluate`/`__call__`, graph type validation, node-alignment errors, and metric direction. |
| Dataset | `pytest -q pgmpy/tests/test_datasets/test_datasets.py` or a dataset-specific file; check `list_datasets`, `load_dataset`, tags, shapes, missing data, ground truth, and expert knowledge. |
| Example model | `pytest -q pgmpy/tests/test_example_models/test_example_models.py` or a model-specific selection; check `list_models`, `load_model`, graph/model class, node/edge counts, and format parsing. |
| LGBN JSON asset | `pytest -q pgmpy/tests/test_devtools/test_lgbn_schema.py` plus any model-load test for the new continuous example model. |

If docstrings include runnable examples, run a narrow doctest target before broadening:

```bash
pytest --doctest-modules --ignore=pgmpy/tests pgmpy/<canonical-package-or-module>
```

Before handing off for review, run:

```bash
pre-commit run --all-files
```

when pre-commit is installed. If unavailable, state that explicitly and run the smallest available ruff/pytest checks instead.

## Static placement helper

The bundled helper can be used before pytest to catch common placement and registration omissions:

```bash
python <path-to-extending-pgmpy>/scripts/extension_template_check.py --repo <pgmpy-checkout> --category ci-test --module-name my_ci_test --class-name MyCITest --registry-name my_ci_test
```

Use `--category all` to list expected template/package/test directories. The helper is read-only and never replaces source review or pytest.

## Registration and docs checklist

- New public classes in `causal_discovery`, `ci_tests`, `structure_score`, and `metrics`: update package `__init__.py` imports and `__all__`.
- New datasets: make the class discoverable under `pgmpy/datasets`, set a unique `name` tag, and add the name to dataset tests.
- New example models: place the class under the correct source subpackage, create a new source subpackage only when needed, set `name` as `source/model`, and update example-model tests.
- User-facing APIs: update the matching API autosummary or guide section when maintainers expect documentation for the feature. Keep examples independent of local checkout paths.
- New citations in score/model/algorithm docstrings: add bibliography entries when docs use citation roles.
- Optional dependencies: mark tests with import skips or credential/network skips instead of importing optional packages unguarded at module import time.

## Optional dependency boundaries

The minimum verified environment for this skill covered core CPU workflows. Treat these as optional unless the user explicitly installs and verifies them:

- torch/Pyro for `FunctionalBayesianNetwork` and `FunctionalCPD`.
- litellm plus provider credentials/network for LLM-assisted discovery.
- plotting extras such as daft/pygraphviz and system graphviz support.
- remote dataset/model downloads when a local cache is not available.

Do not install broad extras just to add a core extension. Add targeted guards and document the extra only for the extension that requires it.

## Human workflow boundaries

- Do not run `git commit` or `git push`; leave changes in the working tree for human review.
- It is fine to suggest logical commit units or a commit message.
- Follow the project's AI disclosure expectations if AI tools assisted the contribution; the contributor remains responsible for explaining and verifying every change.
