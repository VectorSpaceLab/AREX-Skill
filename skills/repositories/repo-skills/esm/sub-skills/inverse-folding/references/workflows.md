# Inverse-Folding Workflows

Use these workflows to plan ESM-IF1 tasks without depending on external example scripts. The bundled `inverse_folding_cli_helper.py` helper constructs commands safely and defaults to dry-run; run it from the `inverse-folding` sub-skill directory as shown in the examples.

## Choose The Workflow

| Goal | Prefer | Key choices |
| --- | --- | --- |
| Design sequences for one chain from its backbone only | Single-chain sampling | `sample`, `--chain`, `--temperature`, `--num-samples` |
| Design one chain while using neighboring chains as context | Multichain sampling | `sample`, `--chain`, `--multichain-backbone` |
| Score variants against one chain structure | Single-chain scoring | `score`, structure, variant FASTA, `--chain` |
| Score variants with complex context | Multichain scoring | `score`, structure, variant FASTA, `--chain`, `--multichain-backbone` |
| Extract learned structure representations | API workflow | `get_encoder_output` or `get_encoder_output_for_complex` |
| Diagnose input structure failures | Validation workflow | suffix, chain list, N/CA/C atoms, non-finite coordinates |

## CLI-Style Sampling

Dry-run a single-chain sampling command:

```bash
python scripts/inverse_folding_cli_helper.py sample input.pdb \
  --chain C \
  --temperature 1.0 \
  --num-samples 3 \
  --outpath output/sampled_sequences.fasta
```

Dry-run a multichain sampling command where all chains condition target-chain design:

```bash
python scripts/inverse_folding_cli_helper.py sample input.pdb \
  --chain C \
  --temperature 1e-6 \
  --num-samples 5 \
  --outpath output/sampled_sequences_multichain.fasta \
  --multichain-backbone
```

Interpretation:

- `--temperature 1.0` gives more diversity.
- Very low temperatures such as `1e-6` are useful when native-like recovery is more important than diversity.
- `--multichain-backbone` loads all chains into the encoder and samples only the requested `--chain`.
- Output is FASTA with headers like `>sampled_seq_1`.

Execution:

```bash
python scripts/inverse_folding_cli_helper.py sample input.pdb \
  --chain C --outpath output/sampled_sequences.fasta --execute
```

Only execute after confirming dependencies, model weights, and compute resources. First execution may download the pretrained ESM-IF1 checkpoint.

## CLI-Style Scoring

Dry-run a single-chain variant scoring command:

```bash
python scripts/inverse_folding_cli_helper.py score input.pdb variants.fasta \
  --chain C \
  --outpath output/variant_scores.csv
```

Dry-run a multichain scoring command for target chain `C` with a variant FASTA and output CSV:

```bash
python scripts/inverse_folding_cli_helper.py score complex.cif variants.fasta \
  --chain C \
  --outpath output/chain_c_variant_scores.csv \
  --multichain-backbone
```

The score output schema is:

```text
seqid,log_likelihood
variant_name,-1.2345
```

Higher log-likelihood indicates the sequence is more probable under the structure-conditioned model. For structures with missing coordinates, the lower-level API also returns `ll_withcoord`, which excludes masked positions.

## API Sampling

Single-chain sampling:

```python
import torch
import esm
import esm.inverse_folding

model, alphabet = esm.pretrained.esm_if1_gvp4_t16_142M_UR50()
model = model.eval()
coords, native_seq = esm.inverse_folding.util.load_coords("input.pdb", "C")

with torch.no_grad():
    sampled_seq = model.sample(coords, temperature=1.0, device="cpu")
```

Multichain sampling:

```python
structure = esm.inverse_folding.util.load_structure("complex.pdb")
coords, native_seqs = esm.inverse_folding.multichain_util.extract_coords_from_complex(structure)
sampled_seq = esm.inverse_folding.multichain_util.sample_sequence_in_complex(
    model, coords, target_chain_id="C", temperature=1.0
)
```

For best multichain performance, the utility concatenates the target chain first and separates additional chains with padding. Always verify that the target chain exists in `coords` before sampling.

## API Scoring

Single-chain scoring:

```python
coords, native_seq = esm.inverse_folding.util.load_coords("input.pdb", "C")
ll_fullseq, ll_withcoord = esm.inverse_folding.util.score_sequence(
    model, alphabet, coords, "ACDEFGHIKLMNPQRSTVWY"
)
```

Multichain scoring:

```python
structure = esm.inverse_folding.util.load_structure("complex.cif")
coords, native_seqs = esm.inverse_folding.multichain_util.extract_coords_from_complex(structure)
ll_fullseq, ll_withcoord = esm.inverse_folding.multichain_util.score_sequence_in_complex(
    model, alphabet, coords, target_chain_id="C", target_seq="ACDEFGHIKLMNPQRSTVWY"
)
```

Scoring checklist:

1. The target sequence length should match the coordinate length for the target chain.
2. FASTA records should contain standard amino-acid letters expected by the ESM alphabet.
3. Compare `ll_withcoord` instead of only `ll_fullseq` if missing coordinates are present.
4. Use the same single-chain versus multichain conditioning mode for all sequences in a comparison.

## Encoder Representation Workflow

Single-chain structure representation:

```python
coords, seq = esm.inverse_folding.util.load_coords("input.pdb", "A")
encoder_output = esm.inverse_folding.util.get_encoder_output(model, alphabet, coords)
```

Complex-conditioned target-chain representation:

```python
structure = esm.inverse_folding.util.load_structure("complex.pdb")
coords, seqs = esm.inverse_folding.multichain_util.extract_coords_from_complex(structure)
encoder_output = esm.inverse_folding.multichain_util.get_encoder_output_for_complex(
    model, alphabet, coords, target_chain_id="A"
)
```

The returned tensor is per target residue after removing beginning/end special tokens. Treat it as a structure-conditioned representation, not as a generic sequence embedding.

## Missing-Coordinate Workflow

When residues are absent, disordered, or intentionally masked:

```python
coords[:10, :] = float("inf")
```

Then score with:

```python
ll_fullseq, ll_withcoord = esm.inverse_folding.util.score_sequence(model, alphabet, coords, seq)
```

Use `ll_withcoord` for comparisons that should ignore masked positions. If many residues are non-finite, inspect whether the structure parser lost atom records or the input chain is not the intended biological chain.

## Post-Sampling Quality Control

Repeated amino-acid runs such as `EEEEEEEE` are a known sampling failure mode. After generating FASTA designs:

1. Parse every sampled sequence.
2. Flag sequences with long homopolymer runs, such as 8 or more identical residues.
3. Re-sample at a lower temperature or increase filtering if repeats are common.
4. Compare both single-chain and multichain conditioning; one mode can outperform the other depending on the protein.

## Diagnostic Case: Chain Not Found Plus Repeats

If a user reports `Chain C not found in input file` and previous outputs had high-repeat designs:

1. Load or inspect the structure chain IDs; mmCIF files can use author/asym IDs differently from expectations.
2. Re-run command construction with the actual chain ID and keep `--dry-run` until the path and chain are correct.
3. Validate that N/CA/C atoms exist for the selected chain.
4. Use a lower temperature such as `1e-6` and apply a long-repeat filter to sampled FASTA records.
5. Try both single-chain and multichain conditioning after chain validation.
