# BDDL package overview

## Installation and package data

The retained package is distribution `bddl==3.7.0`, imported as `bddl`. Its
runtime surface is pure Python plus declared dependencies (`pytest`, `numpy`,
`networkx`, `jupytext`, `future`, and `nltk~=3.7` in the inspected packaging
metadata). Activity definitions, domain files, and generated taxonomy/knowledge
records are runtime package data; a source checkout is not a runtime
requirement when a complete distribution contains those files.

Use a clean, compatible environment and verify with:

```bash
python -m pip install "bddl==3.7.0"
python -m pip check
python -c "from importlib.metadata import version; import bddl; print(version('bddl'))"
```

Do not infer support for the rest of the BEHAVIOR-1K monorepo from BDDL
importability. OmniGibson requires a separate Isaac Sim runtime and is outside
this generated skill.

## Public module map

| Module | Use |
|---|---|
| `bddl.activity` | Higher-level activity `Conditions`, object scope, compiled initial/goal conditions, natural-language views, activity listing, grounded goals, and callback evaluation |
| `bddl.parsing` | Tokenization, domain/problem parsing, BDDL reconstruction, and natural-language condition rendering |
| `bddl.condition_evaluation` | Expression compilation, scope binding, grounding, predicate lookup, and callback-based evaluation |
| `bddl.predicates` / `bddl.logic_base` | Predicate and expression classes used by compiled conditions and evaluation callbacks |
| `bddl.config` | Package-relative activity/domain filename helpers and supported parser requirements |
| `bddl.object_taxonomy` | Synset hierarchy, category/substance resolution, abilities, and graph relations |
| `bddl.knowledge_base` | Public model exports and `KnowledgeBase` container |
| `bddl.knowledge_base.processing` | Explicit generated-data population helpers; use only with the caveats in the knowledge-base route |
| `bddl.knowledge_base.utils` | Analysis of already parsed condition trees; not a raw parser |

## Data-flow rule

For an activity workflow, resolve a domain and problem, inspect the parsed
object/initial/goal structures, create an object scope, compile the conditions,
and only then evaluate them through a caller-supplied callback. A callback
answers the state of a predicate for the caller's own object representation;
BDDL does not provide a simulator or physical object state.

For an object-metadata workflow, validate the synset/category/substance first,
query the taxonomy graph, and construct a populated `KnowledgeBase` only when
generated-data-backed models are actually needed. Keep `load_wordnet=False` for
offline inspection. Treat `KnowledgeBase(populate=False)` as an empty in-memory
container, not as a partially queried database.

## Data and version cautions

- Counts of activities, synsets, objects, tasks, and transitions are observations
  of one package version, not stable API invariants.
- `ObjectTaxonomy(hierarchy_type=...)` accepts a compatibility parameter, but
  the inspected version reads its packaged default hierarchy.
- `KnowledgeBase(populate=True, verbose=False, load_wordnet=False)` is the
  preferred one-time generated-data population path in the inspected version.
- The inspected `build_knowledgebase()` helper may populate twice because of its
  current default construction path; prefer the constructor or explicit empty-
  then-one-populate sequence and recheck later package revisions.
- WordNet helpers can require an NLTK corpus and may download data when enabled;
  they are not prerequisites for offline taxonomy queries.
