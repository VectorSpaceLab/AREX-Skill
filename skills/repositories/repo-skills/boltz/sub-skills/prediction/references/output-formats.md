# Prediction Output Formats

## Directory Layout

A typical run writes:

```text
out_dir/
  lightning_logs/
  processed/
  predictions/
    input_stem/
      input_stem_model_0.cif
      confidence_input_stem_model_0.json
      plddt_input_stem_model_0.npz
      pae_input_stem_model_0.npz
      pde_input_stem_model_0.npz
      affinity_input_stem.json
```

Notes:

- `predictions/<input_stem>/` is one folder per input file stem.
- `processed/` contains serialized intermediate data for inference.
- Existing prediction folders are skipped unless `--override` is set.
- Structure files use `.cif` by default; `--output_format pdb` writes `.pdb` instead.
- With multiple diffusion samples, structure files are ranked by confidence as `<stem>_model_<rank>.cif` or `.pdb`.

## Structure Files

Default structure output:

```text
predictions/<stem>/<stem>_model_0.cif
```

Use `--output_format pdb` for PDB output:

```text
predictions/<stem>/<stem>_model_0.pdb
```

The written structure includes per-token pLDDT values when available. For affinity-enabled Boltz-2 records, Boltz may also write `pre_affinity_<stem>.npz` for the affinity pass.

## Confidence JSON

Example file name:

```text
confidence_<stem>_model_0.json
```

Common fields:

- `confidence_score` — aggregate ranking score; higher is better. Boltz uses this to sort diffusion samples.
- `ptm` — predicted TM score for the structure/complex; range `[0, 1]`, higher is better.
- `iptm` — interface predicted TM score; range `[0, 1]`, higher is better.
- `ligand_iptm` — interface score for protein-ligand interfaces.
- `protein_iptm` — interface score for protein-protein interfaces.
- `complex_plddt` — average pLDDT for the complex; range `[0, 1]`, higher is better.
- `complex_iplddt` — interface-weighted pLDDT; range `[0, 1]`, higher is better.
- `complex_pde` — average predicted distance error in Å; lower is better.
- `complex_ipde` — interface-focused PDE in Å; lower is better.
- `chains_ptm` — per-chain predicted TM-like scores.
- `pair_chains_iptm` — pairwise chain interface scores.

Interpret confidence cautiously:

- Compare samples from the same input and settings before comparing unrelated complexes.
- For interfaces and ligands, inspect `iptm`, `ligand_iptm`, `complex_iplddt`, and `complex_ipde`, not only global `confidence_score`.
- Low confidence can indicate inadequate MSA depth, bad chain definitions, unconstrained flexible regions, unsupported chemistry, or incompatible templates/constraints.

## NPZ Side Outputs

Boltz can write compressed NumPy arrays:

- `plddt_<stem>_model_<rank>.npz` — per-token pLDDT.
- `pae_<stem>_model_<rank>.npz` — predicted aligned error matrix when PAE is emitted.
- `pde_<stem>_model_<rank>.npz` — predicted distance error matrix when PDE is emitted.
- `embeddings_<stem>.npz` — single and pair embeddings when `--write_embeddings` is enabled.

Use `--write_full_pae`, `--write_full_pde`, and `--write_embeddings` only when downstream analysis needs the arrays because they increase output size.

## Affinity JSON

Example file name:

```text
affinity_<stem>.json
```

Fields:

- `affinity_pred_value` — ensemble affinity value reported as `log10(IC50)` with IC50 in µM; lower is stronger among active binders.
- `affinity_probability_binary` — binder-vs-decoy probability in `[0, 1]`; higher is more likely a binder.
- `affinity_pred_value1`, `affinity_pred_value2` — individual ensemble heads when present.
- `affinity_probability_binary1`, `affinity_probability_binary2` — individual binary-probability heads when present.

Use cases:

- Use `affinity_probability_binary` for hit-discovery or binder-vs-decoy triage.
- Use `affinity_pred_value` for comparing related active molecules during hit-to-lead or lead optimization.
- Do not compare `affinity_pred_value` as a general activity classifier for inactive molecules.
- Convert affinity value `y` to an approximate pIC50-like kcal/mol value with `(6 - y) * 1.364` when that representation is requested.

## Quick Output Checks

After a successful run:

```bash
find predictions -maxdepth 3 -type f | sort
python -m json.tool predictions/input_stem/confidence_input_stem_model_0.json
python -m json.tool predictions/input_stem/affinity_input_stem.json
```

Red flags:

- No folder under `predictions/` for the input stem: preprocessing may have failed or an existing folder was skipped.
- `Number of failed examples` is nonzero: inspect logs and target-specific outputs.
- Missing `affinity_<stem>.json` despite affinity YAML: the affinity target may have been skipped due to existing output, invalid binder, or no affinity property in the parsed record.
