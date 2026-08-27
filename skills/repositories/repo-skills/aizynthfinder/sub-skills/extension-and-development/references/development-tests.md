# Development and Focused Tests

Use this reference when editing AiZynthFinder source or adding a custom extension that needs focused validation. The project declares Python `>=3.10,<3.13`; do not require development extras for ordinary users who only consume an existing skill or run an installed package. Reserve these commands for source checkouts or user-approved development environments.

## Test Strategy

Start with the narrowest tests that cover the extension surface, then expand only if the edit crosses subsystem boundaries.

- Dynamic loader changes: `python -m pytest tests/utils/test_dynamic_loading.py`
- Context collection selection behavior: `python -m pytest tests/context/test_collection.py`
- Custom stocks and stock config: `python -m pytest tests/context/test_stock.py`
- Scorer implementations and scorer collection behavior: `python -m pytest tests/context/test_score.py`
- Expansion/filter policy config and custom strategy loading: `python -m pytest tests/context/test_policy.py tests/context/test_expansion_strategies.py`
- CLI hook behavior: `python -m pytest tests/test_cli.py -k "preprocessing or postprocessing or custom_stock"`
- MCTS changes: `python -m pytest tests/mcts`
- Breadth-first changes: `python -m pytest tests/breadth_first`
- DFPN changes: `python -m pytest tests/dfpn`
- Retro* changes: `python -m pytest tests/retrostar`

If the environment lacks optional dependencies, prefer focused `-k` selections over broad suite runs and record skips separately from failures.

## Extension Validation Before Tests

For user-provided modules, run the bundled checker from this sub-skill directory or by passing its resolved script path:

```bash
python scripts/check_custom_aizynth_module.py --mode post-processing --target my_hooks
```

Use checker modes that match the extension point:

- `pre-processing`: module function `pre_processing(finder, index)`.
- `post-processing`: module function `post_processing(finder)`.
- `smiles-extractor`: module function `extract_smiles`, preferably accepting one filename.
- `scorer-class`: class inheriting the scorer base and implementing score methods.
- `stock-object`: class/object compatible with stock query membership.
- `expansion-class`: class inheriting expansion strategy and defining `get_actions`.
- `search-tree-class`: class accepting `config`/`root_smiles` constructor shape and defining `one_iteration`.
- `retrostar-cost-class`: class defining `calculate(mol)`.

The checker imports modules and inspects symbols; it does not start REST services, run model inference, open GPU contexts intentionally, or execute full searches.

## Maintainer Tasks

The repository may expose maintainer automation through Invoke tasks. Treat those as maintainer conveniences, not as mandatory public runtime instructions.

- Use maintainer tasks only in a source checkout where the user expects repository development workflows.
- Prefer direct focused pytest commands for agent edits because they are clearer and easier to bound.
- Treat `invoke full-tests`, `invoke build-docs`, `invoke run_mypy`, and `invoke run_linting` as maintainer commands, not default runtime validation.
- Do not run formatting, docs, release, dependency update, or packaging tasks unless the user explicitly requested that maintenance activity.
- If a task installs dependencies or mutates the environment, ask or ensure the user has already authorized that class of mutation.

## Adding Tests for New Extensions

When adding a new extension to AiZynthFinder itself, mirror existing subsystem tests:

- Add dynamic import tests for a new loader rule.
- Add context collection tests if selection/loading semantics change.
- Add policy/stock/scorer tests with tiny deterministic fake objects rather than external services.
- Add CLI tests by patching `AiZynthFinder` or using tiny modules on `sys.path`, as existing hook tests do.
- For search algorithms, use deterministic fake expansion policies and tiny stock fixtures; avoid real model files or remote services.

## Optional Dependency Awareness

Optional surfaces may require extras or external packages:

- The `all` extra covers `pymongo`, `route-distances`, `scipy`, `timeout-decorator`, and `molbloom`.
- The `tf` extra covers `tensorflow`, `grpcio`, and `tensorflow-serving-api` for TensorFlow serving/remote-model surfaces.
- Mongo stock support requires `pymongo`.
- Route-distance/scorer surfaces may require route-distance dependencies.
- MolBloom stocks require `molbloom`.
- Chemformer REST and ModelZoo plugin strategies require external packages and services beyond core AiZynthFinder.

When tests fail because an optional dependency is absent, distinguish an expected skip/import limitation from a regression in the edited code. Do not paper over a missing optional service by pretending a plugin ran successfully.

## Suggested Validation Ladder

1. Run the checker for the exact custom module/class path.
2. Run the most focused pytest file for the changed subsystem.
3. If YAML loading changed, run dynamic loading plus the relevant context tests.
4. If CLI hooks changed, run the hook-specific `tests/test_cli.py` selection.
5. If search tree behavior changed, run the specific algorithm directory and one end-to-end finder/CLI smoke only if safe models/fixtures are available.
