# BDDL taxonomy and knowledge-base API

This reference describes the BDDL 3.7.0 package API using package-relative
paths only. Examples are CPU-only and operate on in-memory objects or packaged
data. They do not start a simulator and do not regenerate data.

## Package and generated-data contract

```python
import importlib.metadata
import bddl

assert importlib.metadata.version("bddl") == "3.7.0"
print(bddl.__name__)  # bddl
```

`ObjectTaxonomy` reads the packaged
`bddl/generated_data/output_hierarchy_properties.json` file. Knowledge-base
population also consumes packaged records including:

- `object_inventory.json`, `object_renames.csv`, and `deletion_queue.csv` for
  object/category ownership and metadata links;
- `substance_hyperparams.csv` for particle-system parameters;
- `combined_room_object_list.json` and `allowed_room_types.csv` for scenes and
  room validation;
- packaged activity definitions for task and predicate relationships;
- transition-map JSON records and `complaints.json` for transition and QA
  relationships.

These JSON/CSV schemas are versioned inputs, not stable replacements for the
Python model API. A complete installation must expose them package-relatively.
If they are absent, use [troubleshooting](troubleshooting.md). Do not run
`bddl/data_generation`: it is outside the supported workflow.

A hierarchy node contains `name` and `abilities`, may contain `children`, and
may carry `categories`, `substances`, and `hasModel`. `ObjectTaxonomy` uses the
name, child edges, categories, substances, and abilities; `hasModel` is present
in the generated schema but is not loaded as a taxonomy graph attribute. BDDL
3.7.0 data contains 3,484 taxonomy synsets, but counts are data-version
dependent and must not be treated as API invariants.

## ObjectTaxonomy

Import and construct the taxonomy as follows:

```python
from bddl.object_taxonomy import ObjectTaxonomy

taxonomy = ObjectTaxonomy(hierarchy_type="default")
```

Verified constructor signature:

```text
ObjectTaxonomy(hierarchy_type='default')
```

In BDDL 3.7.0, `hierarchy_type` is accepted but not used to select a file; the
constructor loads the packaged default hierarchy. Treat it as a compatibility
parameter, not evidence of alternate hierarchy support.
`refresh_hierarchy_file()` is a read-only in-memory reload of that same file;
it is not data generation and does not write the hierarchy.

Verified public methods:

```text
refresh_hierarchy_file(self)
get_all_synsets(self)
get_synset_from_category(self, category)
get_synset_from_substance(self, substance)
get_synset_from_category_or_substance(self, category_or_substance)
get_subtree_categories(self, synset)
get_subtree_substances(self, synset)
is_valid_synset(self, synset)
get_descendants(self, synset)
get_leaf_descendants(self, synset)
get_ancestors(self, synset)
is_descendant(self, synset, potential_ancestor_synset)
is_ancestor(self, synset, potential_descendant_synset)
get_abilities(self, synset)
get_categories(self, synset)
get_substances(self, synset)
get_children(self, synset)
get_parents(self, synset)
is_leaf(self, synset)
has_ability(self, synset, ability)
get_required_meta_links_for_abilities(abilities)
get_required_meta_links_for_synset(self, synset)
```

### Safe query pattern

Validate names before calling methods whose implementation uses assertions:

```python
name = "stove.n.01"
if not taxonomy.is_valid_synset(name):
    raise ValueError(f"Unknown taxonomy synset: {name}")

parents = taxonomy.get_parents(name)
children = taxonomy.get_children(name)
ancestors = taxonomy.get_ancestors(name)
descendants = taxonomy.get_descendants(name)
leaf_descendants = taxonomy.get_leaf_descendants(name)
abilities = taxonomy.get_abilities(name)
categories = taxonomy.get_categories(name)
substances = taxonomy.get_substances(name)
required_links = taxonomy.get_required_meta_links_for_synset(name)
```

For a category, substance, or either kind of name, the resolver returns one
synset or `None`; it raises `ValueError` if more than one synset matches:

```python
category_synset = taxonomy.get_synset_from_category("standing_tv")
substance_synset = taxonomy.get_synset_from_substance("water")
any_synset = taxonomy.get_synset_from_category_or_substance("water")

missing = taxonomy.get_synset_from_category("not_a_packaged_category")
assert missing is None
```

Do not pass a missing result into `get_categories`, `get_descendants`, or a
relationship predicate. Explain the miss, suggest checking spelling or using
`get_all_synsets()`, and leave the taxonomy unchanged.

The graph points from parent to child. `get_children` and `get_parents` are
immediate relationships; `get_descendants` and `get_ancestors` exclude the
input node. `get_leaf_descendants` excludes the input even when it is a leaf.
`get_subtree_categories` and `get_subtree_substances` aggregate values from
leaf descendants (or from the input itself when it is a leaf).

`get_abilities` returns a deep copy of the ability mapping. Ability names can
have parameter dictionaries. `has_ability` checks only key presence. The
required-meta-link helper maps selected abilities to metadata-link names; for
example, `openable` requires `joint`, `toggleable` requires `togglebutton`,
`sliceable` requires `subpart`, and ordinary `heatSource`/`coldSource` may
require `heatsource` unless `requires_inside` is true. A `substance` ability
returns no required links.

