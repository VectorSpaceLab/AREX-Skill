# BDDL Symbolic Task Troubleshooting

## Triage order

Classify the failure before changing the definition:

1. **Import**: can Python import `bddl`, `bddl.activity`, and `bddl.parsing`?
2. **Lookup**: does the exact activity exist and is the instance in range?
3. **Packaged domain**: does `parse_domain("behavior-1k")` succeed?
4. **Syntax**: can `scan_tokens` and `parse_problem` read the problem?
5. **Symbolic validity**: are predicate tokens, arities, objects, categories,
   scope, and object map consistent?
6. **Grounding/evaluation**: was the tree compiled with the intended option,
   and does the callback satisfy the API contract?
7. **Physical runtime**: if all symbolic checks pass but a simulator fails,
   stop diagnosing it as a BDDL parser failure.

The bundled inspector deliberately gives activity lookup, package-data, and
syntax/parse failures different error prefixes and exit codes:

```bash
python sub-skills/symbolic-tasks/scripts/inspect_bddl_activity.py --activity <activity> --instance 0 --domain behavior-1k
```

## Install or import failure

### Symptom

```text
ModuleNotFoundError: No module named 'bddl'
```

### Likely cause

The `bddl` distribution is absent from the active Python interpreter, or the
command uses a different interpreter from the installer.

### Check

```bash
python -c "from importlib.metadata import version; print(version('bddl'))"
python -c "from importlib.metadata import version; import bddl; print(version('bddl'))"
```

### Recovery

```bash
python -m pip install "bddl==3.7.0"
```

Use `python -m pip`, not an unqualified `pip`, to keep installation and import
on the same interpreter. Do not install OmniGibson, Isaac Sim, CUDA, or a GPU
stack for symbolic BDDL inspection.

### Symptom

Importing a BDDL submodule reports a missing dependency such as `future`,
`numpy`, or `nltk`, even though `bddl` metadata is present.

### Likely cause

An incomplete or manually copied installation bypassed distribution
dependencies.

### Check

```bash
python -m pip check
python -c "from bddl.activity import Conditions; from bddl.parsing import parse_domain"
```

### Recovery

Reinstall the public distribution in the active environment rather than
copying the import package:

```bash
python -m pip install --upgrade --force-reinstall "bddl==3.7.0"
```

If only `from bddl import bddl_verification` fails on `pandas`, core parsing may
still be usable. Install `pandas` only when those offline checker helpers are
actually required, or perform the core parser/compiler checks without importing
that module.

## Missing activity or instance

### Symptom

The bundled inspector reports `activity lookup error`, or direct code raises a
filesystem error from `get_instance_count(activity)`.

### Likely cause

- Activity ids are exact package directory names, usually lowercase with
  underscores.
- The requested activity is not in this installed BDDL version.
- The requested instance is negative or outside the packaged contiguous range.

### Check

```python
from bddl.activity import get_all_activities, get_instance_count

activities = sorted(get_all_activities())
print("requested_activity" in activities)
if "requested_activity" in activities:
    print(get_instance_count("requested_activity"))
```

Or omit `--activity` to list ids from the bundled inspector.

### Recovery

Copy an exact id from `get_all_activities()`. Select an integer instance in
`range(get_instance_count(activity))`. Do not rename the request speculatively,
and do not report a malformed BDDL file until lookup has succeeded.

A missing `activity_manifest.txt` alone is not a lookup failure; current
discovery is through `get_all_activities()` and packaged activity directories.

## Missing packaged definition or domain

### Symptom

```text
FileNotFoundError: ... problemN.bddl
FileNotFoundError: ... domain_behavior-1k.bddl
```

or the bundled inspector reports `package data error` after activity lookup.

### Likely cause

- Package data was omitted from a broken wheel or manually copied install.
- The selected domain name is not packaged.
- Distribution metadata and import files come from different versions.
- Activity ids exist but the expected contiguous problem file is absent.

### Check

```python
from pathlib import Path
from bddl.config import get_definition_filename, get_domain_filename

print(Path(get_definition_filename("requested_activity", 0)).is_file())
print(Path(get_domain_filename("behavior-1k")).is_file())
```

Keep resolved absolute paths local; do not publish them in reports or generated
artifacts.

### Recovery

1. Confirm the distribution version with `importlib.metadata.version("bddl")`.
2. Reinstall the complete distribution with `python -m pip install
   --force-reinstall "bddl==3.7.0"`.
