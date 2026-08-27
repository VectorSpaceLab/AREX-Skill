# Troubleshooting

## First Questions

1. Did the user ask to run inference or only build/validate a command? If only planning, use `scripts/build_protenix_pred_command.py` and do not run `protenix pred`.
2. Does `protenix --help` work? If not, diagnose installation, environment activation, or wrong package version.
3. Does `protenix pred --help` show the expected flags? If not, the installed package may be stale or a different command is on `PATH`.
4. Does the model support the requested features? Template and RNA MSA require `protenix-v2`, `protenix_base_default_v1.0.0`, or `protenix_base_20250630_v1.0.0`.
5. Are booleans passed as explicit values? `protenix pred --use_template true` is correct; bare `--use_template` is not.
6. Did the command reach cache/checkpoint download, preprocessing search, or CUDA model execution? The failure level determines the route.

## CLI Missing or Wrong Version

Symptoms:

```text
protenix: command not found
No such command 'pred'
Error: No such option: --use_rna_msa
```

Actions:

- Verify the active Python environment contains the `protenix` distribution expected by the user.
- Check `protenix --help` and `protenix pred --help` before proposing a long command.
- Preserve the verified package fact that the distribution may expose version `2.0.0`; if help output disagrees with this skill, trust the installed help for that runtime and note a version mismatch.
- Use only registered short commands: `pred`, `json`, `msa`, `mt`, `prep`.

## Bool Flag Values

Symptoms:

```text
Error: Option '--use_template' requires an argument.
Unexpected behavior after wrapper generated '--use_msa False'
```

Actions:

- Pass explicit lowercase values in generated shell commands: `true` or `false`.
- Keep value pairs adjacent, especially when commands are generated through YAML, Python, or shell variables.
- Remember that `protenix json --include_discont_poly_poly_bonds` is a separate bare flag and does not follow the `pred` boolean pattern.

## Avoiding Accidental Expensive Inference

`protenix pred --help` is safe. `protenix pred ...` is not a dry run: it can download cache/checkpoint files, run preprocessing searches, initialize a model, and execute inference.

For no-run command construction:

```bash
python sub-skills/cli-and-inference/scripts/build_protenix_pred_command.py \
  --input input.json \
  --out-dir output \
  --model-name protenix-v2 \
  --use-rna-msa true \
  --use-template true \
  --trimul-kernel torch \
  --triatt-kernel torch \
  --print-warnings
```

If a user accidentally launched inference, tell them to interrupt the process and inspect whether partial files were created under the chosen `--out_dir` and runtime cache root.

## Missing Checkpoints, Cache, or `PROTENIX_ROOT_DIR`

Symptoms:

```text
Given checkpoint path not exist [...]
Downloading model checkpoint ...
Downloading data cache ...
Permission denied while writing cache/checkpoint
```

What Protenix expects:

- The runtime environment variable `PROTENIX_ROOT_DIR`, when set, points to the data root used for cache and checkpoint lookup.
- Checkpoints live under the runtime root's `checkpoint` directory.
- Missing cache/checkpoint files may be downloaded automatically before prediction.
- Template metadata caches may be needed when templates are enabled.
- ESM/ISM models may require extra ESM checkpoint files.

Actions:

1. Ask the user where their runtime data root should be.
2. Have them set `PROTENIX_ROOT_DIR` before running `protenix pred`.
3. Ensure the runtime process can write to the root if downloads are expected.
4. If the environment is offline, the user must pre-stage checkpoints/cache files for the selected model.
5. Do not publish or hard-code local cache paths in skill content.

## Missing MSA, Template, or RNA Paths

Symptoms:

```text
Using templates for inference...
Using RNA MSA for inference...
kalign/hmmsearch/hmmbuild/nhmmer/hmmalign not found
seqres or RNA database path missing
```

Interpretation:

- `--use_msa true` can trigger protein MSA update/search behavior.
- `--use_template true` requires a supported model and either usable template feature paths in JSON or external search tools/databases.
- `--use_rna_msa true` requires a supported model and either usable RNA MSA paths in JSON or RNA search tools/databases.

Actions:

- For command shape, include explicit binary/database path flags when the user supplies them.
- For database layout, installation, or preprocessing strategy, route to `../../msa-template-and-prep/SKILL.md`.
- For JSON fields such as template paths, RNA MSA path fields, and entity-level feature references, route to `../../input-data-and-features/SKILL.md`.

## External Tool Path Confusion

