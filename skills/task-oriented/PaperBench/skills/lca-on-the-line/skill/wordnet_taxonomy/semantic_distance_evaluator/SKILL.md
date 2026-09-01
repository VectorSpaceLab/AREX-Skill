---
name: semantic_distance_evaluator
description: Estimate WordNet-style semantic distance by traversing typed semantic-pointer graphs.
---

# Semantic Distance Evaluator

Use this skill when a task needs the semantic-distance mechanism described as a planned WordNet use. It operates on taxonomy dictionaries with synsets and semantic pointers.

## Inputs
- A taxonomy with synset ids and relation endpoints.
- Synset-id pairs and a near/far threshold.

## Outputs
- Shortest path distance, synset path, relation-label trace, and near/far classification.

## Workflow
1. Convert semantic pointers into a traversal graph while preserving relation labels.
2. Use breadth-first search for shortest concept distance.
3. Return no finite distance for disconnected concepts.
4. Classify pairs with a configured or learned threshold.
5. Log distances and classifications when used as recovery evidence.

## Validation
Run `python tests/test_semantic_distance.py` or validate the skill tree with tests enabled.

## Limitations
Directional pointers are traversed bidirectionally for distance estimation in the reduced proxy while labels remain visible in the path trace.