3. Use `behavior-1k` only when `parse_domain("behavior-1k")` succeeds.
4. If a custom domain is intended, package `domain_<name>.bddl` with the BDDL
   installation or pass a valid installed domain name; a path string is not a
   domain-name substitute.

Do not hard-code a checkout location to work around missing package data.

## Malformed BDDL syntax

### Symptom

- `Missing open parenthesis`
- `Missing close parenthesis`
- `Malformed expression`
- `Problem ... does not match problem pattern`
- `Different domain specified in problem file`
- a section is ignored and a message says it `is not recognized in problem`

### Likely cause

Unbalanced parentheses, multiple top-level expressions, missing `(define ...)`,
a misspelled section marker, or disagreement between the declared `:domain`
and the `domain_name` argument.

### Check

Separate tokenization from semantic section parsing:

```python
from bddl.parsing import scan_tokens, parse_problem

scan_tokens(string=raw_bddl)
parse_problem(
    "diagnostic_activity",
    0,
    "behavior-1k",
    predefined_problem=raw_bddl,
)
```

A missing packaged activity is tested through `get_all_activities()`; malformed
inline syntax is tested through `predefined_problem`. These are independent
failure classes.

### Recovery

1. Balance parentheses and retain one top-level `(define ...)` expression.
2. Include `(problem <name>)`, `(:domain behavior-1k)`, `(:objects ...)`,
   `(:init ...)`, and `(:goal ...)` with exact section tokens.
3. Ensure `:domain` matches the parsed packaged domain's declared name.
4. Re-run `scan_tokens`, then `parse_problem`, then symbolic validators in that
   order.

Do not use natural-language rendering as a syntax validator.

## Unsupported or invalid predicate

### Symptom

- `KeyError` from `get_predicate_for_token` or `compile_state`.
- `AssertionError: Invalid predicate: <token>` from
  `no_invalid_predicates`.
- A predicate has the wrong number of object arguments.

### Likely cause

The token is absent from the logical operator map or
`bddl.predicates.TOKEN_TO_PREDICATE`, is declared differently in the selected
domain, or is used with the wrong arity.

### Check

```python
from bddl.condition_evaluation import get_predicate_for_token
from bddl.parsing import parse_domain

_, _, _, _, domain_predicates = parse_domain("behavior-1k")
print(domain_predicates.get("suspect_token"))
get_predicate_for_token("suspect_token")
```

Then run:

```python
from bddl import bddl_verification as verify
verify.no_invalid_predicates(initial_state, goal_state, domain_predicates)
```

### Recovery

Use a token declared in both the selected domain and the package predicate map,
and match the domain-declared arity. `generate_ground_options=False` only skips
eager option enumeration; it does not allow an unsupported predicate. Adding a
new predicate requires a coordinated domain and Python predicate extension,
which is outside ordinary activity inspection.

## Invalid object scope or object map

### Symptom

- `UncontrolledCategoryError`
- `KeyError` naming a quantified category
- `AssertionError: Middle was not a hyphen`
- a quantified expression has no children or produces surprising bindings
- object-reference validation says an init/goal term is absent from `:objects`

### Likely cause

- An object instance appears in a condition but not in the declared object map.
- A quantifier category is missing from `object_map`.
- The quantifier declaration is not `["?variable", "-", "category"]`.
- `scope` and `object_map` were accidentally swapped.
- A custom dictionary scope maps terms in a way the symbolic callback does not
  expect.

The standard `create_scope` result is a set and is intentionally lightweight;
for some direct leaf expressions the compiler does not validate every name in a
set against the object map. A dictionary scope exercises the stricter term
lookup path, while the verification helpers provide section-wide checks.

### Check

```python
from bddl.condition_evaluation import create_scope

scope = create_scope(objects)
assert all(instance in scope for instances in objects.values() for instance in instances)
strict_scope = {name: name for name in scope}
```

For each quantified category, check `category in objects` and verify that its
instance list is non-empty when the operator requires candidates. For a full
inline definition, run `all_objects_appropriate(...)` and
`no_uncontrolled_category(...)` after parsing. To deliberately test strict
unresolved-term handling, compile with `strict_scope` and an undeclared term.

### Recovery

- Declare every referenced instance under exactly one intended category.
- Pass category-to-instance `objects` as `object_map` and the result of
  `create_scope(objects)` as `scope`.
- Keep the canonical `?variable - category` quantifier shape.
- Use package-produced string scopes for CPU symbolic inspection unless custom
  entity binding is specifically needed.

`UncontrolledCategoryError` stores the unresolved term in its `malformed_cat`
attribute; log that value explicitly because the exception text may be empty.
For taxonomy or synset metadata questions, use the sibling
[knowledge-base sub-skill](../../knowledge-base/SKILL.md).

