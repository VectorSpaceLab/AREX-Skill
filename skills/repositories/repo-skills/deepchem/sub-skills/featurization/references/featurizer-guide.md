# Featurizer Selection Guide

This guide helps choose DeepChem featurizers by raw input, downstream model family, and validation needs. Keep featurization decisions separate from dataset loading and model training: choose the feature representation here, then use the data/model sub-skills for loaders, splitters, and estimators.

## Molecule SMILES or RDKit Mol

| Need | Prefer | Output | Notes |
|---|---|---|---|
| Fast baseline for classical ML | `dc.feat.CircularFingerprint` | dense vector `(size,)` by default | Good first choice for random forests, logistic regression, MLPs, and similarity-style baselines. |
| Count-aware ECFP | `CircularFingerprint(is_counts_based=True)` | dense count vector `(size,)` | Values can exceed 1; useful when counts matter more than binary presence. |
| Sparse fragment inventory | `CircularFingerprint(sparse=True, smiles=True)` | dict per molecule | Useful for fragment inspection, not a fixed numeric matrix unless converted. |
| Interpretable 2D descriptors | `dc.feat.RDKitDescriptors` | dense vector length `len(featurizer.reqd_properties)` | Can disable fragment or BCUT2D descriptors; normalized mode removes descriptors without normalization parameters. |
| High-dimensional descriptors | `dc.feat.MordredDescriptors` | dense vector, commonly 1613 or 1826 | Requires optional `mordred`; missing descriptor values are converted to zero. |
| PubChem structural keys | `dc.feat.PubChemFingerprint` | vector `(881,)` | Requires optional `pubchempy` and network access to PubChem. |
| Graph neural networks | `dc.feat.MolGraphConvFeaturizer` | `dc.feat.GraphData` per molecule | Use for graph models expecting node/edge topology rather than dense vector fingerprints. |
| Legacy Keras graph conv models | `dc.feat.ConvMolFeaturizer`, `dc.feat.WeaveFeaturizer` | `ConvMol` or weave arrays | Prefer only when the target model specifically expects these legacy representations. |
| Coordinate/electronic representation | `dc.feat.CoulombMatrix`, `dc.feat.CoulombMatrixEig` | padded matrices/eigenvalues | Requires a sensible `max_atoms`; may embed conformers if none are present. |
| SMILES as sequence/image | `OneHotFeaturizer`, `SmilesToSeq`, `SmilesToImage`, tokenizers | arrays or tokenizer outputs | Use for sequence/CNN/tokenizer models; validate vocabulary and padding behavior first. |

### ECFP vs Graph Featurization

Choose `CircularFingerprint` when the user wants a fixed-size numeric matrix, quick baselines, classical ML, or compatibility with generic tabular estimators. Choose `MolGraphConvFeaturizer` when the downstream model consumes molecular graph topology and can handle a `GraphData` object per molecule.

For chirality-sensitive tasks, consider both representation and settings:

- `CircularFingerprint(chiral=True)` includes chirality in Morgan fingerprints.
- `MolGraphConvFeaturizer(use_chirality=True)` expands node features from 30 to 32 by adding chirality one-hot fields.
- Always verify that stereochemical SMILES differ as intended; a non-chiral setting may produce identical or less informative features for enantiomers.

## GraphData Outputs

`MolGraphConvFeaturizer` returns one `GraphData` object per successful molecule:

- `node_features`: shape `[num_atoms, num_node_features]`.
- `edge_index`: shape `[2, num_edges]`, using directed edges for molecular bonds.
- `edge_features`: `None` unless `use_edges=True`; when enabled, shape `[num_edges, 11]`.
- Default node features have length 30; `use_chirality=True` gives 32; `use_partial_charge=True` gives 31; enabling both adds both sets.

A graph for a molecule with `B` bonds commonly has `2 * B` directed edges. Validate that graph counts match expectations before batching.

## Sequences and Bioinformatics

Use `dc.feat.FASTAFeaturizer()` when the input is a FASTA file path and the task needs sequence names and raw sequences. It returns one array per FASTA file, with rows like `[name, sequence]` and shape `(num_sequences, 2)` inside each file-level feature.

Use tokenizer-style featurizers only when the user explicitly wants tokenized sequences or SMILES and the tokenizer dependencies/model files are available. `HuggingFaceFeaturizer` wraps a provided Hugging Face tokenizer and returns tokenizer data dictionaries per datapoint.

## Materials

Pick material featurizers by input representation:

- Composition strings such as `"MoS2"`: `ElementPropertyFingerprint` or `ElemNetFeaturizer`.
- Periodic structures as pymatgen `Structure` objects or compatible dicts: `SineCoulombMatrix`, `CGCNNFeaturizer`, and related structure featurizers.
- `CGCNNFeaturizer` returns `GraphData` with crystal nodes and neighbor-distance edge features.
- Many material featurizers require optional packages such as `pymatgen` and `matminer`.

## Polymers

Use polymer featurizers when the raw datapoint is a polymer string representation such as BigSMILES or a weighted directed graph representation accepted by the specific featurizer. The base `PolymerFeaturizer` validates batched inputs and appends empty arrays for invalid datapoints. Keep polymer conversion and vocabulary building scoped to feature preparation.

## Complexes and Structures

Complex featurizers operate on ligand/protein file pairs and produce contact, grid, voxel, atomic coordinate, or interaction fingerprints. Use them when the user already has structures and wants features. Route full docking, pose generation, and structure preparation workflows to the docking/structure skill.

## Vocabulary Builders

Vocabulary builders are user-facing when a featurizer/tokenizer needs a learned vocabulary or token set. Use them to build or inspect vocabularies for tokenizer-style featurizers, then keep the same vocabulary fixed across splits and inference. Do not rebuild vocabularies independently for train and test data.

## Practical Selection Flow

1. Identify raw input: SMILES/Mol, FASTA, composition, structure, polymer string, or complex file pair.
2. Identify model family: fixed-vector/tabular, graph neural network, sequence/tokenizer, material graph, or complex/grid model.
3. Pick the smallest featurizer that satisfies the model: ECFP or RDKit descriptors before expensive optional descriptors; graph featurizers only for graph models.
4. Run a two-to-five item smoke batch and inspect output type, shape, failure entries, and dependency warnings.
5. Lock settings and reuse the same featurizer configuration for all splits and inference.
