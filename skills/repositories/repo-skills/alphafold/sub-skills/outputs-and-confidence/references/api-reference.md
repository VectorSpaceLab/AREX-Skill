# Confidence and Protein API Reference

This reference covers public AlphaFold 2.3.2 APIs used to create and interpret structure/confidence outputs.

## `alphafold.common.confidence`

| Function | Contract | Output or caveat |
| --- | --- | --- |
| `compute_plddt(logits)` | Accepts logits shaped `[num_res, num_bins]` from the predicted LDDT head. | Returns `[num_res]` pLDDT values scaled to `0..100`. |
| `confidence_json(plddt)` | Accepts a rank-1 pLDDT array. | Returns compact JSON with `residueNumber`, `confidenceScore`, and `confidenceCategory`. Raises `ValueError` when pLDDT is not rank 1. |
| `compute_predicted_aligned_error(logits, breaks)` | Accepts PAE logits shaped `[num_res, num_res, num_bins]` and bin-edge breaks shaped `[num_bins - 1]`. | Returns `aligned_confidence_probs`, `predicted_aligned_error`, and `max_predicted_aligned_error`. |
| `pae_json(pae, max_pae)` | Accepts a square `N x N` PAE matrix and max PAE value. | Returns AFDB-style compact JSON list with one object. Raises `ValueError` if PAE is not square. |
| `predicted_tm_score(logits, breaks, residue_weights=None, asym_id=None, interface=False)` | Computes pTM or ipTM from predicted aligned error logits and breaks. | Use `interface=True` with `asym_id` for interface TM-style scoring. |

## Confidence JSON Details

`confidence_json` emits compact JSON like:

```json
{"residueNumber":[1,2],"confidenceScore":[42.0,42.42],"confidenceCategory":["D","D"]}
```

Categories are derived from pLDDT:

- `D`: `0 <= score < 50`
- `L`: `50 <= score < 70`
- `M`: `70 <= score < 90`
- `H`: `90 <= score <= 100`

Invalid scores outside `0..100` are rejected by the internal categorizer.

## PAE JSON Details

`pae_json` emits compact JSON like:

```json
[{"predicted_aligned_error":[[0.0,13.1],[20.1,0.0]],"max_predicted_aligned_error":31.75}]
```

Important shape rules:

- The PAE array must be rank 2.
- The PAE array must be square: `shape[0] == shape[1]`.
- Values are rounded to one decimal place.
- AFDB may return integer PAE values, while AlphaFold's helper emits floats rounded to one decimal place.

## `alphafold.common.protein.Protein`

`Protein` is a frozen dataclass with array fields:

| Field | Shape | Meaning |
| --- | --- | --- |
| `atom_positions` | `[num_res, num_atom_type, 3]` | Cartesian atom coordinates in angstroms. |
| `aatype` | `[num_res]` | Amino-acid type index; unknown `X` is represented by the final residue type index. |
| `atom_mask` | `[num_res, num_atom_type]` | Atom presence mask. |
| `residue_index` | `[num_res]` | Residue numbering as used in PDB/mmCIF, not necessarily contiguous. |
| `chain_index` | `[num_res]` | Zero-indexed chain index per residue. |
| `b_factors` | `[num_res, num_atom_type]` | B-factor values; AlphaFold prediction outputs commonly store pLDDT here. |

A `Protein` object with more than 62 unique chains cannot be written to PDB because the PDB chain alphabet has 62 single-character chain IDs.

## Structure Parsing APIs

| Function | Contract | Caveats |
| --- | --- | --- |
| `from_pdb_string(pdb_str, chain_id=None)` | Parses one PDB string into `Protein`; optional single-chain filter. | Only single-model structures are supported. Insertion codes are rejected. Non-standard residues become `UNK`; non-standard atoms are ignored. |
| `from_mmcif_string(mmcif_str, chain_id=None)` | Parses one mmCIF string into `Protein`; optional single-chain filter. | Same single-model, insertion-code, non-standard residue, and atom caveats as PDB parsing. |
| `to_pdb(prot)` | Converts `Protein` to PDB string. | Fails when any chain index exceeds the 62-chain PDB limit. Lines are padded to 80 characters. |
| `to_mmcif(prot, file_id, model_type)` | Converts `Protein` to mmCIF string and adds AlphaFold/ModelCIF-style metadata for `Monomer` or `Multimer`. | Missing residue numbers are filled with `UNK`; original chain IDs and non-standard residue details are not preserved after parse-and-write. |
| `ideal_atom_mask(prot)` | Computes the ideal heavy-atom mask for the residue sequence. | Useful for comparing observed atoms to expected standard atoms. |
| `from_prediction(features, result, b_factors=None, remove_leading_feature_dimension=True)` | Builds `Protein` from model features and prediction result. | Uses `features['asym_id']` for chain indices when present, otherwise treats all residues as one chain; residue indices are shifted to 1-based numbering. |

## Output-Writing API Behavior

The prediction workflow writes confidence and structure files by combining these APIs:

1. `prediction_result['plddt']` is passed to `confidence_json` and saved as `confidence_<model>.json`.
2. `prediction_result['predicted_aligned_error']` and `prediction_result['max_predicted_aligned_error']`, when present, are passed to `pae_json` and saved as `pae_<model>.json`.
3. `protein.from_prediction` creates an unrelaxed `Protein` with pLDDT repeated into per-atom B-factors.
4. `protein.to_pdb` writes `unrelaxed_<model>.pdb` and ranked PDB files.
5. `protein.to_mmcif` writes `unrelaxed_<model>.cif`, relaxed mmCIF files, and ranked mmCIF files.

## Confidence Interpretation Rules

- pLDDT is local confidence; use it for residue-level reliability and likely disorder.
- PAE is pairwise placement confidence; use it to assess relative domain or chain arrangement.
- pTM estimates global topology confidence for pTM-enabled models.
- ipTM emphasizes interface confidence for complexes and requires asymmetric chain IDs for interface scoring.
- Do not treat a high-confidence local fold as proof that all domains or chains are correctly positioned relative to each other.
