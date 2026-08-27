---
name: graph-data
description: "Construct, batch, split, mask, validate, and troubleshoot
  TorchDrug graph, molecule, protein, and dataset data objects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TorchDrug Graph Data

Use this sub-skill when the task is about TorchDrug data objects rather than model layers, training loops, or domain-specific task recipes.

## Read First

- For constructors, attribute contexts, batching, masking, split helpers, and dataset loading patterns, read [references/data-objects.md](references/data-objects.md).
- For common failures around RDKit input, attribute lengths, device movement, dataset downloads, split lengths, and lazy loading, read [references/troubleshooting.md](references/troubleshooting.md).
- For a no-network sanity check that creates tiny in-memory graphs and molecules, run `python scripts/smoke_graph_data.py` from this sub-skill directory. Add `--skip-rdkit` when RDKit or molecule parsing is unavailable.

## Use This For

- Creating `data.Graph`, `data.Molecule`, `data.Protein`, and their packed variants from in-memory edge lists, SMILES strings, or protein sequences.
- Adding node, edge, graph, atom, bond, molecule, or residue attributes with the right context managers.
- Batching samples with `Graph.pack`, `PackedMolecule.from_smiles`, `PackedProtein.from_sequence`, `data.graph_collate`, or `data.DataLoader`.
- Applying `subgraph`, `node_mask`, `edge_mask`, `graph_mask`, `subbatch`, `compact`, `unpack`, and dataset split helpers.
- Loading TorchDrug datasets or building small local `MoleculeDataset` / `ProteinDataset` objects with transform and lazy-loading options.

## Route Elsewhere

- Use `layers-and-extensions` for graph neural network layers, graph construction modules, and extension compilation.
- Use `training-engine` for `core.Engine`, optimizers, training/evaluation loops, checkpoint save/load, and `Configurable` workflows.
- Use `molecular-workflows` for molecule property prediction, generation, reaction, or chemistry task recipes built on these data objects.
- Use `protein-workflows` for protein prediction, sequence/structure recipes, and protein-specific task pipelines.
- Use `knowledge-graphs` for knowledge graph datasets, entity/relation indexing, and KG tasks.
