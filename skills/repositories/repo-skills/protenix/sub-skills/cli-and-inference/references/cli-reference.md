# CLI Reference

## Installed Command Registry

The installed Protenix distribution exposes the console entry point `protenix` from the batch-inference CLI. The verified short commands are:

| Command | Purpose | This sub-skill's role |
| --- | --- | --- |
| `protenix pred` | Run prediction on a JSON file or a directory of `.json` inputs. | Build and debug prediction command shape. |
| `protenix json` | Convert PDB/CIF inputs to Protenix JSON. | Route schema/entity details to `../../input-data-and-features/SKILL.md`. |
| `protenix msa` | Generate protein MSA from JSON or FASTA. | Route search/database details to `../../msa-template-and-prep/SKILL.md`. |
| `protenix mt` | Run protein MSA plus template search. | Use for command awareness only; route details to preprocessing. |
| `protenix prep` | Run protein MSA, template search, and RNA MSA search. | Use for command awareness only; route details to preprocessing. |

Do not assume long command names such as `protenix predict`, `protenix tojson`, `protenix msatemplate`, or `protenix inputprep` are registered. Some docs use those words as descriptive names, but the installed command registry uses the short names above.

Safe help probes:

```bash
protenix --help
protenix pred --help
protenix json --help
protenix msa --help
protenix mt --help
protenix prep --help
```

## No-Run Command Builder

Use the bundled builder whenever a future agent must produce a prediction command without launching inference:

```bash
python sub-skills/cli-and-inference/scripts/build_protenix_pred_command.py \
  --input input.json \
  --out-dir output \
  --model-name protenix_base_default_v1.0.0 \
  --use-default-params true \
  --print-warnings
```

The builder:

- Does not import Protenix, PyTorch, CUDA libraries, or repository modules.
- Does not check/download checkpoints or cache files.
- Does not run `protenix pred`.
- Prints a shell-quoted command that can be copied to a runtime machine.
- Emits warnings for model/feature mismatches, possible missing search prerequisites, kernel requirements, and common command-shape surprises.

## Boolean Values

`protenix pred` Click options use `type=bool`; pass explicit values:

```bash
protenix pred --input input.json --use_template true --use_rna_msa false
```

Avoid treating prediction booleans as bare toggles. For example, do not write `--use_template` by itself. A separate conversion command exception is `protenix json --include_discont_poly_poly_bonds`, which is a bare flag and should not be followed by `true`.

## Conservative Prediction Command

```bash
protenix pred \
  --input input.json \
  --out_dir output \
  --model_name protenix_base_default_v1.0.0 \
  --use_default_params true \
  --seeds 101 \
  --sample 5
```

This can still be expensive: it initializes the runner, may download caches/checkpoints, preprocesses features, and runs model inference. For planning only, use the no-run builder instead.

## Fast Smoke-Test Shape

When the user explicitly wants a smaller runtime command, choose a mini/tiny model and make the custom step/cycle choice explicit:

```bash
protenix pred \
  --input input.json \
  --out_dir smoke_output \
  --model_name protenix_mini_default_v0.5.0 \
  --use_default_params false \
  --cycle 4 \
  --step 5 \
  --sample 1 \
  --seeds 101 \
  --trimul_kernel torch \
  --triatt_kernel torch
```

Do not combine `--use_default_params true` with a claim that custom `--cycle` or `--step` will be honored; Protenix resets those values for supported model families when defaults are enabled.

## Template and RNA MSA Command Shape

Template and RNA MSA support is available for `protenix-v2`, `protenix_base_default_v1.0.0`, and `protenix_base_20250630_v1.0.0`. If feature files are absent from the JSON, Protenix can attempt automatic search and may require external tools/databases:

```bash
protenix pred \
  --input complex.json \
  --out_dir output \
  --model_name protenix-v2 \
  --use_default_params true \
  --use_template true \
  --use_rna_msa true \
  --trimul_kernel torch \
  --triatt_kernel torch \
  --kalign_binary_path /path/to/kalign \
  --hmmsearch_binary_path /path/to/hmmsearch \
  --hmmbuild_binary_path /path/to/hmmbuild \
  --seqres_database_path /path/to/pdb_seqres.fasta \
  --nhmmer_binary_path /path/to/nhmmer \
  --hmmalign_binary_path /path/to/hmmalign \
  --ntrna_database_path /path/to/nt_rna.fasta \
  --rfam_database_path /path/to/rfam.fasta \
  --rna_central_database_path /path/to/rnacentral.fasta
```

