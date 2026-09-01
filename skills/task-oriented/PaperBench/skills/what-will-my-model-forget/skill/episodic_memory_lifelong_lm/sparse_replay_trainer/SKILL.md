---
name: sparse_replay_trainer
description: Train an online text classifier with sparse replay updates from episodic memory.
---

# Sparse Replay Trainer

## When To Use
Use this skill when reconstructing the episodic-memory lifelong language learning method from de Masson d'Autume et al. without relying on an original implementation repository.

## Inputs
- Small text examples represented as dictionaries.
- Deterministic configuration values such as memory probability, replay interval, K, and adaptation steps.

## Outputs
- Auditable Python objects or JSON-serializable dictionaries matching the module contract.
- Logs that expose mechanism execution rather than only final metrics.

## Workflow
1. Update the base model once per stream example.
2. At configured intervals, sample from memory and perform replay updates.
3. Record replay events with step, sample count, and losses.

## Validation
Run `python tests/test_sparse_replay_trainer.py` from this skill directory.

## Limitations
The scripts are deterministic proxy utilities for bounded recovery. They do not train BERT or reproduce the full paper-scale datasets.
