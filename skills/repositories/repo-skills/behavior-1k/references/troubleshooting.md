# BDDL troubleshooting

## Install and import

**Symptom:** `ModuleNotFoundError: bddl` or a submodule import fails.

**Check:** use the same interpreter for installation and execution:

```bash
python -m pip install "bddl==3.7.0"
python -m pip check
python -c "import bddl; from importlib.metadata import version; print(version('bddl'))"
```

A successful import of `bddl` does not prove that package data or OmniGibson
is available. If only a partial wheel was installed, reinstall a complete
matching distribution rather than adding arbitrary source paths.

## Missing package data

**Symptom:** activity/domain lookup raises `FileNotFoundError`, taxonomy
construction cannot read its hierarchy, or populated KB construction cannot
find generated records.

**Cause:** the distribution is incomplete, package data was omitted, or the
installed version does not match its generated records.

**Recovery:** verify the distribution version and use a complete `bddl==3.7.0`
installation. Do not run maintainer `data_generation` pipelines as a routine
repair; they may require external spreadsheets, source data, or expensive
processing. Retry with an empty `KnowledgeBase` only to isolate container
importability from data population.

## Activity/domain lookup

**Symptom:** an activity or instance is rejected by the activity inspector.

**Check:** omit `--activity` to list exact packaged ids, then use a non-negative
zero-based `--instance`. The helper reports the available contiguous range.
Use the exact domain short name expected by the package, commonly
`behavior-1k`; it resolves a package-relative `domain_<name>.bddl` file.

A domain file can parse successfully while a problem definition is absent or
malformed. Treat those as separate package-data versus definition errors.

## Syntax and predicate errors

**Symptom:** `parse_domain`, `parse_problem`, `scan_tokens`, or condition
compilation fails.

**Check:** inspect a known packaged definition first, then compare custom text
with the supported BDDL requirement forms and the selected domain's predicate
names. `scan_tokens(filename=...)` and `scan_tokens(string=...)` are alternate
inputs; do not pass both. A parser error is not fixed by installing a simulator.

Unsupported predicate tokens indicate a domain/API mismatch. Use the domain's
registered predicates and check arity before constructing a condition. Keep
nested-list shapes produced by `parse_problem`; raw strings are not compiled
condition objects.

## Scope, grounding, and callbacks

**Symptom:** a compiled expression cannot bind an object, grounding produces no
options, or evaluation returns confusing results.

**Check:** create the scope from the parsed object declarations with
`activity.get_object_scope(conds)` or `condition_evaluation.create_scope(...)`;
pass the same object map to `compile_state` when the workflow requires it. Use
`get_ground_state_options` only after compilation and expect multiple options
for disjunctions/quantifiers. Large quantified expressions can expand
combinatorially; inspect parsed conditions before requesting every ground
option.

`activity.evaluate_goal_conditions` and `condition_evaluation.evaluate_state`
call a user-supplied predicate callback. The callback must accept the predicate
class/token contract documented by the API reference and return a truth value
for each predicate evaluation. BDDL reports symbolic satisfaction; it does not
supply a scene, object handles, or a simulator state.

## Taxonomy and KB

**Symptom:** taxonomy methods raise an assertion or a category resolver returns
`None`.

**Check:** call `is_valid_synset` before graph queries. Resolve a category or
substance and handle `None` or ambiguous matches before passing the result to
relationship methods. Use the taxonomy inspector's list modes for spelling
checks.

**Symptom:** populated KB fails while an empty KB works.

**Cause:** generated runtime records are missing/inconsistent, or an optional
WordNet path was enabled. Keep `load_wordnet=False` for offline inspection and
use the constructor's one-time population path. Do not call
`populate_knowledgebase` twice on one populated container.

## Scope boundary failures

**Symptom:** a request asks to launch an environment, satisfy a condition with a
robot, inspect OmniGibson object states, or use Isaac Sim/GPU behavior.

**Recovery:** stop routing through this skill. BDDL can describe symbolic
requirements, but this generated skill deliberately provides no simulator
backend or CPU substitute for OmniGibson. Use a separately verified
OmniGibson/Isaac Sim skill when one exists.