Use placeholder paths only in public examples. Ask the user for their actual runtime paths before telling them to run the command.

## `protenix pred` Flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `-i`, `--input` | Required | Input JSON file or directory; directories are scanned for `.json` files. |
| `-o`, `--out_dir` | `./output` | Prediction output root and `ERR` root. |
| `-s`, `--seeds` | `101` | Comma-separated CLI seeds such as `101,102`. |
| `-c`, `--cycle` | `10` | Pairformer recycle cycle count when `--use_default_params false`. |
| `-p`, `--step` | `200` | Diffusion step count when `--use_default_params false`. |
| `-e`, `--sample` | `5` | Diffusion samples per structure per seed. |
| `-d`, `--dtype` | `bf16` | Inference dtype; common choices are `bf16` and `fp32`. |
| `-n`, `--model_name` | `protenix_base_default_v1.0.0` | Model checkpoint/config name. |
| `--use_msa` | `true` | Use protein MSA features; mini ESM/ISM force this false under default params. |
| `--use_default_params` | `false` | Apply model-family cycle/step defaults; see `model-selection.md`. |
| `--trimul_kernel` | `cuequivariance` | Triangle multiplicative kernel: `cuequivariance` or `torch`. |
| `--triatt_kernel` | `cuequivariance` | Triangle attention kernel: `triattention`, `cuequivariance`, `deepspeed`, or `torch`. |
| `--enable_cache` | `true` | Enable diffusion shared-variable cache. |
| `--enable_fusion` | `true` | Enable efficient diffusion transformer fusion. |
| `--enable_tf32` | `true` | Allow TF32 for FP32 matrix operations. |
| `--msa_server_mode` | `protenix` | Protein MSA search mode: `protenix` or `colabfold`. |
| `--use_template` | `false` | Use template features or automatic template search if required. |
| `--use_rna_msa` | `false` | Use RNA MSA features or automatic RNA MSA search if required. |
| `--use_seeds_in_json` | `false` | Prefer JSON `modelSeeds` over CLI `--seeds`. |
| `--need_atom_confidence` | `false` | Write full atom-level confidence JSON in addition to summary confidence. |
| `--kalign_binary_path` | `None` | Path to `kalign`; otherwise Protenix searches `PATH`. |
| `--use_tfg_guidance` | `false` | Toggle Training-Free Guidance; route internals to advanced configuration. |
| `--hmmsearch_binary_path` | `None` | Template-search `hmmsearch` path. |
| `--hmmbuild_binary_path` | `None` | Template-search HMM build path and RNA fallback. |
| `--seqres_database_path` | `None` | PDB SeqRes database path for template search. |
| `--nhmmer_binary_path` | `None` | RNA MSA `nhmmer` path. |
| `--hmmalign_binary_path` | `None` | RNA MSA `hmmalign` path. |
| `--hmmbuild_rna_binary_path` | `None` | RNA-specific `hmmbuild`; falls back to `--hmmbuild_binary_path` when omitted. |
| `--ntrna_database_path` | `None` | NT-RNA database path. |
| `--rfam_database_path` | `None` | Rfam database path. |
| `--rna_central_database_path` | `None` | RNAcentral database path. |
| `--nhmmer_n_cpu` | `None` | CPU count for `nhmmer`. |

## Related CLI Routing

Use these only as routing hints from this sub-skill:

```bash
protenix json --input structure.cif --out_dir json_out --altloc first
protenix msa --input input.json --out_dir msa_out --msa_server_mode protenix
protenix mt --input input.json --out_dir mt_out --seqres_database_path /path/to/pdb_seqres.fasta
protenix prep --input input.json --out_dir prep_out --ntrna_database_path /path/to/nt_rna.fasta
```

For JSON schema and entity details, route to `../../input-data-and-features/SKILL.md`. For MSA/template/RNA database preparation and search behavior, route to `../../msa-template-and-prep/SKILL.md`.
