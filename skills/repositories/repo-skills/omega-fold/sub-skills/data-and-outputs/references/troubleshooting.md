# Data and Output Troubleshooting

## Malformed FASTA

Symptoms:

- No yielded sequences.
- `IndexError` or unexpected sequence concatenation.
- A sequence appears under the wrong header.

Checks:

- Ensure every record starts with `>` or `:`.
- Put sequence lines after the header; do not put sequence text before the first header.
- Avoid blank lines inside records.
- Run `python sub-skills/data-and-outputs/scripts/inspect_fasta_pipeline.py --fasta input.fasta` and inspect the reported record count and output paths.

## Invalid or Ambiguous Residues

OmegaFold accepts canonical residues plus `X` and `-`, with pre-lookup substitutions for `Z`, `B`, and `U`:

```text
Z -> E, B -> D, U -> C, - -> 21, X -> 20
```

Symptoms:

- `ValueError: '<letter>' is not in list` from residue lookup.
- Assertion about amino-acid indices after tensorization.

Fixes:

- Remove whitespace, digits, `*`, `.`, and non-amino-acid annotations from sequence lines.
- Convert uncommon residues to one of `ARNDCQEGHILKMFPSTWYVX-` before running OmegaFold.
- Remember that `X` is accepted as unknown in the input tensors, but `save_pdb` skips unknown residue index `20` because the PDB residue conversion helper only covers canonical residues.

## Output Directory Surprises

Symptoms:

- A directory appears next to the FASTA during inspection.
- PDBs are written somewhere different from expected.

Causes and fixes:

- `fasta2inputs(..., output_dir=None)` creates `<fasta-basename>/` next to the input FASTA.
- Direct `fasta2inputs(..., output_dir="path")` expects that path to already exist; create it first or use the bundled helper, which creates its inspection output directory.
- `save_pdb` creates the parent directory for `save_path` automatically.
- Full CLI inference creates the positional `output_dir` before predictions begin.

## Header and Filename Problems

Symptoms:

- A slash in a FASTA header becomes a dash in the PDB filename.
- Long names become `0th chain.pdb`, `1th chain.pdb`, and so on.
- Outputs overwrite each other.

Explanation:

- OmegaFold replaces only the current platform's `os.path.sep` in headers before appending `.pdb`.
- It compares header length to the filesystem maximum name length minus four characters for `.pdb`; too-long headers use sorted-chain fallback names.
- Sorting by sequence length happens before fallback names are assigned.
- Duplicate names after separator replacement are not deduplicated.

Fixes:

- Use short, unique, portable headers such as `protein_a`, not full file paths or descriptions.
- Avoid `/`, `\\`, control characters, and very long identifiers in FASTA headers.
- If exact output names matter, run the bundled helper first to print predicted PDB paths.

## Empty or Sparse PDB Output

Symptoms:

- PDB file has few `ATOM` records or no residues.
- Some input positions are missing from the PDB.

Causes:

- `mask=False` residues are skipped.
- Gap token `21` is skipped.
- Unknown residue index `20` is skipped by `save_pdb` because `residx_to_3` only maps canonical residue indices.
- Atom14 slots with empty atom names are skipped by design.

Checks:

- Inspect `sequence` and `mask` values passed to `save_pdb`.
- Use canonical residues if a synthetic PDB writer test needs visible residue atoms.
- In model outputs, verify `final_atom_positions` shape is `[num_res, 14, 3]` before writing.

## Biopython / PDB Writer Issues

Symptoms:

- Import errors for `Bio` or `Bio.PDB`.
- PDB formatting errors from `PDBIO`.

Fixes:

- Ensure `biopython` is installed with OmegaFold.
- Keep `pos14` numeric and shaped `[num_res, 14, 3]`; avoid NaN or string data.
- Use simple chain ids such as `A`; PDB chain ids are one character.
- If using the legacy OmegaFold dependency stack with `torch==1.12.0`, keep `numpy<2` to avoid NumPy ABI warnings or failures from old PyTorch builds.

## Confidence Interpretation

Symptoms:

- User asks whether PDB B-factors are physical crystallographic B-factors.
- Values look like `80.00` or `95.00` in the PDB B-factor column.

Explanation:

- OmegaFold's CLI writes `output["confidence"] * 100` as PDB B-factors.
- Treat these as pLDDT-like per-residue confidence scores on a 0-100 scale, not experimental thermal displacement factors.
- `save_pdb` itself does not scale; it writes whatever `b_factors` tensor you pass.

## Sequence Order Confusion

Symptoms:

- The first PDB does not correspond to the first FASTA record.
- Fallback names like `0th chain.pdb` do not match file order.

Explanation and fix:

- `fasta2inputs` sorts `(header, sequence)` pairs by sequence length before yielding.
- Ask users to match outputs by printed `save_path` and sequence length, or inspect with the bundled helper before full inference.
