# BDDL Symbolic Task API Reference

## Purpose and prerequisites

Read this for CPU-only discovery, parsing, symbolic compilation, grounding,
callback-based evaluation, natural-language rendering, and string construction.
The distribution is `bddl` and the import package is also `bddl`. The verified
3.7.0 baseline can be installed and checked without a simulator:

```bash
python -m pip install "bddl==3.7.0"
python - <<'PY'
from importlib.metadata import version
import bddl
from bddl.activity import get_all_activities

print(version("bddl"))
print(len(get_all_activities()))
PY
```

The installed 3.7.0 package was live-imported to verify the signatures and
workflows below. It contained a `behavior-1k` domain, 26 declared predicates,
and 1,016 activity directories. Treat those counts as a version check, not as
timeless API constants. The repository README retains some historical domain
names and helper signatures; use the live 3.7.0 signatures here for this
checkout.

For synset taxonomy, abilities, generated object metadata, or knowledge-base
models, use the sibling [knowledge-base sub-skill](../../knowledge-base/SKILL.md).
No simulator or GPU is needed for the APIs below.

## Discovery and packaged lookup

Use API discovery rather than assuming a checkout layout:

```python
from bddl.activity import get_all_activities, get_instance_count
from bddl.config import get_definition_filename, get_domain_filename

activities = sorted(get_all_activities())
count = get_instance_count(activities[0])
problem_file = get_definition_filename(activities[0], 0)
domain_file = get_domain_filename("behavior-1k")
```

The resolved filenames are package-local inputs to parser functions. Treat
their absolute values as ephemeral diagnostics rather than portable data. The
bundled CLI omits paths in list mode and emits the selected domain/problem
paths only when `--activity` requests file-specific inspection.

| API | Input | Output / behavior |
| --- | --- | --- |
| `get_all_activities()` | None | Unsorted `list[str]` of packaged activity directory names; sort for deterministic output. |
| `get_instance_count(act)` | Exact activity id | Number of contiguous `problemN.bddl` instances. A missing activity normally surfaces as a filesystem error; non-contiguous ids raise `AssertionError`. |
| `get_definition_filename(behavior_activity, instance, domain=False)` | Activity and integer instance | Filename for `bddl/activity_definitions/<activity>/problemN.bddl`. With `domain=True`, this is a legacy behavior-100 lookup; prefer `get_domain_filename` for named domains. |
| `get_domain_filename(domain_name)` | For example, `"behavior-1k"` | Filename for packaged `domain_<domain_name>.bddl`; existence is not checked by the path constructor. |

Some builds may carry an `activity_manifest.txt` beside packaged definitions.
Do not make discovery depend on it: the verified `get_all_activities()` behavior
enumerates packaged activity directories, and a build can be usable without a
manifest. If a manifest exists, use it only as supplementary read-only data and
cross-check it against `get_all_activities()`.

## Verified signatures

### High-level activity API (`bddl.activity`)

```text
Conditions(behavior_activity, activity_definition, simulator_name, predefined_problem=None)
get_object_scope(conds)
get_initial_conditions(conds, scope, generate_ground_options=True)
get_goal_conditions(conds, scope, generate_ground_options=True)
get_ground_goal_state_options(conds, scope, goal_conditions)
evaluate_goal_conditions(goal_conditions, evaluate_fn)
get_reward(ground_goal_state_options, evaluate_fn)
get_natural_initial_conditions(conds)
get_natural_goal_conditions(conds)
get_all_activities()
get_instance_count(act)
```

`simulator_name` is historically named. In this CPU-only workflow it is the
packaged BDDL domain name, such as `"behavior-1k"`; it does not import or launch
a simulator.

`Conditions` parses both the named domain and either a packaged problem file or
`predefined_problem`. Its important attributes are:

- `parsed_objects`: `dict[str, list[str]]`, category to declared instances.
- `parsed_initial_conditions`: list of ground literal nested lists.
- `parsed_goal_conditions`: list of top-level goal expression nested lists.

`get_initial_conditions` omits top-level `inroom` literals before compilation.
Call `compile_state` directly with the package-produced set scope if an
inspection must preserve them. Both high-level getters inspect element zero:
they return `None` when that element exists but is falsey, while a truly empty
parsed section raises `IndexError`. Normal packaged definitions have non-empty
sections; validate custom parsed input before calling the wrappers.

### Parsing and construction (`bddl.parsing`)

