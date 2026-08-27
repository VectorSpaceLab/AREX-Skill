# Variant Prediction Workflows

This reference distills the ESM zero-shot variant prediction example into reusable command patterns. The bundled helper prints safe commands and validates tiny DMS CSVs before model inference.

## Model Families

| Use case | Model locations | Inputs | Supported scoring |
| --- | --- | --- | --- |
| ESM-1v ensemble | `esm1v_t33_650M_UR90S_1` through `esm1v_t33_650M_UR90S_5` | Wild-type sequence plus DMS CSV | `wt-marginals`, `masked-marginals`, `pseudo-ppl` |
| MSA Transformer | `esm_msa1b_t12_100M_UR50S` | Wild-type sequence, DMS CSV, A3M MSA | `masked-marginals` only |
| Local checkpoints | One or more model file paths | Same as matching architecture | Same as matching architecture |

ESM-1v was released as five same-architecture checkpoints intended for ensemble scoring. The example script writes one output column per `--model-location` value.

## Scoring Strategy Choice

- `wt-marginals`: runs the wild-type sequence once, then scores each mutant as `log p(mutant residue) - log p(wild-type residue)` at the mutated position. This is the common ESM-1v DMS path and is the least expensive of the three strategies.
- `masked-marginals`: masks each sequence position and scores substitutions from masked-token probabilities. This is required for MSA Transformer and can also be used with sequence models, but is more expensive because it loops over positions.
- `pseudo-ppl`: mutates the sequence first, then sums masked-position log probabilities across the mutated sequence. This is row-wise and expensive for large DMS tables.

## ESM-1v Command Pattern

Use the bundled runner through the helper default so the workflow remains self-contained after export:

```bash
python scripts/variant_prediction_helper.py \
  --model-location esm1v_t33_650M_UR90S_1 esm1v_t33_650M_UR90S_2 esm1v_t33_650M_UR90S_3 esm1v_t33_650M_UR90S_4 esm1v_t33_650M_UR90S_5 \
  --sequence HPETLVKVKDAEDQLGARVGYIELDLNSGKILESFRPEERFPMMSTFKVLLCGAVLSRVDAGQEQLGRRIHYSQNDLVEYSPVTEKHLTDGMTVRELCSAAITMSDNTAANLLLTTIGGPKELTAFLHNMGDHVTRLDRWEPELNEAIPNDERDTTMPAAMATTLRKLLTGELLTLASRQQLIDWMEADKVAGPLLRSALPAGWFIADKSGAGERGSRGIIAALGPDGKPSRIVVIYTTGSQATMDERNRQIAEIGASLIKHW \
  --dms-input dms.csv \
  --mutation-col mutant \
  --dms-output labeled.csv \
  --offset-idx 24 \
  --scoring-strategy wt-marginals
```

The helper validates the CSV and prints a command for `scripts/run_variant_prediction.py`. Add `--execute` only after model downloads, memory, and device requirements are acceptable. Full ESM-1v inference can still require model downloads and substantial memory.

## MSA Transformer Command Pattern

```bash
python scripts/variant_prediction_helper.py \
  --model-location esm_msa1b_t12_100M_UR50S \
  --sequence HPETLVKVKDAEDQLGARVGYIELDLNSGKILESFRPEERFPMMSTFKVLLCGAVLSRVDAGQEQLGRRIHYSQNDLVEYSPVTEKHLTDGMTVRELCSAAITMSDNTAANLLLTTIGGPKELTAFLHNMGDHVTRLDRWEPELNEAIPNDERDTTMPAAMATTLRKLLTGELLTLASRQQLIDWMEADKVAGPLLRSALPAGWFIADKSGAGERGSRGIIAALGPDGKPSRIVVIYTTGSQATMDERNRQIAEIGASLIKHW \
  --dms-input dms.csv \
  --mutation-col mutant \
  --dms-output labeled.csv \
  --offset-idx 24 \
  --scoring-strategy masked-marginals \
  --msa-path alignment.a3m \
  --msa-samples 400
```

The bundled runner expects A3M-like FASTA. It removes lowercase insertion letters plus `.` and `*` before batching; the first MSA sequence is the target sequence used for masked scoring.

## Helper-First Workflow

Use the bundled helper to catch notation and offset problems before expensive inference:

```bash
python sub-skills/variant-effect-prediction/scripts/variant_prediction_helper.py \
  --model-location esm1v_t33_650M_UR90S_1 esm1v_t33_650M_UR90S_2 \
  --sequence HPETLVKVKDAEDQLGARVGYIELDLNSGKILESFRPEERFPMMSTFKVLLCGAVLSRVDAGQEQLGRRIHYSQNDLVEYSPVTEKHLTDGMTVRELCSAAITMSDNTAANLLLTTIGGPKELTAFLHNMGDHVTRLDRWEPELNEAIPNDERDTTMPAAMATTLRKLLTGELLTLASRQQLIDWMEADKVAGPLLRSALPAGWFIADKSGAGERGSRGIIAALGPDGKPSRIVVIYTTGSQATMDERNRQIAEIGASLIKHW \
  --dms-input data/BLAT_ECOLX_Ranganathan2015.csv \
  --mutation-col mutant \
  --dms-output labeled.csv \
  --offset-idx 24 \
  --scoring-strategy wt-marginals \
  --nogpu
```

By default the helper prints a shell-quoted command that runs the bundled `scripts/run_variant_prediction.py` runner. Add `--execute` only after validation passes and the environment has the required model/runtime dependencies.

## Reproducibility Checklist

- Record the exact model names or local checkpoint filenames, scoring strategy, `--offset-idx`, `--mutation-col`, MSA path, and `--msa-samples`.
- Preserve the input DMS CSV and output CSV together; the example output appends one score column per model and retains the original columns.
- Use the same wild-type sequence string that mutation notation references after applying `offset_idx`.
- For MSA Transformer, record whether the MSA was A3M and how many sequences were sampled from the start of the file.