Prediction exposes these path options:

| Option | Use |
| --- | --- |
| `--kalign_binary_path` | Alignment helper used around template/RNA workflows. |
| `--hmmsearch_binary_path` | Template search. |
| `--hmmbuild_binary_path` | Template search and RNA fallback. |
| `--seqres_database_path` | Template search database. |
| `--nhmmer_binary_path` | RNA MSA search. |
| `--hmmalign_binary_path` | RNA MSA alignment. |
| `--hmmbuild_rna_binary_path` | RNA-specific HMM build path. |
| `--ntrna_database_path` | NT-RNA database. |
| `--rfam_database_path` | Rfam database. |
| `--rna_central_database_path` | RNAcentral database. |
| `--nhmmer_n_cpu` | CPU count for RNA MSA search. |

Do not guess these paths. Use placeholders only in generic examples and ask the user for runtime values before issuing a runnable command.

## CUDA and Kernel Failures

Symptoms:

```text
Invalid trimul_kernel. Options: 'cuequivariance', 'torch'.
Invalid triatt_kernel. Options: 'triattention', 'cuequivariance', 'deepspeed', 'torch'.
CUTLASS_PATH environment variable ...
CUDA extension compile error
fast_layernorm JIT compile failure
out of memory
```

Actions at this sub-skill level:

1. Rebuild the command with portable kernels: `--trimul_kernel torch --triatt_kernel torch`.
2. Consider `--dtype fp32` when diagnosing BF16/mixed-precision issues.
3. Keep `--enable_cache true --enable_fusion true --enable_tf32 true` for normal GPU runs, but disable one at a time only for focused debugging.
4. If `--triatt_kernel deepspeed` is requested, ensure the user understands it requires `CUTLASS_PATH` at runtime.
5. Route installation and backend internals to `../../advanced-model-configuration/SKILL.md`.

No-run fallback builder:

```bash
python sub-skills/cli-and-inference/scripts/build_protenix_pred_command.py \
  --input input.json \
  --out-dir output \
  --dtype fp32 \
  --trimul-kernel torch \
  --triatt-kernel torch \
  --print-warnings
```

## Output Directory Surprises

Symptoms:

```text
No CIF files directly under output/
ERR directory exists
Multiple nested folders appeared
```

Actions:

- Look under `OUT/<dataset_name>/<sample_name>/seed_<seed>/predictions/` for CIF and summary confidence files.
- If `--input` was a directory, expect multiple JSON jobs and nested output subtrees.
- If `--need_atom_confidence true`, expect additional `full_data` confidence JSON files.
- Choose a fresh `--out_dir` for debugging to avoid confusing old and new prediction files.
- See `output-layout.md` for the current dumper structure.

## Model/Version Feature Mismatch

Symptoms:

```text
Only protenix_base_default_v1.0.0, protenix_base_20250630_v1.0.0 and protenix-v2 supports template inference.
Only protenix_base_default_v1.0.0, protenix_base_20250630_v1.0.0 and protenix-v2 supports RNA MSA inference.
```

Fix:

- Switch to a supported model for template/RNA MSA: `protenix-v2`, `protenix_base_default_v1.0.0`, or `protenix_base_20250630_v1.0.0`.
- If the user must keep a v0.5, mini, or tiny model, set `--use_template false --use_rna_msa false` and route any feature-preparation questions to the preprocessing/input sub-skills.

## Two Common Diagnosis Patterns

### Protein/RNA complex with template, seeds from JSON, and fallback kernels

Use the builder, not `protenix pred`, while planning:

```bash
python sub-skills/cli-and-inference/scripts/build_protenix_pred_command.py \
  --input complex.json \
  --out-dir output \
  --model-name protenix_base_default_v1.0.0 \
  --use-rna-msa true \
  --use-template true \
  --use-seeds-in-json true \
  --trimul-kernel torch \
  --triatt-kernel torch \
  --print-warnings
```

Expected warnings should mention template/RNA prerequisites if binary/database paths were not supplied.

### Missing checkpoints plus CUDA kernel errors

Separate the issues:

1. Cache/checkpoint issue: set or fix runtime `PROTENIX_ROOT_DIR`, permissions, and offline checkpoint staging.
2. Kernel issue: rebuild a fallback command with `--trimul_kernel torch --triatt_kernel torch --dtype fp32`.
3. Route deep CUDA/CUTLASS/cuEquivariance/layernorm debugging to `../../advanced-model-configuration/SKILL.md`.
