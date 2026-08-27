# Knowledge-base troubleshooting

Keep this workflow CPU-only. The checks below inspect package data and
in-memory objects; none of the recoveries runs a simulator or the maintainer
data-generation pipeline.

## Import or version failure

**Symptom:** `ModuleNotFoundError: No module named 'bddl'`, an import fails from
`bddl.knowledge_base`, or the package version is not the expected release.

**Cause:** BDDL is not installed in the active Python environment, a different
BDDL release is shadowing it, or the environment has incomplete dependencies.

**Check:**

```bash
python -c 'import bddl, importlib.metadata; print(bddl.__name__); print(importlib.metadata.version("bddl"))'
python -m pip check
```

The intended distribution reports version `3.7.0` and imports as `bddl`.

**Recovery:** Install a complete BDDL 3.7.0 distribution through the supported
Python environment process, then confirm the version again. Do not install
simulator packages for this CPU-only workflow.

## Missing packaged generated data

**Symptom:** `ObjectTaxonomy()` raises `FileNotFoundError` for the hierarchy,
`KnowledgeBase(populate=True)` fails while opening a CSV/JSON file, or a
packaging check shows no `bddl/generated_data/` records.

**Cause:** The installation contains Python modules but not the generated
runtime records, or the package data is incomplete for this BDDL release.

**Check:** Use package-relative checks, without printing installation paths in
shared output:

```python
import importlib.resources as resources

root = resources.files("bddl") / "generated_data"
for name in (
    "output_hierarchy_properties.json",
    "object_inventory.json",
    "allowed_room_types.csv",
):
    print(name, (root / name).is_file())
```

Also run:

```bash
python sub-skills/knowledge-base/scripts/inspect_bddl_taxonomy.py --help
python sub-skills/knowledge-base/scripts/inspect_bddl_taxonomy.py --synset entity.n.01 --children
```

**Recovery:** Reinstall or obtain a complete BDDL 3.7.0 distribution that
ships its generated runtime data. If only taxonomy data is present, use
`ObjectTaxonomy` for taxonomy work and report that full KB population is
blocked. Do not run `bddl/data_generation/*`, invent replacement inventory
records, or claim that a partial KB is complete.

## Empty KB versus failed or partial population

**Symptom:** `len(KnowledgeBase(populate=False).all_synsets()) == 0`, or a
populated KB has no tasks/categories/transitions when those records are
expected.

**Cause:** `populate=False` intentionally constructs only the container. A
partial count may instead indicate a population exception, missing generated
records, or duplicate population.

**Check:** Compare explicitly and capture the first exception:

```python
from bddl.knowledge_base import KnowledgeBase

empty = KnowledgeBase(populate=False, verbose=False)
print(len(empty.all_synsets()), len(empty.all_categories()), len(empty.all_tasks()))

populated = KnowledgeBase(populate=True, verbose=False, load_wordnet=False)
print(len(populated.all_synsets()), len(populated.all_categories()), len(populated.all_tasks()))
```

The empty object should report zero for those collections. For a normal
3.7.0 packaged-data smoke test, the populated object has thousands of synsets,
nonzero categories, and more than one thousand tasks; exact counts are not
API guarantees.

**Recovery:** If the populated constructor fails, preserve the exception and
use the missing-data or duplicate-population diagnosis below. To populate an
empty instance, call `populate_knowledgebase(kb, ...)` exactly once. Do not
continue using a half-populated object as if it were valid.

### Duplicate population and `build_knowledgebase`

**Symptom:** An assertion or `ValueError` reports a duplicate synset/category,
for example a category already exists, when calling `build_knowledgebase()` or
calling `populate_knowledgebase` twice.

**Cause:** The `add_*` methods enforce unique keys and population is not
idempotent. In BDDL 3.7.0, `build_knowledgebase()` calls `KnowledgeBase()` with
its default `populate=True` and then calls `populate_knowledgebase` again. The
second population fails on a duplicate record.

**Check:** If the failure follows `build_knowledgebase()` or a second explicit
population call, do not retry it in a loop.

**Recovery:** Prefer one of these two patterns:

```python
# One population through the constructor.
kb = KnowledgeBase(populate=True, verbose=False, load_wordnet=False)

# Or explicit empty container plus one population.
kb = KnowledgeBase(populate=False, verbose=False)
from bddl.knowledge_base.processing import populate_knowledgebase
populate_knowledgebase(kb, verbose=False, load_wordnet=False)
```

If a future BDDL release changes `build_knowledgebase`, verify that release
before changing this guidance. Never use duplicate-population failure as a
reason to regenerate source data.

## Optional WordNet is unavailable

**Symptom:** `load_wordnet=True` raises an NLTK error or attempts a corpus
download; definitions remain empty; or `wn_synset_exists` returns `False` for a
known WordNet synset.

**Cause:** WordNet is optional for the offline taxonomy/KB path. Population
calls `nltk.download("wordnet")` when `load_wordnet=True`, so that mode may
require network access and writable corpus storage. With the NLTK package but
no corpus, `canonicalize` returns its input unchanged and `wn_synset_exists`
returns `False`, which can mask corpus absence.

**Check:** Keep the safe path disabled:

