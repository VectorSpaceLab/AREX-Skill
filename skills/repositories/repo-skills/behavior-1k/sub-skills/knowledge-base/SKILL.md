---
name: knowledge-base
description: "Guide CPU-only inspection of BDDL object taxonomy and
  generated-data-backed knowledge bases, including model relationships,
  abilities, safe construction, taxonomy queries, and condition-to-synset
  utilities."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NO_LICENSE
---

# BDDL Knowledge Base

Use this sub-skill for requests about BDDL taxonomy, object categories or
synsets, substances, abilities/properties, generated knowledge-base records,
`KnowledgeBase`, or which objects and predicates occur in parsed conditions.
The verified API and data contract is BDDL 3.7.0.

## Route

1. Read [the API reference](references/api-reference.md) before using a
   taxonomy or knowledge-base API. Confirm that BDDL 3.7.0 and its packaged
   generated runtime data are available.
2. For a category, substance, or synset query, prefer the bundled read-only
   [taxonomy inspector](scripts/inspect_bddl_taxonomy.py). From the generated
   skill root, run it as `python sub-skills/knowledge-base/scripts/inspect_bddl_taxonomy.py`;
   it validates names,
   supports explicit relationship/ability queries, and never regenerates data.
3. Choose knowledge-base state deliberately:
   - `--knowledge-base none` performs only taxonomy inspection.
   - `--knowledge-base empty` constructs an empty model container.
   - `--knowledge-base populated` reads packaged records once, in memory, with
     WordNet disabled.
4. In Python, use `KnowledgeBase(populate=False)` for an empty container or
   `KnowledgeBase(populate=True, load_wordnet=False)` for one-time population.
   In BDDL 3.7.0, avoid `build_knowledgebase()` because it attempts population
   twice; see the exact contract and safe alternatives in the API reference.
5. Follow model relationships from `Synset` to categories, properties, objects,
   particle systems, tasks, scenes, and transition rules. Treat generated
   JSON/CSV files as versioned inputs, not as a stable substitute for the model
   API.
6. When starting from an activity name, raw problem, or condition tree that
   still needs parsing, compilation, grounding, or evaluation, route first to
   [symbolic-tasks](../symbolic-tasks/SKILL.md). Return here only for taxonomy,
   generated-record, model-relationship, or parsed-condition metadata work.
7. Use [troubleshooting](references/troubleshooting.md) for package-data,
   duplicate-population, WordNet, invalid-name, stale-method, or input-shape
   failures.

## Boundaries

- Supported work is read-only taxonomy inspection, empty or one-time in-memory
  KB population, model traversal, and metadata analysis on CPU.
- `bddl/data_generation` is a maintainer pipeline and is not a supported
  runtime workflow. Do not run it to answer queries or repair missing packaged
  data.
- OmniGibson, Isaac Sim, simulators, robot or sensor APIs, GPU execution,
  physical hardware, and physical object-state checks are outside this
  sub-skill. Taxonomy or KB membership does not prove physical availability or
  scene state.
