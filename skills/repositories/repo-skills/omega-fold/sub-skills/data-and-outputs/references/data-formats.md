# Data Formats and Output Semantics

## FASTA Input Contract

OmegaFold reads a normal FASTA file containing one or more sequences. A header line starts with either `>` or `:`, and the amino-acid sequence follows on the next line or across continuation lines until the next header.

Accepted pattern:

```text
>protein_a
ACDEFGHIK
:protein_b
MSTNPKPQR
```

Operational details from `pipeline.fasta2inputs`:

- Sequence lines are uppercased before residue lookup.
- Entries are sorted by sequence length before yielding; output order can differ from file order.
- Headers are used for output PDB names after path-separator replacement and length checks.
- Blank physical lines are not explicitly ignored unless their line length is zero, so avoid blank lines inside records.
- A sequence line before the first header is invalid in practice because the parser has no active record to append to.

## Residue Normalization

Before tensorization, OmegaFold applies these substitutions to each sequence:

| Input residue | Internal residue | Meaning |
| --- | --- | --- |
| `Z` | `E` | Treat ambiguous glutamate/glutamine as glutamate. |
| `B` | `D` | Treat ambiguous aspartate/asparagine as aspartate. |
| `U` | `C` | Treat selenocysteine as cysteine. |
| `-` | mask token index `21` | Gap/mask position; written neither as a real residue nor atom in PDB output. |
| `X` | unknown residue index `20` | Allowed as unknown residue. |

Canonical residues map to indices in this order:

```text
A R N D C Q E G H I L K M F P S T W Y V X -
0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21
```

Invalid letters are rejected during `rc.restypes_with_x.index(aa)` lookup before the later assertion can run. Treat errors such as `ValueError: '<letter>' is not in list` as invalid amino-acid input.

## `fasta2inputs` Tensor Layout

`pipeline.fasta2inputs(...)` yields one item per FASTA entry after length sorting:

```text
(input_data, save_path)
```

`input_data` is a list with `num_cycle` dictionaries. Each cycle dictionary has:

| Key | Shape | Dtype intent | Meaning |
| --- | --- | --- | --- |
| `p_msa` | `[num_pseudo_msa + 1, num_res]` | integer residue indices | Row `0` is the unmasked target sequence; remaining rows are pseudo-MSA copies with random masking. |
| `p_msa_mask` | `[num_pseudo_msa + 1, num_res]` | float/bool mask | Row `0` is all ones; pseudo rows are sampled with `torch.rand(...).gt(mask_rate)`. |

Important controls:

- `num_cycle` controls how many cycle dictionaries are produced.
- `num_pseudo_msa` controls how many pseudo rows are added after the target row.
- `mask_rate` is the probability threshold used to mask pseudo-MSA positions; masked positions in `p_msa` become `21`.
- `deterministic=True` seeds a local `torch.Generator` with `num_res`, making the pseudo-mask reproducible for a given sequence length and parameters.
- `device` moves the nested tensors through OmegaFold's recursive device helper.

## Output Directory and PDB Naming

If `output_dir` is provided, `save_path` is created inside that directory and the directory should already exist when calling `fasta2inputs` directly. If `output_dir=None`, OmegaFold creates a sibling folder next to the FASTA file using the FASTA basename without the first extension:

```text
/path/to/input.fasta -> /path/to/input/<header>.pdb
```

For each sequence header:

- If the header length is below the filesystem name limit minus four characters, `os.path.sep` is replaced with `-` and the result becomes `<header>.pdb`.
- If the header is too long, the output name becomes `<i>th chain.pdb`, where `i` is the zero-based index after length sorting.
- On Unix-like systems, `/` is replaced by `-`. Backslashes are not `os.path.sep` on Unix and should be avoided in headers for portability.
- Direct `fasta2inputs(..., output_dir="existing_dir")` expects the output directory to exist before it queries filesystem name limits; the CLI creates its positional output directory before calling this parser.
- Duplicate headers can resolve to the same PDB path and later outputs can overwrite earlier ones; make headers unique after separator replacement.

OmegaFold writes one PDB per input sequence, not one combined multi-chain PDB.

## PDB and Confidence Semantics

Full inference writes PDBs by calling:

```python
pipeline.save_pdb(
    pos14=output["final_atom_positions"],
    b_factors=output["confidence"] * 100,
    sequence=input_data[0]["p_msa"][0],
    mask=input_data[0]["p_msa_mask"][0],
    save_path=save_path,
    model=0,
)
```

Interpretation:

- `output["confidence"]` is per-residue predicted confidence, derived from OmegaFold's confidence head on a 0-1 scale.
- The CLI multiplies confidence by `100` before PDB writing, so B-factor values in normal inference outputs are pLDDT-like 0-100 values.
- `save_pdb` stores the provided `b_factors` value on every emitted atom for that residue.
- The PDB chain id defaults to `A`; `save_pdb(..., init_chain='B')` can choose another chain for custom scripts.
- Residues with `mask=False`, sequence index `21`, or an out-of-range residue index are skipped.
- Atom coordinates must use OmegaFold's atom14 layout: `[num_res, 14, 3]` positions plus `[num_res]` sequence and mask values.

## Atom14 Writer Expectations

`save_pdb` maps residue indices to standard three-letter residue names and then emits non-empty atom names from the atom14 table. For example, alanine emits backbone atoms plus `CB`; glycine emits no `CB`. Empty atom slots are ignored.

Use `save_pdb` for OmegaFold-style atom14 tensors. It is not a general-purpose PDB repair, multi-chain assembly, ligand writer, or mmCIF exporter.