```python
from bddl.object_taxonomy import ObjectTaxonomy
from bddl.knowledge_base import KnowledgeBase

ObjectTaxonomy()
KnowledgeBase(populate=True, verbose=False, load_wordnet=False)
```

For a preinstalled corpus check, use `wn_synset_exists` only if the environment
already has WordNet; do not assume that an attempted download succeeded.

**Recovery:** Continue with `load_wordnet=False`. This supports taxonomy and
populated-KB relationships but does not provide WordNet definitions or custom
synset classification: BDDL 3.7.0 sets `definition=""` and `is_custom=False` in
this mode. Obtain explicit network/storage approval before enabling WordNet.
The bundled CLI never enables it and never downloads data.

## Legacy taxonomy method names

**Symptom:** A taxonomy test or older integration raises `AttributeError` for
`get_class_name_from_igibson_category`, `get_subtree_igibson_categories`,
`is_valid_class`, `get_igibson_categories`, or `get_parent`.

**Cause:** Those legacy names are not methods of the BDDL 3.7.0
`ObjectTaxonomy` implementation even though an older taxonomy test module still
calls them.

**Recovery:** Use the current API and account for changed return shapes:

| Legacy call | BDDL 3.7.0 call |
| --- | --- |
| `get_class_name_from_igibson_category(x)` | `get_synset_from_category(x)` |
| `get_subtree_igibson_categories(s)` | `get_subtree_categories(s)` |
| `is_valid_class(s)` | `is_valid_synset(s)` |
| `get_igibson_categories(s)` | `get_categories(s)` |
| `get_parent(s)` | `get_parents(s)` |

`get_parents` returns a list because the taxonomy is represented as a directed
graph; do not assume a scalar parent. Use the bundled inspector to avoid these
stale names. Treat failures from the legacy test module as API-drift evidence,
not as a reason to alter generated data.

## Invalid taxonomy names or ambiguous category lookup

**Symptom:** `get_categories`, `get_ancestors`, `is_leaf`, or another relation
raises an assertion; a category lookup returns `None`; or a resolver raises
`ValueError: Multiple synsets matched`.

**Cause:** Taxonomy methods validate synsets with assertions. Category and
substance resolvers return `None` for no match and reject ambiguous matches.

**Check:**

```python
name = "candidate.n.01"
if not taxonomy.is_valid_synset(name):
    print("not in this packaged taxonomy")

resolved = taxonomy.get_synset_from_category("candidate_category")
print(resolved)
```

For CLI recovery, run:

```bash
python sub-skills/knowledge-base/scripts/inspect_bddl_taxonomy.py --category candidate_category
python sub-skills/knowledge-base/scripts/inspect_bddl_taxonomy.py --list-synsets --limit 20
```

**Recovery:** Correct spelling, use the exact canonical synset string, or stop
when a resolver returns `None` instead of passing that result to another
method. For an ambiguous category, use the synset names in the `ValueError` and
choose one explicitly with `--synset`; do not mutate the hierarchy. A missing
category is not proof that an object exists in any physical asset inventory.

## Condition utility receives the wrong object

**Symptom:** `get_leaf_conditions` raises for an unexpected item or empty
expression; `get_synsets` fails to split inputs; or a result appears to have
an incorrect type.

**Cause:** The utility module expects parsed BDDL condition nodes, not raw
activity names, strings, simulator objects, or arbitrary nested data. Some
return annotations are stale in this release: `object_used_as_fillable`
returns a `bool`, and `object_used_predicates` returns a `set` of predicate
names.

**Check:** Route raw activity parsing and condition compilation to
[symbolic-tasks](../../symbolic-tasks/SKILL.md), then pass a predicate or
condition tree produced by that workflow. Confirm the input has predicate
leaves with synset-instance names before calling `get_synsets`.

**Recovery:** Parse/compile the activity first, flatten with
`get_leaf_conditions`, and use `all_task_predicates` to inspect predicate
names. Do not make a simulator callback or physical-state claim from these
metadata utilities.

## Accidental maintainer data-generation side effect

**Symptom:** A proposed fix starts `bddl/data_generation/*`, asks for external
spreadsheets/approval data, downloads records, changes generated files, or
leaves a large regeneration job running.

**Cause:** Packaged generated data was confused with the maintainer pipeline.
The KB consumes generated records; it does not own their production.

**Check:** Stop before executing the command. Confirm the requested operation
is only one of: taxonomy construction, read-only package-data presence, an
empty or one-time in-memory KB population, or condition metadata inspection.
Check that no output path, network flag, or source-data input is needed.

**Recovery:** Cancel the generation attempt, preserve existing data, and return
to the packaged-data workflow. Reinstall a complete distribution or report the
missing-data block. `bddl/data_generation` remains outside supported workflows;
never treat generated-file edits as a read-only inspection result.

## Scope boundary

This sub-skill does not diagnose or operate OmniGibson, Isaac Sim, robot
controllers, sensors, GPUs, physical devices, or simulator object states. If a
question asks whether a taxonomy/KB object is physically instantiated or a
predicate is true in a scene, route the symbolic portion to
[symbolic-tasks](../../symbolic-tasks/SKILL.md) and report that simulator
execution is outside the verified CPU BDDL scope.
