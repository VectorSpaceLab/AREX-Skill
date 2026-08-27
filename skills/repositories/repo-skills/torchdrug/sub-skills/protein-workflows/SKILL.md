---
name: protein-workflows
description: "Plan TorchDrug protein sequence, structure, contact prediction,
  function/property, ESM, GearNet, and protein-protein interaction workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Protein Workflows

Use this sub-skill when a user needs TorchDrug/TorchProtein guidance for protein data, residue or atom views, sequence/structure encoders, contact prediction, protein function/property prediction, ESM embeddings, or protein-protein interaction tasks.

## Read First

- For protein object creation, dataset families, feature choices, representation model selection, graph construction, and ESM caveats, read [references/protein-data-and-models.md](references/protein-data-and-models.md).
- For end-to-end contact, protein property/function, and interaction/PPI affinity recipes, read [references/task-workflows.md](references/task-workflows.md).
- For failures around downloads, sequence/PDB parsing, feature dimensions, truncation, ESM caches, memory, and contact labels, read [references/troubleshooting.md](references/troubleshooting.md).
- For an offline planning checklist, run `python scripts/plan_protein_workflow.py --workflow contact`, `property`, or `interaction` from this sub-skill directory.

## Use This For

- Creating `data.Protein` / `data.PackedProtein` from sequences or PDB-derived structures.
- Choosing between `ProteinCNN`, `ProteinResNet`, `ProteinLSTM`, `ProteinBERT`, `GearNet`, `ESM`, and `Physicochemical` protein encoders.
- Planning `ProteinNet` contact prediction with `tasks.ContactPrediction` and residue coordinates/masks.
- Planning protein property, function, localization, stability, fluorescence, beta-lactamase, enzyme commission, or AlphaFoldDB workflows.
- Planning `HumanPPI`, `YeastPPI`, or `PPIAffinity` workflows with `tasks.InteractionPrediction`.

## Route Elsewhere

- Use `../graph-data/SKILL.md` for generic graph packing, masking, dataset containers, collators, and raw `Graph` mechanics.
- Use `../layers-and-extensions/SKILL.md` for custom graph construction layers, new edge functions, compiled extension issues, or deep layer internals.
- Use `../training-engine/SKILL.md` for `core.Engine`, optimizer/scheduler wiring, checkpoint save/load, config round-trips, logging, CPU/GPU selection, and distributed training.
- Use `../molecular-workflows/SKILL.md` for small-molecule, reaction, generation, retrosynthesis, or ligand-property workflows.
- Use `../knowledge-graphs/SKILL.md` for entity/relation triple reasoning and knowledge graph completion.
