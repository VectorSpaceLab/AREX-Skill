# Extension Troubleshooting

Use this reference to diagnose failures in custom AiZynthFinder modules, class paths, optional plugin strategies, and source-edit tests.

## Dynamic Loading Failures

### `Unable to load module` or `ModuleNotFoundError`

Likely causes:

- The module path is misspelled.
- The module is not installed or not on Python import path in the runtime environment.
- The user supplied a filesystem path where AiZynthFinder expects an import path.
- A plugin module was referenced without making its directory importable.

Actions:

- Validate with `scripts/check_custom_aizynth_module.py --target package.module.ClassName --mode class` or a more specific mode.
- Convert file paths to importable packages/modules, or install the package in the environment that runs AiZynthFinder.
- Use a fully qualified class path for custom classes.
- Avoid adding private absolute checkout paths to reusable skill content; ask the user to configure their environment or package installation.

### Module imports but class/function is missing

Likely causes:

- The final class/function name is misspelled.
- The module exposes `post_processing` but the CLI flag used `--pre_processing`, or the reverse.
- The custom class is nested inside another object and not exported at module top level.

Actions:

- Run the checker with `--function pre_processing`, `--function post_processing`, or the exact `--class-name`.
- For CLI hooks, explain that a post-only module can be used with `--post_processing <module>`, not with `--pre_processing <module>`.
- Export the symbol at module top level or update the YAML class path.

## CLI Hook Problems

### Hook appears ignored

The CLI intentionally ignores hook modules that cannot be imported or do not expose the expected function. There may be no hard failure.

Actions:

- Validate the module with the checker before running the CLI.
- Confirm the module name, not a file path, is passed to the CLI hook flag.
- Confirm the function signature: `pre_processing(finder, index)` or `post_processing(finder)`.
- For post-processing, return a dictionary so the CLI can merge values into statistics.

### Pre-processing receives unexpected index

Single-SMILES CLI runs call `pre_processing(finder, -1)`. Multi-SMILES runs call it with a zero-based index over the not-yet-processed input after checkpoint skipping.

Actions:

- Treat `index == -1` as a single-target sentinel.
- Do not assume the index matches original file line number when checkpoint resume is active.

## Stock Extension Failures

### `Only objects ... inherited from StockQueryMixin can be added`

The object loaded into `finder.stock.load()` is not a `StockQueryMixin` subclass.

Actions:

- Subclass `aizynthfinder.context.stock.queries.StockQueryMixin`.
- Implement `__contains__(self, mol)`.
- Use optional `price`, `amount`, and `availability_string` methods only when those outputs are needed.

### Stop criteria do not work as expected

Stop criteria involving price or amount require the selected stock query to implement `price(mol)` or `amount(mol)`. The mixin defaults raise stock exceptions.

Actions:

- Implement the required method on the custom stock.
- If the stock cannot provide the value, remove that stop criterion and document the limitation.

## Scorer Failures

### `Only objects ... inherited from Scorer can be added`

The scorer does not inherit the expected base class.

Actions:

- Inherit from `aizynthfinder.context.scoring.scorers_base.Scorer` or the scoring package re-export.
- Implement `_score_node` and `_score_reaction_tree`.
- Provide a stable display name through `__repr__` or `scorer_name` so config references match the loaded collection key.

### Reward scorer not found during MCTS setup

`search.algorithm_config.search_rewards` names must match loaded scorer collection names.

Actions:

- Load the custom scorer through YAML `scorer` or direct API before tree setup.
- Check `repr(scorer)` because that is commonly used as the collection key.
- If using weighted rewards, ensure one weight per reward.

## Policy and Plugin Failures

### Expansion class incompatible

Symptoms include policy exceptions during load, missing `get_actions`, bad return shapes, or downstream reaction errors.

Actions:

- Inherit `ExpansionStrategy` and call the base initializer.
- Define `_required_kwargs` for required YAML keys.
- Return two aligned lists: reaction actions and numeric priors.
- Keep prediction caches resettable with `reset_cache`.

### Chemformer REST returns no actions

Likely causes:

- Optional Chemformer package/service is not installed or not running.
- URL, hostname, port, or route is wrong.
- Service returns non-OK status or times out.
- Disconnection-aware strategy was used without valid `break_bonds`.

Actions:

- Treat service availability as a user-provided prerequisite.
- Validate import/class shape locally with the checker, but test the URL separately with user-approved service checks.
- Increase search `time_limit` only after service latency is understood.
- For disconnection-aware use, validate `break_bonds` against the target molecule.

### ModelZoo fails during construction

Likely causes:

- `ssbenchmark`/ModelZoo stack is absent.
- `module_path` is missing.
- External model package, checkpoint, vocabulary, or GPU mode is user-specific and not configured.

Actions:

- Confirm optional packages are installed in the runtime environment.
- Ensure `module_path` is present in YAML.
- Keep model checkpoint/vocabulary paths user-supplied.
- Do not start GPU/service workflows from the checker.

## Search Algorithm Mismatches

### `search.algorithm` class cannot be loaded

Actions:

- Use `mcts` for built-in MCTS, otherwise use a fully qualified class path.
- Validate custom class import with `--mode search-tree-class`.
- Confirm the constructor accepts `config` and optional `root_smiles`.

### Non-MCTS algorithm behaves differently than expected

Actions:

- Do not apply MCTS-only interpretations to breadth-first, DFPN, or Retro*.
- Remember DFPN does not support filter policy or serialization/deserialization in the built-in implementation.
- For Retro*, validate molecule-cost configuration separately.

## Test and Environment Failures

### Optional dependency absent

Actions:

- Identify whether the failing test is optional-plugin, Mongo, route-distance, MolBloom, TensorFlow/remote-model, or service related.
- Narrow pytest selection to the edited subsystem when optional extras are unavailable.
- Record skipped optional coverage instead of masking real failures.

### Broad suite fails after a focused edit

Actions:

- Re-run the focused tests for the edited extension point.
- Separate unrelated optional dependency failures from regressions.
- Expand only to adjacent tests listed in `development-tests.md`.

## Difficult Diagnosis Patterns

### Post-only hook passed as pre-processing

If a module has `post_processing(finder)` but lacks `pre_processing(finder, index)`, the checker should report the missing pre hook and identify that the module is usable with the CLI `--post_processing <module>` flag.

### Plugin config without optional services

If a config uses Chemformer REST or ModelZoo but optional packages/services are absent, distinguish importability from runtime readiness: a class path may be valid while the REST endpoint, ModelZoo package, external model directory, checkpoint, vocabulary, or GPU setup is missing. Recommend validating the local import first, then checking service/package readiness through user-approved environment-specific commands.