A valid relation example and a non-mutating recovery for a bad category:

```python
assert taxonomy.is_descendant("stove.n.01", "home_appliance.n.01")
assert taxonomy.is_ancestor("home_appliance.n.01", "stove.n.01")
assert taxonomy.get_synset_from_category("__missing_category__") is None
```

The command-line equivalents are:

```bash
python sub-skills/knowledge-base/scripts/inspect_bddl_taxonomy.py \
  --synset stove.n.01 --parents --children --abilities --required-meta-links
python sub-skills/knowledge-base/scripts/inspect_bddl_taxonomy.py \
  --category standing_tv --ancestors --leaf
python sub-skills/knowledge-base/scripts/inspect_bddl_taxonomy.py \
  --substance water --abilities --substances
python sub-skills/knowledge-base/scripts/inspect_bddl_taxonomy.py \
  --list-categories --limit 20
```

Exactly one selector is required: `--synset`, `--category`, `--substance`,
`--list-synsets`, `--list-categories`, or `--list-substances`. A missing target
or comparison name exits nonzero with the relevant list-mode recovery. Query
flags cannot be combined with list mode, and `--limit` is list-only.

## KnowledgeBase construction and population

Import the container from the public package namespace:

```python
from bddl.knowledge_base import KnowledgeBase
```

Verified constructor and processing signatures:

```text
KnowledgeBase(populate: bool = True, verbose: bool = True, load_wordnet: bool = False)
build_knowledgebase(verbose=True, load_wordnet=False)
populate_knowledgebase(kb: KnowledgeBase, verbose=True, load_wordnet=False)
```

### Empty versus populated

Use an empty container when testing model creation or inspecting the schema
without loading generated data:

```python
empty = KnowledgeBase(populate=False, verbose=False)
assert len(empty.all_synsets()) == 0
assert len(empty.all_categories()) == 0
assert len(empty.all_tasks()) == 0
```

Use the constructor's one-time population path for a generated-data-backed
read-only KB:

```python
kb = KnowledgeBase(
    populate=True,
    verbose=False,
    load_wordnet=False,
)
print(len(kb.all_synsets()), len(kb.all_categories()), len(kb.all_tasks()))
```

With the BDDL 3.7.0 packaged records, a smoke test produced 3,484 synsets,
1,829 categories, 9,589 objects, 1,016 tasks, and 2,818 transition rules. These
counts are observations, not compatibility guarantees. Population is in-memory
and reads packaged records; it is not data regeneration.

If starting from an empty container, populate exactly once:

```python
from bddl.knowledge_base.processing import populate_knowledgebase

kb = KnowledgeBase(populate=False, verbose=False)
populate_knowledgebase(kb, verbose=False, load_wordnet=False)
```

Do not call `populate_knowledgebase` again on the same populated instance:
`add_*` methods reject duplicate keys and the object graph is not designed as
an idempotent refresh operation.

**BDDL 3.7.0 caveat:** `processing.build_knowledgebase()` constructs
`KnowledgeBase()` with its default `populate=True` and then calls
`populate_knowledgebase` on the already populated container. This duplicate
population path fails. Prefer `KnowledgeBase(populate=True, ...)` or the
explicit empty-then-one-populate sequence above. Re-check this behavior before
using the helper with another BDDL release.

`load_wordnet=False` is the safe offline default. With that setting,
`Synset.definition` is empty and every populated `Synset.is_custom` value is
`False`; custom-vs-WordNet classification is not performed.
`load_wordnet=True` calls `nltk.download("wordnet")` during preparation and may
need network and writable corpus storage. Do not enable it merely to inspect
taxonomy abilities.

The bundled inspector supports `--knowledge-base empty` and
`--knowledge-base populated`, always with WordNet disabled, so the two states
can be compared without data generation.

## Public exports and model relationships

`bddl.knowledge_base` re-exports these model classes and helpers:

```text
Property, MetaLink, Predicate, Scene, Category, Object, ParticleSystem,
Synset, TransitionRule, Task, RoomRequirement, RoomSynsetRequirement, Room,
RoomObject, AttachmentPair, SynsetState, KnowledgeBase, ComplaintType,
Complaint, PredicateUsage, CompiledTask, CookingRecipe, MachineRecipe,
MixingRecipe, SubstanceCookingRecipe, WasherRecipe
```

The core graph is:

```text
KnowledgeBase
  ├─ Synset ─ parents/children/ancestors/descendants
  │          ├─ Category ─ objects ─ MetaLink / AttachmentPair / Complaint
  │          ├─ Property
  │          ├─ ParticleSystem ─ particles (Object)
  │          ├─ Task ─ RoomRequirement ─ RoomSynsetRequirement
  │          └─ TransitionRule ─ input/output/machine Synset sets
  ├─ Scene ─ Room ─ RoomObject ─ Object
  └─ PredicateUsage ─ tasks and synsets
```

