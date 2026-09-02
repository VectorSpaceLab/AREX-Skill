---
name: benchmark_property_taxonomy
description: Classify offline RL datasets by D4RL challenge properties and explain benchmark implications from metadata.
---

# Benchmark Property Taxonomy

Use this skill when interpreting a D4RL-style dataset or selecting a reduced recovery target. It maps dataset metadata and variant names to challenge properties such as sparse rewards, mixed-quality data, narrow demonstrations, or undirected trajectories.

## Inputs

- A metadata dictionary or JSON file containing `domain`, `variant`, `reward_type`, `behavior_source`, and optional descriptive fields.
- Dataset names may be full environment names such as `hopper-medium-expert-v2` or separated domain/variant fields.

## Outputs

- `tags`: D4RL challenge tags.
- `explanations`: short reasons for each tag.
- `warnings`: missing-metadata notes.

## Workflow

1. Normalize names to lowercase.
2. Infer variant rules for common D4RL names: random, medium, medium-replay, medium-expert, expert, cloned, human, partial, mixed, diverse, and play.
3. Add domain-specific tags for Maze2D, AntMaze, Adroit, and Kitchen when supported by metadata.
4. Return warnings instead of overclaiming when metadata is insufficient.
5. Use tags to guide recovery interpretation, not as a replacement for executable experiments.

## Validation

Run `python scripts/classify_dataset.py --metadata-json <file>`. Tests cover representative D4RL-style metadata cases and missing metadata warnings.

## Limitations

The classifier is rule-based and paper-derived. It does not download benchmark files or measure actual policy performance.
