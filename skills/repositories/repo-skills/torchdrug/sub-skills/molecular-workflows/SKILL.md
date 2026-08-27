---
name: molecular-workflows
description: "Plan TorchDrug molecular property prediction, molecular
  pretraining and finetuning, molecule generation, and retrosynthesis
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Molecular Workflows

Use this sub-skill when a user needs to build or debug a TorchDrug workflow for small molecules or chemical reactions.

## When To Use

- Build property prediction pipelines for molecule datasets such as `ClinTox`, `BACE`, or custom SMILES/label datasets.
- Plan molecular self-supervised pretraining with `InfoGraph`, `AttributeMasking`, or related pretraining tasks, then finetune with `PropertyPrediction`.
- Set up ZINC250k molecule generation with `GCPNGeneration` or GraphAF-style `AutoregressiveGeneration`, including PPO finetuning for QED or penalized logP.
- Set up USPTO50k retrosynthesis with G2Gs: center identification, synthon completion, and the combined `Retrosynthesis` beam-search pipeline.
- Interpret molecular metrics, generated SMILES, beam-search candidates, and common chemistry-specific failures.

## Route Elsewhere

- Raw `data.Graph`, `data.Molecule`, packed batches, masks, collators, and custom data object construction belong in the `graph-data` sub-skill.
- GNN layer internals, custom model/layer design, compiled extensions, and representation output shapes belong in the `layers-and-extensions` sub-skill.
- Generic `core.Engine` checkpointing, save/load, logging, scheduler, distributed settings, and config serialization belong in the `training-engine` sub-skill.
- Protein structure, protein function, residue, sequence, and contact workflows belong in the `protein-workflows` sub-skill.
- Knowledge graph reasoning and entity/relation ranking workflows belong in the `knowledge-graphs` sub-skill.

## References

- [Property and pretraining](references/property-and-pretraining.md) covers ClinTox/BACE property prediction, custom molecule datasets, split choices, feature compatibility, `GIN`, `InfoGraph`, `AttributeMasking`, and finetuning.
- [Generation and retrosynthesis](references/generation-and-retrosynthesis.md) covers ZINC250k GCPN/GraphAF setup, PPO objective caveats, USPTO50k reaction/synthon modes, G2Gs training, and beam-search output interpretation.
- [Troubleshooting](references/troubleshooting.md) covers dataset downloads, RDKit and invalid SMILES, feature mismatches, criterion/metric choices, generation validity and resampling, retrosynthesis split seeds, and compute expectations.

## Safe Planner

Run `python scripts/plan_molecular_workflow.py --workflow property`, `pretrain`, `generation`, or `retrosynthesis` from this sub-skill directory to print a no-download, no-training checklist and minimal API skeleton.