A `Synset` is the KB-side node, not just a taxonomy string. Its useful derived
properties include `abilities`, `property_names`, `is_substance`, `is_liquid`,
`is_leaf`, `matching_objects`, `matching_ready_objects`,
`matching_particle_systems`, `required_meta_links`, `state`, and transition
relationships. Population links a category to its owning synset and objects,
and a particle system to its substance synset and particles. `Category` and
`ParticleSystem` match their owner synset plus ancestors. Their diagnostic
views report non-leaf or non-substance mappings rather than silently treating
such mappings as valid.

A populated KB can be queried through these verified `KnowledgeBase` methods
(the add methods mutate only the in-memory container and are not needed for
read-only inspection):

```text
get_synset(name), all_synsets()
get_category(name), all_categories()
get_particle_system(name), all_particle_systems()
all_properties()
get_object(name), all_objects()
get_scene(name), all_scenes(), all_rooms()
get_predicate_usage(name), all_predicate_usages()
get_task(name), all_tasks()
get_transition_rule(name), all_transition_rules()
get_meta_link(name), get_attachment_pair(name), all_attachment_pairs()
all_complaint_types(), get_complaint_type(name)
sort_all()
```

`get_*` returns `None` on a missing keyed object, `all_*` returns a shallow list
copy, and `sort_all()` mutates only the ordering of the container's internal
collections. None of these read/query paths writes generated data.

For example:

```python
synset = kb.get_synset("table.n.02")
assert synset is not None
print(synset.parents, synset.children)
print(synset.abilities, synset.required_meta_links)

category = kb.get_category("breakfast_table")
if category is not None:
    print(category.synset.name, len(category.objects))

task = kb.get_task("cleaning_up_after_a_meal-0")
if task is not None:
    print(task.synsets, task.uses_predicates)
```

The dataclass models also expose state/error views such as
`Synset.view_unmatched(kb)`, `Object.view_error_missing_meta_links(kb)`, and
`Task.view_error_missing_object(kb)`. Treat these as diagnostics over a
populated KB, not as proof that a simulator or asset provider is available.
Do not assume every cached property is safe on a partially hand-built object;
relationships such as `Object.owner` require exactly one of `category` or
`particle_system`.

## Condition-to-synset utilities

These helpers in `bddl.knowledge_base.utils` consume already parsed BDDL
condition objects. They are not an activity parser or compiler. Route raw
activity names, definitions, domain parsing, condition construction, and
predicate evaluation to [symbolic-tasks](../../symbolic-tasks/SKILL.md) first.

Verified signatures:

```text
canonicalize(s)
wn_synset_exists(synset)
get_initial_and_goal_conditions(conds) -> Tuple[List, List]
get_leaf_conditions(cond) -> List
get_synsets(cond)
object_substance_match(cond, synset) -> Tuple[bool, bool]
object_used_as_fillable(cond, synset) -> Tuple[bool, bool]  # actual result is bool
object_used_predicates(cond, synset) -> Tuple[bool, bool]  # actual result is set[str]
all_task_predicates(cond) -> Set[str]
leaf_inroom_conds(raw_cond, synsets: Set[str]) -> List[Tuple[str, str]]
```

Interpret the two booleans from `object_substance_match` in this order:
`(used_as_non_substance, used_as_substance)`. `object_used_as_fillable` returns
a boolean despite its stale tuple annotation. `object_used_predicates` returns
a set of predicate names despite its stale tuple annotation. `get_leaf_conditions`
flattens lists and logic expressions to predicate leaves and raises on an empty
or unexpected tree. `get_synsets` is intended for a predicate leaf whose input
names follow BDDL synset-instance naming; it strips the instance suffix and
validates the canonical-looking form.

`canonicalize` and `wn_synset_exists` import NLTK WordNet lazily. If the NLTK
package exists but its WordNet corpus is unavailable, `canonicalize` returns
the input unchanged and `wn_synset_exists` returns `False`; neither result can
then distinguish a custom synset from a missing corpus. They are optional
validation helpers, not prerequisites for offline taxonomy queries or
`KnowledgeBase(..., load_wordnet=False)`.

A generic analysis pattern is:

```python
from bddl.knowledge_base import utils

initial, goal = utils.get_initial_and_goal_conditions(parsed_conditions)
all_conditions = initial + goal
for cond in all_conditions:
    for leaf in utils.get_leaf_conditions(cond):
        names = utils.get_synsets(leaf)
        print(names, leaf.STATE_NAME)

print(utils.all_task_predicates(all_conditions))
print(utils.object_substance_match(all_conditions, "water.n.06"))
print(utils.object_used_as_fillable(all_conditions, "bowl.n.01"))
print(utils.object_used_predicates(all_conditions, "bowl.n.01"))
```

Do not pass raw strings, raw parsed lists with the wrong shape, or simulator
objects where these helpers expect BDDL condition nodes. A utility result is
metadata for reasoning about a task; it does not instantiate objects or check
physical state.

## Maintainer-only generation boundary

The packaged hierarchy, inventories, room lists, annotations, transition
records, and complaints are runtime inputs. `bddl/data_generation` is a
maintainer pipeline that may depend on external sources, approval state, or
expensive processing. It is not a supported workflow for this sub-skill and
must not be run to repair an import, answer a taxonomy query, or populate a KB.
