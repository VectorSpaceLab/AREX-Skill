# Output interpretation and validation reference

Use this reference to inspect an existing ColabFold result directory without reopening source code or notebooks.

## Common output files

A normal prediction result directory can contain:

- Ranked structure files: `<job>_unrelaxed_rank_001_<model_tag>.pdb` and, when relaxation was enabled, `<job>_relaxed_rank_001_<model_tag>.pdb`.
- Per-model score JSON: `<job>_scores_rank_001_<model_tag>.json`.
- PAE JSON: `<job>_predicted_aligned_error_v1.json` unless PAE JSON output was skipped or the model did not expose PAE.
- Plot PNGs: `<job>_coverage.png`, `<job>_pae.png`, `<job>_plddt.png`, and optionally `<job>_ext_metrics.png`.
- Run configuration: `config.json`.
- Citations: `cite.bibtex`.
- AF3 JSON-only export: `<job>.json` when the workflow requested AlphaFold3 JSON output instead of structure prediction.

The exact number of model files depends on `--num-models`, `--num-seeds`, ranking, skipped output types, and relaxation settings.

## Naming patterns

Important substrings:

- `unrelaxed`: structure emitted directly from prediction.
- `relaxed`: structure after Amber/OpenMM relaxation.
- `rank_001`, `rank_002`, ...: rank after the configured ranking metric is applied.
- `alphafold2_ptm`, `alphafold2_multimer_v*`, `deepfold_v1`: model family encoded in the file tag.
- `model_1`, `model_2`, ... and `seed_000`, ...: model/seed components.

Do not infer biological quality from rank alone. Rank reflects the selected model confidence metric, not experimental validation.

## Score JSON keys

Per-model score JSON commonly includes:

- `plddt`: per-residue pLDDT values, rounded for easier use.
- `ptm`: predicted TM-score summary, present for pTM-capable models.
- `iptm`: interface pTM, usually for complexes/multimer-capable predictions.
- `pae`: predicted aligned error matrix, when available and not skipped.
- `max_pae`: maximum PAE value paired with `pae`.
- `pairwise_actifptm`, `pairwise_iptm`, `per_chain_ptm`, `actifptm`: optional extra interface metrics when extra pTM calculation was enabled.

Validation checks:

- `plddt` should be a non-empty list of numbers, usually in the 0-100 range.
- `pae`, when present, should be a square matrix with the same length as `plddt`.
- `ptm`, `iptm`, and extra pTM metrics should be treated as unavailable rather than zero if their keys are absent.
- For complexes, missing `iptm` may indicate a monomer model, single-chain input, or disabled/unavailable multimer scoring.

## Confidence interpretation

pLDDT:

- Stored in score JSON as `plddt` and in output PDB B-factors.
- Higher is better. Use it for local residue-level confidence.
- Be careful in molecular replacement and crystallographic workflows: the PDB B-factor column is confidence, not a physical temperature factor.
- A low-confidence flexible tail can coexist with a high-confidence structured core.

PAE:

- Low PAE between two residue blocks means the relative placement of those residues is predicted more confidently.
- High PAE between domains or chains can indicate uncertain relative orientation even when each domain has good pLDDT.
- Missing PAE plots do not necessarily mean missing PAE data; check score JSON and PAE JSON before re-running prediction.

pTM and ipTM:

- pTM summarizes predicted global fold agreement.
- ipTM summarizes predicted interface confidence for complexes.
- ColabFold can rank by `plddt`, `ptm`, `iptm`, or a multimer metric; `auto` chooses a context-appropriate metric.
- For complexes, inspect both pLDDT and interface metrics; high chain confidence does not guarantee a correct interface.

Extra pTM/interface metrics:

- `pairwise_actifptm` and `pairwise_iptm` help compare chain-pair interfaces.
- `per_chain_ptm` helps identify weak chains in a larger complex.
- `<job>_ext_metrics.png` is expected only when extra pTM metrics were calculated and plotting was not skipped.

## Plot files

Expected plot meanings:

- `<job>_coverage.png`: MSA sequence coverage; missing if MSA/plot output was skipped or input was not MSA-backed.
- `<job>_pae.png`: PAE heatmap across ranked models; missing if PAE is unavailable or plot output was skipped.
- `<job>_plddt.png`: per-residue pLDDT plot across ranked models; missing if plot output was skipped.
- `<job>_ext_metrics.png`: chain/interface pTM metric plot; only expected for extra pTM workflows.

If `config.json` contains skipped output settings or AF3 JSON-only intent, do not flag missing structure plots as a prediction failure.

## mmCIF and PDB handling

Post-output structure handling can include PDB and mmCIF files:

- ColabFold prediction structure outputs are typically PDB files.
- Template/input conversion utilities can create mmCIF and validate required fields such as `_entity_poly_seq.mon_id` and revision date metadata.
- When validating mixed directories, treat `.pdb` and `.cif` as structure-like outputs but do not assume every `.cif` is a ranked prediction output.

The bundled inspector reports PDB/CIF counts separately and classifies relaxed vs unrelaxed PDBs by file name.

## Citations

`cite.bibtex` should be present for completed prediction outputs unless citation writing was skipped or the run failed before finalization. Inspect it for evidence of method coverage:

- OpenMM citation appears when Amber relaxation was used.
- AlphaFold/AlphaFold-Multimer/DeepFold citations depend on model type.
- MMseqs/database/template citations depend on MSA, environmental database, and template usage.

Do not fabricate citations. If `cite.bibtex` is missing, report it as missing and reconstruct only from known run settings if those settings are available.

## Output validation checklist

1. Confirm the directory exists and is readable.
2. Count structure files: ranked unrelaxed PDBs, ranked relaxed PDBs, and any mmCIF files.
3. Parse score JSON files and verify `plddt` lists plus PAE matrix shape when `pae` is present.
4. Check for `config.json` and use it to explain intentional missing outputs such as skipped plots or PAE JSON.
5. Check for PAE, pLDDT, coverage, and extra metric PNGs; distinguish missing plots from missing score data.
6. Check `cite.bibtex` and note whether Amber/OpenMM citation is expected.
7. For relaxation requests, ensure source PDBs exist before invoking `colabfold_relax`.

## Example validation commands

Human-readable summary:

```bash
python scripts/inspect_colabfold_outputs.py results_dir
```

Machine-readable summary with warning exit code:

```bash
python scripts/inspect_colabfold_outputs.py results_dir --json --warn-exit-code
```

The validator is deliberately conservative. It warns about suspicious or missing post-processing artifacts but does not decide whether the scientific result is valid.
