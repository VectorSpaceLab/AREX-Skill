---
name: episodic_memory_store
description: Maintain frozen-key episodic memory with random write, random replay sampling, and Euclidean KNN retrieval.
---

# Episodic Memory Store

## When To Use
Use this skill when reconstructing the episodic-memory lifelong language learning method from de Masson d'Autume et al. without relying on an original implementation repository.

## Inputs
- Small text examples represented as dictionaries.
- Deterministic configuration values such as memory probability, replay interval, K, and adaptation steps.

## Outputs
- Auditable Python objects or JSON-serializable dictionaries matching the module contract.
- Logs that expose mechanism execution rather than only final metrics.

## Workflow
1. Encode keys with a fixed deterministic encoder.
2. Write examples probabilistically to control memory capacity.
3. Use random samples for replay and nearest neighbors for local adaptation.

## Validation
Run `python tests/test_episodic_memory_store.py` from this skill directory.

## Limitations
The scripts are deterministic proxy utilities for bounded recovery. They do not train BERT or reproduce the full paper-scale datasets.
