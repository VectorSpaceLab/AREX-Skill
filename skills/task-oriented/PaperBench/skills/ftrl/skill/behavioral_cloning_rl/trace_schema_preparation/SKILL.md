---
name: trace_schema_preparation
description: Prepare fixed-rate behavioral cloning trace examples for GRAIL-style reduced recovery experiments.
---

# trace_schema_preparation

Use this skill when recovering Bain and Sammut style behavioural cloning without the original simulator repository. It is not a general reinforcement-learning skill; it targets trace-driven reactive cloning with explicit GRAIL-style separation.

## Inputs
- JSON-compatible trace examples or prepared examples, depending on the script.
- Current-attempt artifacts only; do not read any original source repository.

## Outputs
- Deterministic JSON-compatible structures that can be consumed by downstream recovery modules.

## Workflow
1. Validate required process variables.
2. Derive goal-elevation and elevator-action labels.
3. Preserve provenance and avoid adding downstream predictions.

## Validation
Run `python scripts/trace_schema_preparation.py --help` where applicable and run the tests through the Distiller skill-tree validator with `--run-tests`.

## Limitations
The scripts implement a reduced proxy for the paper mechanism. They validate trace preparation, GRAIL separation, compactness, and reactive action prediction; they do not recreate the unavailable flight simulator.
