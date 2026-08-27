# Structure-sequence troubleshooting

## Missing Foldseek executable

Symptoms:

- The converter exits before running Foldseek.
- Error text says the Foldseek path does not exist, is not executable, or is not found on `PATH`.

Fix:

1. Install or download a Foldseek binary compatible with the host platform.
2. Put it on `PATH` and pass `--foldseek foldseek`, or pass the executable file location supplied by the user.
3. Re-run the bundled converter from any working directory; the script does not import SaProt repository modules.

## Missing or unsupported structure path

Symptoms:

- Error text says the structure path was not found or is not a file.
- pLDDT extraction reports an unsupported suffix.

Fix:

- Pass an existing `.pdb`, `.cif`, or `.mmcif` path to `--structure`.
- If pLDDT masking is requested, use `.pdb`, `.cif`, or `.mmcif` files that Bio.PDB can parse.

## Empty Foldseek output

Symptoms:

- Foldseek exits successfully but the descriptor file is empty.
- The converter reports that no chains were parsed.

Fix:

- Confirm Foldseek can process the structure with `structureto3didescriptor` directly.
- Check that the structure contains protein atoms rather than only nucleic acid, ligand, or incomplete records.
- Rerun with `--foldseek-verbose` to see Foldseek diagnostics.

## Low-confidence AlphaFold masking

Symptoms:

- Combined tokens contain `#` in the second character, such as `M#` or `L#`.
- Masking happens automatically for AlphaFold-style files.

Explanation:

- `#` replaces the 3Di character where average residue pLDDT is below `--plddt-threshold`.
- The amino-acid character is preserved, so sequence length and residue positions remain aligned.

Fix or adjustment:

- Use `--plddt-mask false` for experimental PDB structures or when masking is not desired.
- Use `--plddt-threshold` to adjust sensitivity.
- Use `--plddt-mask true` for AlphaFold-derived files whose metadata does not contain an AlphaFold marker.

## Chain-name mismatch

Symptoms:

- The converter returns no records for `--chain B`.
- JSON output lists a different set of `available_chains`.

Fix:

1. Run once without `--chain` and inspect `available_chains`.
2. Use exact chain IDs as Foldseek reports them.
3. For multi-chain structures, remember that Foldseek descriptor names may include file, model, or chain decorations before the final chain suffix.

## Temporary output cleanup

The converter writes Foldseek descriptor files into a private temporary directory and deletes that directory after parsing, even on failures. If a process is interrupted by the operating system, stale temporary files may remain in the platform temporary directory and can be removed safely after no converter process is running.

## Bio.PDB parser errors

Symptoms:

- pLDDT masking fails with parser warnings or exceptions.
- The converter still returns unmasked Foldseek records with warning messages.

Fix:

- Validate that the file is a well-formed PDB or mmCIF.
- Disable masking with `--plddt-mask false` if the structure is experimental and B-factors are not pLDDT.
- Use a cleaned structure file if Bio.PDB cannot parse the original.

## pLDDT length mismatch

Symptoms:

- Warning text reports a mismatch between pLDDT residue count and Foldseek 3Di length.
- Masking is skipped for that chain to avoid corrupting residue alignment.

Fix:

- Check for non-standard residues, missing residues, alternate chains, or descriptor chain-name mismatch.
- Rerun without chain filtering to verify which Foldseek chain corresponds to the parsed Bio.PDB chain.
- If alignment cannot be trusted, use unmasked conversion and document the confidence limitation for downstream model inference.
