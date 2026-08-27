# Troubleshooting Descriptors and Fingerprints

## Invalid Molecules

Symptoms:

- `Chem.MolFromSmiles(...)` returns `None`.
- Descriptor or fingerprint functions fail with confusing C++ argument errors.
- Feature tables silently contain missing rows or all-zero placeholders.

Fixes:

- Check every parsed molecule before calling descriptor or fingerprint APIs.
- Preserve the input index and original SMILES in error records.
- Route sanitization, kekulization, and supplier behavior to `../molecule-io-core/` when parsing is the real problem.
- Never treat an invalid molecule as a valid zero-vector unless the downstream model explicitly defines that encoding.

## Deprecated Morgan Helpers

Symptoms:

- Warnings about using Morgan generator APIs.
- New code still calls `AllChem.GetMorganFingerprintAsBitVect` or `rdMolDescriptors.GetMorganFingerprintAsBitVect`.
- Old parameters such as `nBits`, `bitInfo`, or `useChirality` do not line up with generator examples.

Fixes:

- Replace legacy bit-vector calls with `rdFingerprintGenerator.GetMorganGenerator(...).GetFingerprint(mol)`.
- Map `nBits` to `fpSize` and `useChirality` to `includeChirality`.
- For count fingerprints, call `GetCountFingerprint` or `GetSparseCountFingerprint` instead of `GetFingerprint`.
- For bit explanations, use `rdFingerprintGenerator.AdditionalOutput()` and allocate the required output collection before fingerprinting.

## Bit-Vector Length or Type Errors

Symptoms:

- Similarity functions raise type errors.
- Similarities look wrong because query and library fingerprints were generated with different settings.
- A numpy or pandas matrix has inconsistent widths.

Fixes:

- Build query and library fingerprints with the same generator instance or the same recorded settings.
- Keep `radius`, `fpSize`, chirality, feature invariants, and count simulation settings consistent.
- Use `fingerprint.GetNumBits()` for explicit bit-vector width checks.
- Do not compare explicit bit vectors against sparse count vectors unless the selected `DataStructs` metric supports that exact pair and tests cover it.
- Recompute fingerprints after changing molecule standardization rules; molecule identity and salt/tautomer choices affect bits.

## Sparse vs Explicit Fingerprints

Symptoms:

- Memory usage grows when expanding sparse fingerprints into dense arrays.
- `ConvertToNumpyArray` does not produce the expected fixed-length vector.
- Similarity search and model-training code disagree about feature dimensions.

Fixes:

- Use `GetFingerprint` for fixed-size explicit bit vectors in small ML tables.
- Use `GetSparseFingerprint` or `GetSparseCountFingerprint` for large similarity-search libraries or unfolded identifiers.
- Convert explicit bit vectors to numpy arrays only when a fixed-width ML matrix is required.
- Keep sparse/count fingerprints as sparse data structures for search unless there is a clear modeling requirement to densify.

## Descriptor Registry Surprises

Symptoms:

- `Descriptors.CalcMolDescriptors` returns more or fewer columns than expected.
- A model trained with one RDKit version cannot find a descriptor column later.
- Vector descriptor names appear after calling setup functions.

Fixes:

- Store the RDKit version and ordered descriptor column list with every trained model or exported feature table.
- Use a fixed, explicit descriptor list for production models instead of blindly using the full registry.
- Call `Descriptors.setupAUTOCorrDescriptors()` only when AUTOCORR2D columns are required and expected.
- Treat 3D descriptors separately; they require conformers and should route through `../conformers-drawing/` for embedding failures.

## Butina Distance Matrix Problems

Symptoms:

- `Butina.ClusterData` raises `ValueError: Mismatched input data dimension and nPts`.
- Clusters are unexpectedly large or small.
- The cutoff appears inverted relative to a desired similarity threshold.

Fixes:

- For `isDistData=True`, pass exactly `nPts * (nPts - 1) // 2` distances in lower-triangle order.
- Convert similarity to distance with `distance = 1.0 - similarity`.
- Convert a desired similarity cutoff `s` to `distThresh = 1.0 - s`.
- Keep input molecule/fingerprint metadata in the same order used to build the distance list.
- Use `reordering=True` only when you intentionally want neighbor counts updated after each selected centroid.

## Pandas and Export Issues

Symptoms:

- Object columns contain RDKit molecules or bit-vector objects that do not serialize cleanly.
- CSV output loses fingerprint information or stores unreadable objects.
- Invalid rows disappear during `DataFrame` construction.

Fixes:

- Export descriptor rows as plain numbers, strings, and booleans.
- Convert explicit fingerprints to numeric bit columns or store compact text/binary representations deliberately.
- Maintain a separate error table for invalid inputs.
- Keep molecule objects in pandas only for interactive analysis; route broader pandas/RDKit integration to `../data-cli-integration/`.