## Ground-option failures or blow-up

### Symptom

- `flattened_condition_options` is missing when calling
  `get_ground_state_options`.
- Grounding uses excessive time or memory.
- Pair quantifiers fail with an index/shape error or `ForNPairs asks for more
  pairs than instances available`.
- No consistent grounded option remains.

### Likely cause

- The state was compiled with `generate_ground_options=False` and then passed
  to the ground-option API.
- A goal's disjunctions and quantifiers produce a Cartesian combinatorial
  expansion.
- A quantified category is empty, or `fornpairs` requests more pairs than the
  category populations permit.
- Every option contains an atom together with its negation.

### Check

Inspect category population sizes and the parsed logical structure before eager
grounding. Confirm the compile flag used for the exact tree.

### Recovery

- For evaluation only, keep `generate_ground_options=False` and do not call
  `get_ground_state_options`.
- For grounding, recompile the parsed state with `True`; do not try to mutate an
  already compiled tree into grounded mode.
- Test a reduced symbolic fixture before grounding a large real activity.
- Bound category sizes and inspect `or`, `forall`, `exists`, `forn`,
  `forpairs`, and `fornpairs` branches for combinatorial growth.
- Correct impossible pair counts or contradictory branches rather than
  treating an empty option list as a simulator error.

## Evaluation callback misuse

### Symptom

- The callback compares its first argument with a string and never matches.
- Accessing `predicate_cls.STATE_NAME` raises `AttributeError`.
- Compound expressions raise an assertion involving `NoneTypes`.
- All conditions appear unsatisfied despite a matching truth table.
- A dictionary scope sends custom entity values while the callback expects names.

### Likely cause

The current leaf API calls
`evaluate_fn(predicate_cls, *entities, **predicate_kwargs)`, where the first
argument is a concrete class, not a token string. In 3.7.0, `STATE_NAME` is
assigned to predicate instances and is therefore not available on that class
argument. The callback returned `None` or a non-Boolean, used mismatched entity
values, rejected forwarded keyword arguments, or expected custom values while
the package-produced set scope contains instance-name strings.

### Check

Temporarily reverse the public predicate map and log the exact callback values:

```python
from bddl.predicates import TOKEN_TO_PREDICATE

predicate_to_token = {cls: token for token, cls in TOKEN_TO_PREDICATE.items()}

def inspect_callback(predicate_cls, *entities, **kwargs):
    print(predicate_to_token[predicate_cls], entities, kwargs)
    return False
```

### Recovery

Recover the token with the reverse `TOKEN_TO_PREDICATE` mapping, key the truth
table by the exact resolved entity values, accept forwarded keyword arguments,
and always return `True` or `False`. A set scope yields names; a dictionary
scope can substitute caller values. Keep side effects out of a symbolic
inspection callback.

## Validation-helper failure

### Symptom

A checker fails on raw-text splitting even though `scan_tokens` and
`parse_problem` succeed, or importing the checker module pulls in metadata
requirements not needed by core parsing.

### Likely cause

Some offline helpers assume canonical whitespace/section layout; metadata-aware
checks also depend on generated BDDL knowledge data.

### Check

Run core checks in increasing depth:

1. `scan_tokens`
2. `parse_domain` and `parse_problem`
3. `compile_state(..., generate_ground_options=False)`
4. narrowly selected `bddl_verification` helpers

Record the exact checker name and exception rather than reporting only
"validation failed."

### Recovery

Use parser results as the structural representation, normalize constructed text
with `construct_bddl_from_parsed`, and re-run only the checker appropriate to
the desired guarantee. Route metadata validity and predicate-property
compatibility through [knowledge-base](../../knowledge-base/SKILL.md). Do not
run maintainer batch or data-generation routines for read-only task inspection.

## Symbolic success but simulator failure

### Symptom

The definition parses, compiles, grounds, and evaluates against a synthetic
truth table, but scene sampling, object-state checks, robot actions, or task
execution fail elsewhere.

### Cause

BDDL describes objects and logical initial/goal conditions. Symbolic success
does not prove that assets exist, a physical state can be sampled, a controller
can reach it, or a simulator implements every object-state predicate.

### Recovery

Report the symbolic checks that passed and preserve the parsed condition that
reaches the runtime boundary. Route the remaining issue to the simulator or
environment owner. Do not import OmniGibson or Isaac Sim here, do not classify a
GPU/runtime failure as malformed BDDL, and do not claim physical feasibility
from parser success.
