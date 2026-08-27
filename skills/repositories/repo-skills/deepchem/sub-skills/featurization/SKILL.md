---
name: featurization
description: "Choose, run, validate, and troubleshoot DeepChem featurizers for
  molecules, graphs, descriptors, sequences, materials, polymers, and
  complexes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DeepChem Featurization

Use this sub-skill when the user needs to select or debug `deepchem.feat` transformations before loading data into models. Route dataset loading, MolNet presets, splitting, and CSV/SDF loader mechanics to `../data-and-molnet/`; route model construction/training to `../model-training/`; route full docking pose generation to `../docking-and-structure/`.

## Quick Router

- Use `CircularFingerprint` for fixed-size ECFP/Morgan bit vectors or count vectors for classical ML, similarity, and quick baselines.
- Use `RDKitDescriptors` for interpretable 2D physicochemical descriptors; use `MordredDescriptors` only when the optional Mordred package is available and high-dimensional descriptors are desired.
- Use `MolGraphConvFeaturizer` for graph neural network inputs as `GraphData`; set `use_edges=True` when the downstream model consumes edge attributes and `use_chirality=True` when stereochemistry matters.
- Use `CoulombMatrix` or `CoulombMatrixEig` for coordinate-aware molecular representations where `max_atoms` and conformer handling are explicit.
- Use `FASTAFeaturizer` for FASTA files and biosequence extraction; use tokenizer wrappers such as `HuggingFaceFeaturizer` only when transformer tokenizers are installed and intentionally selected.
- Use material featurizers such as `ElementPropertyFingerprint`, `SineCoulombMatrix`, `CGCNNFeaturizer`, and `ElemNetFeaturizer` for composition strings or pymatgen structures.
- Use polymer, complex, and docking-adjacent featurizers only for feature extraction; route pose generation and docking workflows elsewhere.

## Minimal Patterns

```python
import deepchem as dc

smiles = ["CCO", "c1ccccc1"]
features = dc.feat.CircularFingerprint(size=1024).featurize(smiles)
print(features.shape)  # (2, 1024)
```

```python
graphs = dc.feat.MolGraphConvFeaturizer(use_edges=True).featurize(["CCO"])
graph = graphs[0]
print(graph.node_features.shape, graph.edge_index.shape, graph.edge_features.shape)
```

```python
descriptors = dc.feat.RDKitDescriptors(use_bcut2d=False).featurize(["CCO"])
print(descriptors.shape)
```

For mixed-validity batches, always inspect per-entry outputs before passing features to a model. Failed molecular featurizations usually appear as empty arrays, and heterogeneous feature shapes can force an object array.

## Validation Checklist

1. Confirm input type: SMILES/RDKit Mol for molecular featurizers, FASTA file path for `FASTAFeaturizer`, pymatgen structure or structure dict for structure featurizers, composition string for composition featurizers.
2. Print `type(feature)` and shape-like attributes for a tiny batch before scaling up.
3. Check failures: empty arrays, warnings about failed datapoints, missing optional dependency warnings, or object arrays from heterogeneous outputs.
4. Match feature family to model family: vectors for scikit-learn/dense models, `GraphData` for graph models, sequence/tokenizer outputs for sequence models, structure/composition features for materials models.
5. Keep featurizer settings identical between train/validation/test/inference.

## Bundled References

- `references/featurizer-guide.md`: selection guidance by input, task, and model family.
- `references/api-reference.md`: common signatures, output contracts, and validation snippets.
- `references/troubleshooting.md`: failure modes for invalid SMILES, optional dependencies, graph shape mismatches, Coulomb `max_atoms`, and descriptor normalization.
- `scripts/inspect_featurizer_outputs.py`: tiny CLI to inspect SMILES and optional FASTA outputs without needing dataset loaders.

## Helper Script

Run the bundled helper from this sub-skill directory or by path:

```bash
python scripts/inspect_featurizer_outputs.py --smiles CCO 'C[C@H](O)Cl' bad_smiles --featurizers circular molgraph rdkit
```

Add `--fasta path/to/file.fasta --featurizers fasta` to inspect FASTA extraction when the sequence dependency is installed.
