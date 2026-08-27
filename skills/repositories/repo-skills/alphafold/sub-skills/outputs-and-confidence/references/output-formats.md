# AlphaFold Output Formats

This reference summarizes the files created by the public AlphaFold 2.3.2 `run_alphafold` prediction workflow. Use it to inspect completed or partially completed target directories without rerunning inference.

## Target Directory Layout

`run_alphafold` writes one target directory for each FASTA basename under the configured output directory.

| Path pattern | Meaning | Notes |
| --- | --- | --- |
| `msas/` | MSA and template-search intermediate files | Created before model inference; reused only when `use_precomputed_msas` is intentionally enabled by the prediction workflow. |
| `features.pkl` | Pickled feature dictionary from the data pipeline | Appears after successful feature generation; may exist even if model inference later fails. |
| `result_<model>.pkl` | Pickled full model prediction result | Contains arrays such as `plddt`, structure-module outputs, and, for pTM/multimer models, PAE/pTM/ipTM fields. |
| `confidence_<model>.json` | Per-residue pLDDT JSON for one model | Written from the model result `plddt` array. |
| `pae_<model>.json` | Predicted aligned error JSON for one model | Written only when `predicted_aligned_error` and `max_predicted_aligned_error` are present. Monomer models without the pTM head may not emit PAE. |
| `unrelaxed_<model>.pdb` | PDB created before Amber relaxation | B-factors contain per-atom copies of the residue pLDDT. |
| `unrelaxed_<model>.cif` | mmCIF created before Amber relaxation | Saved for each unrelaxed model. |
| `relaxed_<model>.pdb` | PDB after Amber relaxation | Present only for models selected by `models_to_relax`. |
| `relaxed_<model>.cif` | mmCIF after Amber relaxation | Present only for relaxed models. |
| `ranked_<n>.pdb` | Rank-ordered structure where `0` is best | Uses the relaxed structure when available, otherwise the unrelaxed structure. |
| `ranked_<n>.cif` | mmCIF counterpart of each ranked PDB | Saved from the same relaxed or unrelaxed structure selected for `ranked_<n>.pdb`. |
| `ranking_debug.json` | Ranking scores and model order | Key is `plddts` for pLDDT ranking or `iptm+ptm` for multimer-style ranking. |
| `timings.json` | Runtime timings per pipeline/model stage | Includes feature, process, predict, benchmark, and relax timings when those stages ran. |
| `relax_metrics.json` | Relaxation metrics by relaxed model | Present only when one or more models were relaxed. |

## Ranking Semantics

- `ranking_debug.json` contains `order`, a list of model names in best-to-worst order.
- `ranked_0.pdb` and `ranked_0.cif` correspond to the first model in `order`; `ranked_1.*` corresponds to the second, and so on.
- Monomer-style runs rank by mean pLDDT and store scores under `plddts`.
- Multimer-style runs rank by a combined interface/global confidence score and store scores under `iptm+ptm` when `iptm` is available in model results.
- A ranked file may be relaxed or unrelaxed. Check whether the model name from `order` also has `relaxed_<model>.pdb`; if it does not, `ranked_<n>.pdb` was copied from `unrelaxed_<model>.pdb`.

## Confidence Files

### `confidence_<model>.json`

The confidence JSON contains three parallel arrays:

- `residueNumber`: 1-based residue indices.
- `confidenceScore`: per-residue pLDDT values rounded to two decimal places.
- `confidenceCategory`: one-letter categories derived from pLDDT.

pLDDT categories are:

| Category | pLDDT range | Interpretation |
| --- | --- | --- |
| `D` | `0 <= score < 50` | Very low confidence; often disordered or unreliable local structure. |
| `L` | `50 <= score < 70` | Low confidence. |
| `M` | `70 <= score < 90` | Medium confidence. |
| `H` | `90 <= score <= 100` | High confidence local structure. |

pLDDT describes local residue-level confidence. It should not be used alone to judge relative domain placement in multi-domain proteins or complexes.

### `pae_<model>.json`

The PAE JSON is a list with one object:

- `predicted_aligned_error`: square `N x N` matrix of expected aligned errors rounded to one decimal place.
- `max_predicted_aligned_error`: maximum possible PAE value for that prediction head.

Low PAE between two residue ranges suggests confident relative placement between those ranges. High PAE between domains can indicate flexible, uncertain, or incorrectly placed domain orientation even when local pLDDT is high.

## Structure Files

- AlphaFold writes PDB files with pLDDT in the B-factor field when structures are assembled from predictions.
- PDB output supports at most 62 chains because AlphaFold maps chain indices to single-character PDB chain IDs.
- mmCIF output is better suited for many-chain structures because chain IDs are encoded without the same single-character limit.
- mmCIF conversion fills missing residue indices with `UNK` in `_entity_poly_seq` to preserve residue numbering.
- Parsing a ground-truth PDB/mmCIF through AlphaFold's `Protein` representation converts non-standard residues to `UNK` and ignores non-standard atoms.

## Partial-Run Triage

Use missing files to infer where a run stopped:

| Present files | Likely stage reached | Next diagnostic route |
| --- | --- | --- |
| Target directory and `msas/` only | Directory creation or MSA stage started | `prediction-cli` for command/data-pipeline flags; `input-data-and-formats` for FASTA/MSA issues. |
| `features.pkl` but no `result_<model>.pkl` | Feature pipeline succeeded; model processing/prediction failed | `model-config-and-api` for JAX/model/parameter issues. |
| `result_<model>.pkl` and confidence JSON but no ranked files | Model prediction succeeded; structure assembly, relaxation, or final writing failed | This sub-skill for structure writing; `relaxation` when relaxation was enabled. |
| Ranked files but no relaxed files | Expected if `models_to_relax=none` or model was not selected for relaxation | `prediction-cli` for `models_to_relax`; `relaxation` for backend failures. |
| No PAE files | Expected for non-pTM outputs; suspicious only when pTM/multimer outputs were expected | `model-config-and-api` for preset selection. |

## Practical Inspection Checklist

1. List the target directory and confirm `ranking_debug.json`, `timings.json`, ranked structures, and per-model confidence files.
2. Open `ranking_debug.json` and map ranked indices to model names and ranking score type.
3. Summarize `confidence_<model>.json` pLDDT distribution by category and contiguous low-confidence spans.
4. Summarize `pae_<model>.json` matrix size and high-PAE blocks when PAE is present.
5. Inspect whether `ranked_0` came from a relaxed or unrelaxed model before reporting stereochemical expectations.
6. Treat AFDB/server output dialects separately from local `run_alphafold` output folders.
