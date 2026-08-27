# Extension templates and base contracts

This reference distills pgmpy's extension templates, canonical package map, and base-class contracts into self-contained maintainer guidance. It is for contributors adding new public extension types, not for routine use of pgmpy APIs.

## Canonical extension map

| Extension category | Canonical package | Template responsibility | Public discovery/registration | Focused tests |
|---|---|---|---|---|
| Causal discovery algorithm | `pgmpy/causal_discovery/` | Copy the causal-discovery scaffold, rename the class/module, implement estimator parameters, `_fit`, learned graph attributes, examples, and references. | Add import and `__all__` entry in `pgmpy/causal_discovery/__init__.py`. | `pgmpy/tests/test_causal_discovery/test_<Algorithm>.py`; include sklearn-style fit/score behavior where appropriate. |
| Conditional independence test | `pgmpy/ci_tests/` | Copy the CI-test scaffold, define `_tags`, store constructor inputs, implement `_compute_result`, and return `_CITestResult`. | Add import and `__all__` entry in `pgmpy/ci_tests/__init__.py`; lookup uses `get_ci_test`. | `pgmpy/tests/test_ci_tests/test_<test_name>.py`; cover independent/dependent cases, conditioning sets, caching/symmetry, and invalid inputs. |
| Structure score | `pgmpy/structure_score/` | Copy the score scaffold, implement tags, constructor, `_local_score`, and optional structure priors. | Add import and `__all__` entry in `pgmpy/structure_score/__init__.py`; lookup uses `get_scoring_method`. | `pgmpy/tests/test_structure_score/test_<score_name>.py`; cover local/global score, caching, supported data type, and lookup by name. |
| Metric | `pgmpy/metrics/` | Copy the metric scaffold, choose supervised vs unsupervised base, define tags, implement `_evaluate`, and document interpretation. | Add import and `__all__` entry in `pgmpy/metrics/__init__.py`; lookup uses `get_metrics`. | `pgmpy/tests/test_metrics/test_<metric_name>.py`; cover graph/data validation and edge cases. |
| Dataset | `pgmpy/datasets/` | Copy the dataset scaffold, define tags, source paths, parsing/loader methods only when defaults are insufficient, and missing/category/ordinal metadata. | Dataset classes are discovered from the package; add the dataset name to the dataset test list. | `pgmpy/tests/test_datasets/test_datasets.py` or a focused dataset-specific test. |
| Example model | `pgmpy/example_models/<source>/` | Copy the example-model scaffold, choose the correct mixin, define tags and data path, and override loading only for non-standard formats. | Model classes are discovered from subpackages; create a source subpackage with `__init__.py` if needed and add the model name to the appropriate test list. | `pgmpy/tests/test_example_models/test_example_models.py` and format/schema-specific tests when needed. |

## Category contracts

### Causal discovery algorithms

- Base: `BaseCausalDiscovery`, which provides sklearn-style `fit(X, y=None)`, input validation, `n_features_in_`, `feature_names_in_`, and `score(X=... or true_graph=...)` once `causal_graph_` exists.
- Required implementation: `_fit(X)` for ordinary algorithms, or `_fit(X, independencies)` if using the constraint mixin pattern. Set `causal_graph_` to a `DAG`, `PDAG`, `MAG`, or `ADMG` as appropriate, set `adjacency_matrix_`, and preserve feature metadata from validated input.
- Existing helper patterns: constraint-based algorithms use a skeleton/orientation pattern; score-based algorithms use structure scores and legal graph operations; tree algorithms use pairwise edge-weight helpers. Use these only when the new algorithm truly matches the pattern.
- Tests should use small deterministic `pandas.DataFrame` fixtures, set progress flags off for automation, check learned graph type/edges, and verify `score` with a metric when meaningful.

### Conditional independence tests

- Base: `BaseCITest` from `pgmpy.ci_tests._base`.
- Required tags: `name`, `data_types`, `default_for`, `requires_data`, and `is_symmetric`.
- Required implementation: `_compute_result(X, Y, Z)` returning `_CITestResult(statistic=..., p_value=..., effect_size=..., attributes={...})`.
- Runtime behavior: `is_independent` returns `p_value_ >= significance_level`; `run_test` validates `X`, `Y`, and `Z`, handles symmetric cache keys when configured, and projects result attributes such as `statistic_`, `p_value_`, and `effect_size_` onto the instance.
- Use `_ResidualMixin` only for tests that need residualization with estimator fit/predict behavior. Guard estimator requirements explicitly.

