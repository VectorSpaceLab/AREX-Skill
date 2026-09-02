---
name: local_adaptation_predictor
description: Retrieve memory neighbors and adapt temporary parameters for a single prediction while preserving base parameters.
---

# Local Adaptation Predictor

## When To Use
Use this skill when reconstructing the episodic-memory lifelong language learning method from de Masson d'Autume et al. without relying on an original implementation repository.

## Inputs
- Small text examples represented as dictionaries.
- Deterministic configuration values such as memory probability, replay interval, K, and adaptation steps.

## Outputs
- Auditable Python objects or JSON-serializable dictionaries matching the module contract.
- Logs that expose mechanism execution rather than only final metrics.

## Workflow
1. Retrieve K nearest memory values using the memory skill.
2. Copy base parameters and optimize local parameters against retrieved labels plus anchor.
3. Predict with local parameters and confirm base parameters were not mutated.

## Validation
Run `python tests/test_local_adaptation_predictor.py` from this skill directory.

## Limitations
The scripts are deterministic proxy utilities for bounded recovery. They do not train BERT or reproduce the full paper-scale datasets.
