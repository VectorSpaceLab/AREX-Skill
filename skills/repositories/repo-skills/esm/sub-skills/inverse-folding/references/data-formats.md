# Inverse-Folding Data Formats

ESM-IF1 consumes protein backbone coordinates and optionally target sequences. Keep data validation explicit because most runtime failures come from structure parsing, chain selection, missing atoms, sequence length mismatch, or output-path assumptions.

## Structure Inputs

Supported file suffixes:

| Suffix | Loader path | Notes |
| --- | --- | --- |
| `.pdb` | `biotite.structure.io.pdb.PDBFile` through `util.load_structure` | Uses first model and filters backbone atoms. |
| `.cif` | `biotite.structure.io.pdbx.PDBxFile` through `util.load_structure` | Also used for mmCIF files. |

`util.load_structure(fpath, chain=None)` accepts:

- `chain=None` to keep all chains after backbone filtering.
- A string chain ID such as `"C"` to keep one chain.
- A list of chain IDs such as `["A", "B", "C"]` to keep a selected chain set.

Failure behavior:

- No parsed chains raises `ValueError: No chains found in the input file.`
- Missing target chain raises `ValueError: Chain <id> not found in input file`.
- Unsupported suffixes fail because only `.pdb` and `.cif` paths are parsed.

## Backbone Coordinate Tensor

The inverse-folding model expects one coordinate array per chain with shape:

```text
L x 3 x 3
```

Where:

| Axis | Meaning |
| --- | --- |
| `L` | Residues in the extracted chain. |
| `3` atom axis | Backbone atoms in order `N`, `CA`, `C`. |
| `3` coordinate axis | Cartesian `x`, `y`, `z` values. |

Element mapping:

```text
coords[i][0] = N atom coordinates for residue i
coords[i][1] = CA atom coordinates for residue i
coords[i][2] = C atom coordinates for residue i
```

`util.extract_coords_from_structure(structure)` returns:

```python
coords, seq = esm.inverse_folding.util.extract_coords_from_structure(structure)
```

`coords` is the `L x 3 x 3` array and `seq` is the one-letter sequence converted from residue names.

## Missing Coordinates

Missing atoms become non-finite coordinate rows. `get_atom_coords_residuewise(["N", "CA", "C"], structure)` writes `nan` for atoms that are absent in a residue. Manual masking often uses `inf`:

```python
coords[:10, :] = float("inf")
```

Downstream scoring uses finite-coordinate masks:

```python
coord_mask = np.all(np.isfinite(coords), axis=(-1, -2))
```

Practical rules:

- A residue must have finite `N`, `CA`, and `C` coordinates to count in `ll_withcoord`.
- Missing coordinates are acceptable for ESM-IF1, but too many missing residues can make scoring hard to interpret.
- If all target-chain coordinates are non-finite, scoring can divide by zero or produce invalid values.

## Multichain Dictionaries

`multichain_util.extract_coords_from_complex(structure)` returns two dictionaries:

```python
coords, seqs = esm.inverse_folding.multichain_util.extract_coords_from_complex(structure)
```

Shape:

```python
coords = {
    "A": array_of_shape_LA_3_3,
    "B": array_of_shape_LB_3_3,
    "C": array_of_shape_LC_3_3,
}
seqs = {
    "A": "...",
    "B": "...",
    "C": "...",
}
```

Multichain sampling and scoring target exactly one chain:

```python
target_chain_id = "C"
```

The utility concatenates the target chain first, inserts padding between chains, and conditions on the rest of the complex. The default padding length is `10` residues with non-finite coordinates.

## Variant FASTA Input

Scoring mode expects a FASTA file with one or more sequence records:

```text
>native
MSTNPKPQR...
>variant_A10V
MSTNPKPQR...
```

Validation checklist:

- Use a `.fasta`, `.fa`, or text FASTA path for clarity.
- Every record should be a protein sequence compatible with the ESM alphabet.
- For fixed-backbone scoring, each target sequence should match the target-chain coordinate length.
- Avoid commas in FASTA headers if writing simple CSV output, because the bundled source-compatible output is comma-separated without quoting.

## Sampled FASTA Output

Sampling output is FASTA:

```text
>sampled_seq_1
ACDEFGHIKLMNPQRSTVWY
>sampled_seq_2
ACDEFGHIKLMNPQRSTVWY
```

Recommended post-processing:

- Confirm every sequence length matches the target-chain coordinate length.
- Flag long homopolymer repeats, especially repeated acidic residues such as `EEEEEEEE`.
- Record the sampling temperature and single-chain/multichain mode alongside each design batch.

## Scoring CSV Output

Scoring output schema:

```text
seqid,log_likelihood
native,-1.2345
variant_A10V,-1.4567
```

Column meanings:

| Column | Meaning |
| --- | --- |
| `seqid` | FASTA header string. |
| `log_likelihood` | Average conditional log-likelihood over the scored target sequence. |

For API workflows, prefer retaining both values returned by scoring:

```text
seqid,log_likelihood_fullseq,log_likelihood_withcoord
```

`log_likelihood_withcoord` is useful when missing backbone coordinates should be excluded from the average.

## Chain IDs

Chain IDs come from the parsed structure, not from a user assumption or file name. Before long jobs:

1. Inspect available chain IDs with a structure parser or a short validation script.
2. Confirm the target chain has meaningful length after backbone filtering.
3. Confirm all required chains are present before using multichain conditioning.
4. Be careful with mmCIF files where displayed author chain IDs may differ from internal asym IDs depending on parser behavior.

## Output Paths

Sampling and scoring scripts create the parent output directory before writing. The bundled helper validates and creates output directories only in `--execute` mode; dry-run mode prints what would be created.

Use explicit output names:

```text
output/sampled_sequences.fasta
output/chain_c_variant_scores.csv
```

Avoid writing into temporary or source-repo example directories when building reusable agent workflows.