```text
scan_tokens(filename=None, string=None)
parse_domain(domain)
parse_problem(behavior_activity, activity_definition, domain_name, predefined_problem=None)
gen_natural_language_condition(parsed_condition, indent=0)
gen_natural_language_conditions(parsed_conditions)
construct_full_bddl(behavior_activity, activity_definition, object_list, init_state, goal_state)
construct_bddl_from_parsed(behavior_activity, activity_definition, parsed_object_list, parsed_init_state, parsed_goal_state, domain='behavior-1k')
build_goal(goal_expr)
```

### Symbolic compilation (`bddl.condition_evaluation`)

```text
create_scope(object_terms)
compile_state(parsed_state, scope=None, object_map=None, generate_ground_options=True)
evaluate_state(compiled_state, evaluate_fn)
get_ground_state_options(compiled_state, scope=None, object_map=None)
get_predicate_for_token(token)
```

### Package paths (`bddl.config`)

```text
get_definition_filename(behavior_activity, instance, domain=False)
get_domain_filename(domain_name)
```

## Parsing data flow

### Tokenization

```python
from bddl.parsing import scan_tokens

tokens = scan_tokens(string="(define (problem demo-0) (:domain behavior-1k))")
```

Choose one input mode:

```python
from pathlib import Path
from bddl.config import get_definition_filename

problem_file = get_definition_filename("some_packaged_activity", 0)
from_file = scan_tokens(filename=problem_file)
from_string = scan_tokens(string=Path(problem_file).read_text())
assert from_file == from_string
```

`filename` opens a local file; `string` parses caller-supplied text without a
file lookup. If both are passed, the 3.7.0 implementation silently gives
`filename` precedence, so callers should still pass exactly one. `scan_tokens`
removes semicolon comments, lowercases tokens, and returns one nested list. It
raises:

- `ValueError("No input BDDL provided.")` when neither input is given.
- an exception containing `Missing open parenthesis`, `Missing close
  parenthesis`, or `Malformed expression` for structural token errors.

### Domain parsing

```python
from bddl.parsing import parse_domain

domain_name, requirements, types, actions, predicates = parse_domain("behavior-1k")
```

The return value is a five-tuple. `predicates` maps a token to its typed
parameter mapping. The verified domain declares unary and binary predicates;
it does not supply physical predicate implementations.

### Problem parsing

```python
from bddl.parsing import parse_problem

problem_name, objects, initial_state, goal_state = parse_problem(
    "some_packaged_activity", 0, "behavior-1k"
)
```

Inputs and outputs:

- When `predefined_problem is None`, activity and definition identify the
  packaged problem file.
- When a raw `predefined_problem` string is supplied, package file lookup for
  the problem is bypassed, but the declared `:domain` must still equal
  `domain_name`.
- `objects` is `{category: [instance, ...]}`.
- `initial_state` is one nested list per initial literal.
- `goal_state` is one nested list per top-level conjunct. A non-conjunctive
  top-level expression, such as `or`, remains one nested expression.

A small generic parsed representation looks like:

```python
objects = {
    "apple.n.01": ["apple.n.01_1", "apple.n.01_2"],
    "table.n.02": ["table.n.02_1"],
}
initial_state = [
    ["ontop", "apple.n.01_1", "table.n.02_1"],
    ["ontop", "apple.n.01_2", "table.n.02_1"],
]
goal_state = [
    [
        "exists",
        ["?apple.n.01", "-", "apple.n.01"],
        ["cooked", "?apple.n.01"],
    ]
]
```

Parsing confirms structure and domain-name agreement; it does not by itself
prove object metadata validity, predicate applicability, physical feasibility,
or current-world truth.

## Conditions, scope, and object map

```python
from bddl.activity import (
    Conditions,
    get_goal_conditions,
    get_initial_conditions,
    get_object_scope,
)

conds = Conditions("some_packaged_activity", 0, "behavior-1k")
scope = get_object_scope(conds)
object_map = conds.parsed_objects
compiled_initial = get_initial_conditions(
    conds, scope, generate_ground_options=False
)
compiled_goal = get_goal_conditions(
    conds, scope, generate_ground_options=False
)
```

For caller-supplied text, retain the same domain check while bypassing packaged
problem lookup:

```python
inline_conds = Conditions(
    "diagnostic_activity",
    0,
    "behavior-1k",
    predefined_problem=raw_bddl,
)
```

Keep these concepts separate:

- **Object map**: category to all declared instance names, for example
  `{"apple.n.01": ["apple.n.01_1"]}`. Quantifiers use it to select instances.
