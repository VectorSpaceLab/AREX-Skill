---
name: descriptors-fingerprints
description: "Calculate RDKit molecular descriptors, fingerprints, bit-vector
  similarities, clustering inputs, and ML-ready feature tables."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# RDKit Descriptors and Fingerprints

Use this sub-skill when a request involves molecular properties, feature engineering, fingerprint generation, similarity search, bit vectors, distance matrices, or Butina clustering.

## Route Here

- Calculate scalar descriptors with `rdkit.Chem.Descriptors`, `rdkit.Chem.rdMolDescriptors`, `rdkit.Chem.Lipinski`, `rdkit.Chem.Crippen`, `rdkit.Chem.MolSurf`, or `rdkit.Chem.QED`.
- Build feature dictionaries or pandas-ready rows from molecules and descriptor functions.
- Generate Morgan, RDKit, atom-pair, or topological-torsion fingerprints with `rdkit.Chem.rdFingerprintGenerator`.
- Compare fingerprints with `rdkit.DataStructs` metrics such as Tanimoto, Dice, cosine, and bulk similarity helpers.
- Convert similarities to distances for nearest-neighbor search, clustering, or ML inputs.
- Cluster molecules with `rdkit.ML.Cluster.Butina.ClusterData` from condensed distance lists or feature vectors.

## Route Elsewhere

- Use `../molecule-io-core/` for SMILES/SDF parsing, sanitization, molecule validation, and canonicalization before descriptor work.
- Use `../conformers-drawing/` for 3D conformer generation, shape descriptors, alignment, RMSD, or drawing similarity maps.
- Use `../contrib-utilities/` for optional contributed scorers such as SA Score, NP Score, Fraggle, MMPA, or NIBR filters.
- Use `../data-cli-integration/` for RDKit data-file locations, feature-definition files, database helpers, or non-feature-engineering pandas integration.

## Start With These References

- `references/descriptors.md` for descriptor families, drug-like properties, and feature-table recipes.
- `references/fingerprints-and-similarity.md` for fingerprint generator APIs, vector types, similarity, top-k search, and Butina clustering.
- `references/troubleshooting.md` for deprecated Morgan helpers, invalid molecules, vector mismatches, sparse/count/vector issues, and pandas export pitfalls.
- `scripts/fingerprint_similarity.py` for a small, self-contained CLI that parses SMILES, builds Morgan generator fingerprints, and reports Tanimoto similarities while surfacing invalid inputs.

## Common Patterns

- Prefer the current generator API: `rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048).GetFingerprint(mol)`.
- Use `Descriptors.CalcMolDescriptors(mol)` when a broad scalar descriptor dictionary is more useful than calling individual descriptor functions.
- Use `rdMolDescriptors.CalcExactMolWt(mol)`, `Crippen.MolLogP(mol)`, `MolSurf.TPSA(mol)`, `Lipinski.NumHDonors(mol)`, and `QED.qed(mol)` for focused medicinal-chemistry properties.
- Check every parsed molecule for `None` before descriptor or fingerprint calculation; most downstream APIs expect a valid `Chem.Mol`.
- For Butina from fingerprint similarities, pass distances as `1.0 - similarity` in condensed lower-triangle order with `isDistData=True`.

## Quick Smoke

Run the bundled helper on a few molecules:

```bash
python scripts/fingerprint_similarity.py --smiles "CCO" "CCCO" "c1ccccc1" --top-k 2
```

For a query-vs-library search:

```bash
python scripts/fingerprint_similarity.py --query "CCO" --smiles "CCO" "CCN" "c1ccccc1" --top-k 3
```
