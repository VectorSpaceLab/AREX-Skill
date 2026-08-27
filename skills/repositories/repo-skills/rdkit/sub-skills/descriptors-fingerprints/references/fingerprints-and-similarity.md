# Fingerprints, Similarity, and Clustering

Use this reference for current RDKit fingerprint generator APIs, `DataStructs` similarity metrics, top-k similarity search, and Butina clustering inputs.

## Prefer Fingerprint Generators

RDKit exposes modern fingerprint generators in `rdkit.Chem.rdFingerprintGenerator`. Prefer these over legacy Morgan helper calls in new code.

```python
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator

mol = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
fingerprint = generator.GetFingerprint(mol)
```

Common generators:

```python
morgan = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
rdkit_fp = rdFingerprintGenerator.GetRDKitFPGenerator(fpSize=2048)
atom_pair = rdFingerprintGenerator.GetAtomPairGenerator(fpSize=2048)
torsion = rdFingerprintGenerator.GetTopologicalTorsionGenerator(fpSize=2048)
```

Useful generator methods:

- `GetFingerprint(mol)`: explicit bit vector suitable for most Tanimoto searches.
- `GetCountFingerprint(mol)`: count vector when repeated features matter.
- `GetSparseFingerprint(mol)`: sparse bit vector for very large/unfolded spaces.
- `GetSparseCountFingerprint(mol)`: sparse count vector for count-aware workflows.
- `GetFingerprints(mols, numThreads=...)`: batch fingerprints when available for the generator and RDKit build.

## Morgan Migration Pattern

Legacy code often uses deprecated or warning-prone helpers such as:

```python
from rdkit.Chem import AllChem
fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
```

Migrate to:

```python
from rdkit.Chem import rdFingerprintGenerator
morgan = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
fp = morgan.GetFingerprint(mol)
```

Parameter mapping:

- `radius` stays `radius`.
- `nBits` becomes `fpSize` for fixed-length bit fingerprints.
- `useChirality` usually maps to `includeChirality`.
- Count fingerprints should use `GetCountFingerprint` or sparse count fingerprints instead of bit vectors.
- If old code used `bitInfo`, use `rdFingerprintGenerator.AdditionalOutput()` and enable the needed collection methods before fingerprinting.

## Similarity Metrics

`rdkit.DataStructs` provides bit-vector and count-vector similarity functions:

```python
similarity = DataStructs.TanimotoSimilarity(fp_a, fp_b)
dice = DataStructs.DiceSimilarity(fp_a, fp_b)
cosine = DataStructs.CosineSimilarity(fp_a, fp_b)
```

For one query against many library fingerprints, use bulk helpers where available:

```python
scores = DataStructs.BulkTanimotoSimilarity(query_fp, library_fps)
ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
```

Keep vector types compatible:

- Compare explicit bit vectors with explicit bit vectors from the same generator settings.
- Compare count vectors with count-compatible metrics only when counts are intentional.
- Keep `fpSize`, radius, chirality, and feature settings identical across query and library fingerprints.
- Do not mix sparse and explicit forms in the same matrix unless the chosen function supports both and you have tested it.

## Top-K Similarity Search

A safe top-k search keeps invalid inputs out of the fingerprint list and returns original row metadata:

```python
def parse_valid(smiles_values):
    valid = []
    errors = []
    for index, smiles in enumerate(smiles_values):
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            errors.append({"index": index, "smiles": smiles, "error": "invalid SMILES"})
        else:
            valid.append({"index": index, "smiles": smiles, "mol": mol})
    return valid, errors

valid, errors = parse_valid(["CCO", "not-a-smiles", "CCN"])
generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
for row in valid:
    row["fp"] = generator.GetFingerprint(row["mol"])

query_fp = valid[0]["fp"]
scores = DataStructs.BulkTanimotoSimilarity(query_fp, [row["fp"] for row in valid])
top = sorted(zip(valid, scores), key=lambda item: item[1], reverse=True)[:5]
```

## Fingerprint Columns for ML

For small datasets, explicit bit vectors can be expanded into 0/1 columns:

```python
from rdkit import DataStructs
import numpy as np

array = np.zeros((fingerprint.GetNumBits(),), dtype=np.int8)
DataStructs.ConvertToNumpyArray(fingerprint, array)
bit_columns = {f"morgan_{i}": int(value) for i, value in enumerate(array)}
```

Guidance:

- Use explicit bit vectors for fixed-width ML tables and common scikit-learn style inputs.
- Use sparse fingerprints for memory-efficient similarity workflows over large libraries.
- Use count fingerprints for count-aware models; do not binarize counts unless that is a deliberate modeling choice.
- Persist the generator settings with trained models so future query fingerprints match training columns.

## Butina Clustering from Similarities

`rdkit.ML.Cluster.Butina.ClusterData` accepts either feature vectors (`isDistData=False`) or a precomputed distance matrix/list (`isDistData=True`). For fingerprint clustering, build a condensed lower-triangle distance list in the same order RDKit expects:

```python
from rdkit import DataStructs
from rdkit.ML.Cluster import Butina

fingerprints = [generator.GetFingerprint(mol) for mol in mols]
distances = []
for i in range(1, len(fingerprints)):
    sims = DataStructs.BulkTanimotoSimilarity(fingerprints[i], fingerprints[:i])
    distances.extend(1.0 - sim for sim in sims)

clusters = Butina.ClusterData(distances, len(fingerprints), distThresh=0.35, isDistData=True)
```

Interpretation:

- `distThresh` is a distance cutoff, not a similarity cutoff. A Tanimoto similarity cutoff of `0.65` corresponds to `distThresh=0.35`.
- Returned clusters are tuples of input indices; the first element is the centroid selected by the Butina algorithm.
- Keep the original molecule metadata list in the same order as `fingerprints` to map cluster indices back to molecules.
- `reordering=True` updates neighbor counts after each cluster is chosen and can change cluster composition.

## Additional Output for Bit Explanations

When explaining Morgan bits or atom environments, use generator `AdditionalOutput` rather than legacy `bitInfo` plumbing:

```python
from rdkit.Chem import rdFingerprintGenerator

additional = rdFingerprintGenerator.AdditionalOutput()
additional.AllocateBitInfoMap()
fp = generator.GetFingerprint(mol, additionalOutput=additional)
bit_info = additional.GetBitInfoMap()
```

The exact additional-output methods vary by fingerprint type and RDKit version, so guard explanatory tooling with a small smoke test before using it in production.
