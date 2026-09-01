---
name: lexical_taxonomy_schema
description: Build and validate compact WordNet-style synset and semantic-pointer taxonomies for recovery experiments.
---

# Lexical Taxonomy Schema

Use this skill when a task needs a WordNet-style lexical graph with synsets, word senses, and typed semantic pointers. Do not use it as a substitute for the full WordNet database; it is a schema and reduced-fixture builder for mechanism-faithful experiments.

## Inputs
- Synset records with `id`, `lemmas`, `pos`, optional `gloss`, and `relations`.
- Relation records with `type` and `target` synset id.

## Outputs
- Validated taxonomy dictionaries.
- Inventory counts for character strings, synsets, string-sense combinations, and semantic pointers.
- Lemma/POS lookup indexes for downstream tagging.

## Workflow
1. Represent each lexicalized concept as a synset rather than as a single surface word.
2. Preserve many-to-many word-to-sense mappings because the paper distinguishes strings from string-sense combinations.
3. Validate relation endpoints before any tagging or distance computation.
4. Use typed semantic pointers such as hyponym, antonym, meronym, related, or pertains_to.
5. Record inventory counts whenever a recovery claims to reproduce WordNet-like structure.

## Validation
Run `python tests/test_lexical_schema.py` or validate the tree with `validate_skill_tree.py --run-tests`.

## Limitations
The bundled fixture is intentionally tiny. It tests mechanism contracts only and does not contain the original WordNet database.
