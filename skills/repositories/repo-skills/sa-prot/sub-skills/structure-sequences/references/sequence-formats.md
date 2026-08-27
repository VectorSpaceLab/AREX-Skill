# SaProt structure-sequence formats

## Conversion source

SaProt structure-aware input starts from Foldseek `structureto3didescriptor` output. For each reported chain, Foldseek emits an amino-acid sequence and a 3Di structural alphabet sequence. The SaProt utility pattern pairs those columns residue by residue.

The bundled converter runs Foldseek with chain-name mode enabled so individual chains can be selected after conversion. A tiny mmCIF structure such as the SaProt example `example/8ac8.cif` is useful evidence for checking that a local Foldseek binary can process mmCIF input, but runtime workflows should pass their own structure path.

## Output sequence types

- `aa`: the amino-acid sequence reported by Foldseek.
- `foldseek`: the 3Di structural sequence reported by Foldseek, normalized to lowercase for SaProt token pairing.
- `combined`: the SaProt AA+3Di sequence. Each residue becomes a two-character token: one amino acid followed by one lowercase 3Di character or `#`.

Examples of combined tokens:

- `M#` means amino acid `M` with masked or unavailable structural context.
- `Ev` means amino acid `E` paired with 3Di token `v`.
- `Qp` means amino acid `Q` paired with 3Di token `p`.

A combined sequence is the concatenation of these two-character tokens, for example `M#EvVpQpL#VyQdYaKv`. Tokenizers for SaProt models treat this as a sequence of AA+3Di pairs rather than as independent single characters.

## pLDDT masking

SaProt recommends masking low-confidence regions in predicted AlphaFold-style structures. Masking changes only the structural half of the combined token: the amino-acid character remains unchanged and the 3Di character becomes `#` when pLDDT is below the threshold.

The bundled converter supports:

- `--plddt-mask auto`: inspect the structure text for AlphaFold-style provenance and enable masking when it is detected.
- `--plddt-mask true`: always attempt to parse pLDDT values from B-factors and mask low-confidence residues.
- `--plddt-mask false`: never apply pLDDT masking.
- `--plddt-threshold 70.0`: default threshold used by the SaProt utility pattern.

For `.cif` input the converter uses Bio.PDB `MMCIFParser`; for `.pdb` input it uses `PDBParser`. It averages atom B-factors per residue for the selected chain, matching the SaProt pLDDT masking convention.

## Chain selection

When `--chain` is omitted, the converter emits every chain present in the Foldseek descriptor file. When one or more `--chain` values are supplied, only exact chain IDs are emitted. If no requested chain appears, inspect the JSON `available_chains` field or rerun without `--chain` to see Foldseek's chain naming.

Foldseek chain names can differ from the user-visible biological label when structures contain model or entity decorations. The converter derives the chain ID from the descriptor name in the same style as SaProt: remove the input file name prefix, then take the suffix after the final underscore.

## Choosing a format for downstream work

- Use `combined` for SaProt structural token input, mutation scoring, embedding extraction, and most structure-aware tasks.
- Use `aa` only when a downstream model or dataset explicitly expects amino acids without structural tokens.
- Use `foldseek` for debugging 3Di conversion or for tools that store the structural alphabet separately.

After generating a combined sequence, route model scoring or embedding tasks to `model-inference`. For storing converted records in LMDB or dataset manifests, route to `datasets-configs`.