### Structure scores

- Base: `BaseStructureScore` from `pgmpy.structure_score._base`.
- Required tags: `name`, `supported_datatype`, `default_for`, and the current parametericity tag used by the codebase. In this version, existing scores and the base class use the spelling `is_parameteric`; if maintainers intentionally rename it, update base class, concrete scores, template, and tests together.
- Required implementation: `_local_score(variable, parents)` returning a float. Public `local_score` wraps it with an LRU cache, and `score(model)` sums local scores over model nodes plus `structure_prior(model)`.
- Optional implementation: `structure_prior(model)` for absolute log-prior and `structure_prior_ratio(operation)` for add/remove/flip deltas used by search algorithms.
- Use data-type-specific patterns from existing discrete, Gaussian, and conditional-Gaussian scores; do not accept arbitrary score kwargs through `get_scoring_method` unless that API is intentionally changed and tested.

### Metrics

- Bases: `BaseSupervisedMetric` for graph-vs-graph metrics, `BaseUnsupervisedMetric` for data-vs-graph metrics.
- Supervised tags include `name`, `requires_true_graph=True`, `requires_data`, `lower_is_better`, `is_symmetric`, and `supported_graph_types`.
- Unsupervised tags include `name`, `requires_true_graph=False`, `requires_data=True`, `lower_is_better`, and `supported_graph_types`.
- Required implementation: `_evaluate(...)`; base `evaluate` validates graph types and, for unsupervised metrics, that data is a `pandas.DataFrame` containing all graph nodes.
- Tests should cover equal-node graph validation, supported graph families such as `DAG`/`PDAG` when declared, and metric interpretation direction.

### Datasets

- Base: `BaseDataset`; specialized bases are available for covariance, Tubingen cause-effect pairs, and simulated datasets.
- Required tags include name, variable/sample counts, ground truth/expert knowledge/missing/index flags, simulated/interventional flags, and discrete/continuous/mixed/ordinal flags.
- Static datasets normally rely on `base_url`, `data_url`, `ground_truth_url`, `expert_knowledge_url`, and default classmethods. Only override parsing when the default tabular/dagitty/expert-knowledge loaders cannot parse the source.
- Simulated datasets should build a model once in `__init__`, then implement instance methods `load_dataframe(self, n_samples=None)` and `load_ground_truth(self)` so generated data and graph share one model.
- Prefer `pgmpy.causal_discovery.ExpertKnowledge` for new dataset expert knowledge. A legacy estimator ExpertKnowledge import in old templates or code should be treated as compatibility-sensitive and checked against current source before use.

### Example models

- Base: `BaseExampleModel` plus one data-format mixin.
- Mixins: `DiscreteMixin` for gzipped BIF, `BIFMixin` for plain BIF, `ContinuousMixin` for Linear Gaussian BN JSON, and `DAGMixin` for dagitty strings.
- Required tags: `name` in `source/model` form, `n_nodes`, `n_edges`, `is_parameterized`, and exactly one of `is_discrete`, `is_continuous`, or `is_hybrid` when parameterized.
- If adding a new source namespace, create a subdirectory under `pgmpy/example_models/` with `__init__.py` and tests/list entries. Keep loaders deterministic and avoid relying on network during unit tests unless the test is explicitly marked/guarded.
- Continuous Linear Gaussian JSON files must satisfy the LGBN schema: top-level `nodes`, `arcs`, and `cpds`; each CPD has `coefficients` with `"(Intercept)"`, positive `variance`, and `parents`.

## Reference-only source artifacts

The six Python files under `devtools/extension_templates/` are reference scaffolds. Keep them synchronized with base-class APIs, but do not import them as runtime code. The R helper `devtools/scripts/convert_bnrep_models.R` is maintainer-only/reference-only because it installs/uses R packages and external bnRep conversion context; do not route ordinary pgmpy extension tasks through it.