- **Scope**: the names available to expressions. In the verified API,
  `create_scope(object_map)` and `get_object_scope(conds)` produce a
  `set[str]` of declared instance names. Internals also accept a dictionary
  when variable or entity bindings are needed.
- **Parsed state**: nested lists containing logical operators, predicates,
  variables, category declarations, and object terms.
- **Compiled state**: `list[HEAD]`, one root per parsed top-level condition.
  Each root retains `.body`, `.children`, `.terms`, `.scope`, and `.object_map`;
  evaluation sets `.currently_satisfied`, while eager grounding adds
  `.flattened_condition_options`. Interior classes are in
  `bddl.condition_evaluation`; leaf predicate classes are in
  `bddl.predicates`; their base `Expression` is in `bddl.logic_base`.

For symbolic inspection, preserve instance-name strings. A dictionary scope
can map names to custom values for direct literals, but quantifier behavior is
simplest and least surprising with the package-produced name scope.

## Compilation, evaluation, and predicates

### Compile and evaluate a tiny symbolic state

```python
from bddl.condition_evaluation import create_scope, compile_state, evaluate_state
from bddl.predicates import TOKEN_TO_PREDICATE

object_map = {"apple.n.01": ["apple.n.01_1"]}
scope = create_scope(object_map)
parsed_state = [["cooked", "apple.n.01_1"]]
compiled = compile_state(
    parsed_state,
    scope=scope,
    object_map=object_map,
    generate_ground_options=False,
)

predicate_to_token = {cls: token for token, cls in TOKEN_TO_PREDICATE.items()}
truth = {("cooked", ("apple.n.01_1",)): True}

def evaluate_symbolically(predicate_cls, *entities, **kwargs):
    token = predicate_to_token[predicate_cls]
    return bool(truth.get((token, tuple(entities)), False))

all_true, indices = evaluate_state(compiled, evaluate_symbolically)
assert all_true
assert indices == {"satisfied": [0], "unsatisfied": []}
```

The live 3.7.0 compilation path calls
`evaluate_fn(predicate_cls, *resolved_entity_values, **predicate_kwargs)`. The
first argument is the concrete class, such as `bddl.predicates.Cooked`, not the
string `"cooked"`. In 3.7.0, `STATE_NAME` is assigned to predicate instances,
not to the class passed to the callback; recover the token with the reverse
`TOKEN_TO_PREDICATE` mapping shown above or compare class identity directly.
This class-valued contract is what `bddl.predicates.Predicate.evaluate`
implements; older type hints or prose that say `predicate_name: str` are
historical. The callback must return an actual Boolean on every call.
`evaluate_state` returns:

```text
(all_satisfied: bool, {"satisfied": [indices], "unsatisfied": [indices]})
```

This callback can evaluate a supplied symbolic truth table; BDDL does not infer
world truth from the activity definition alone. When `scope` is the set from
`create_scope`, resolved values are instance-name strings. With a dictionary
scope, direct names and quantifier bindings can resolve to caller-supplied
values, so the callback must key on those values consistently.

The high-level activity wrappers delegate to the same compiler/evaluator:

```python
from bddl.activity import (
    evaluate_goal_conditions,
    get_goal_conditions,
    get_ground_goal_state_options,
    get_object_scope,
    get_reward,
)

scope = get_object_scope(conds)
goals = get_goal_conditions(conds, scope, generate_ground_options=True)
all_true, indices = evaluate_goal_conditions(goals, evaluate_symbolically)
grounded = get_ground_goal_state_options(conds, scope, goals)
reward = get_reward(grounded, evaluate_symbolically)  # max satisfied fraction
```

`get_ground_goal_state_options` asserts that at least one consistent option
exists. `get_reward` expects non-empty grounded options whose inner condition
lists are non-empty.

### Logical and predicate tokens

`get_predicate_for_token(token)` recognizes these logical operators:

```text
and, or, not, imply, forall, exists, forn, forpairs, fornpairs
```

The verified predicate map contains:

```text
Unary:  cooked, frozen, open, folded, unfolded, toggled_on, hot, on_fire,
        future, real, broken
Binary: saturated, covered, filled, contains, ontop, nextto, under, touching,
        inside, overlaid, attached, draped, insource, inroom, grasped
```

For a logical operator it returns an expression class. For a known leaf token
it returns a constructor that creates the corresponding class from
`bddl.predicates`. An unknown token raises `KeyError`; disabling ground-option
generation does not make an unsupported token valid.

## Grounding

Grounding enumerates concrete satisfying branches for disjunctions and
quantifiers:

```python
from bddl.condition_evaluation import (
    compile_state,
    create_scope,
    get_ground_state_options,
)

object_map = {
    "apple.n.01": ["apple.n.01_1", "apple.n.01_2"],
}
scope = create_scope(object_map)
parsed_goal = [[
    "exists",
    ["?apple.n.01", "-", "apple.n.01"],
    ["cooked", "?apple.n.01"],
]]
compiled = compile_state(
    parsed_goal,
    scope=scope,
    object_map=object_map,
    generate_ground_options=True,
)
options = get_ground_state_options(compiled, scope=scope, object_map=object_map)
```

`options` is `list[list[HEAD]]`, shortest options first. Contradictory options
containing both an atom and its negation are removed.

Use `generate_ground_options=False` when only evaluation or structural
inspection is needed, especially for large conjunctions, disjunctions, or pair
quantifiers. Do not then call `get_ground_state_options` on that compiled tree;
recompile with `True` first. Eager grounding can grow combinatorially, and pair
quantifiers can fail when their category populations are empty or insufficient.

## Natural-language rendering

```python
from bddl.activity import (
    get_natural_goal_conditions,
    get_natural_initial_conditions,
)

initial_text = get_natural_initial_conditions(conds)
goal_text = get_natural_goal_conditions(conds)
```

For already parsed conditions:

```python
from bddl.parsing import gen_natural_language_conditions

lines = gen_natural_language_conditions(goal_state)
```

The output is `list[str]`, one string per parsed top-level condition. Rendering
is explanatory, not a validation or semantic equivalence proof. Keep the parsed
nested lists as the authoritative machine representation.

## Constructing and round-tripping BDDL text

Prefer the parsed constructor for behavior-1k:

```python
from bddl.parsing import construct_bddl_from_parsed, parse_problem

text = construct_bddl_from_parsed(
    "demo_activity",
    0,
    parsed_object_list=objects,
    parsed_init_state=initial_state,
    parsed_goal_state=goal_state,
    domain="behavior-1k",
)
parsed_again = parse_problem(
    "demo_activity",
    0,
    "behavior-1k",
    predefined_problem=text,
)
```

`construct_bddl_from_parsed` returns a string and performs no write. Parse it
again, compare normalized objects/init/goal, compile with a scope, and then run
appropriate validation checks before using it.

`construct_full_bddl(...)` also returns a string, but the verified implementation
uses the legacy `behavior-100` domain in its template and expects preformatted
string sections. Do not use it to claim behavior-1k output; prefer
`construct_bddl_from_parsed(..., domain="behavior-1k")`.

## Safe validation helpers

`bddl.bddl_verification` contains offline checker functions. Import and call
individual read-only checks; do not run its maintainer batch/data-generation
entry points as part of ordinary inspection.

Useful checks after `parse_problem` include:

```python
from bddl import bddl_verification as verify
from bddl.parsing import parse_domain

_, _, _, _, domain_predicates = parse_domain("behavior-1k")
verify.object_list_correctly_formatted(raw_bddl)
verify.all_objects_appropriate(objects, initial_state, goal_state)
verify.no_qmarks_in_init(raw_bddl)
verify.no_contradictory_init_atoms(initial_state)
verify.no_invalid_predicates(initial_state, goal_state, domain_predicates)
verify.no_uncontrolled_category("demo_activity", raw_bddl)
```

Expectations and limits:

- These functions signal invalid input mainly with `AssertionError` or
  `ValueError`; capture the checker name and exception message.
- `object_list_correctly_formatted` and `no_qmarks_in_init` inspect raw text and
  assume conventional section formatting. Tokenize and parse first so a generic
  parenthesis error is not confused with a style-check failure.
- `all_objects_appropriate` checks object references across sections.
- `no_invalid_predicates` compares atoms with the parsed domain declaration.
- `no_uncontrolled_category` compiles initial and goal conditions without eager
  grounding and can expose quantifier/category binding failures; it validates
  an inline definition as behavior-1k definition 0. Pair it with
  `all_objects_appropriate`, because the set-based scope does not reject every
  undeclared direct leaf term during compilation.
- Metadata-aware checks such as synset validity or predicate-property alignment
  require generated object metadata. Route that work through
  [knowledge-base](../../knowledge-base/SKILL.md) instead of treating a parser
  success as metadata validation.
