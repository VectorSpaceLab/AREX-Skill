# Structure-Prediction Troubleshooting

Use this reference before escalating to downloads, environment changes, or GPU execution. Most failures in HelixFold-family workflows are missing prerequisites, incompatible GPU/Paddle stacks, invalid inputs, or under-planned resource use.

## Malformed Entity JSON

Symptoms:

- JSON parser errors.
- Schema validation errors before MSA generation.
- Missing `entities`, unsupported `type`, absent `sequence`, absent ligand `ccd`/`smiles`, or invalid `count`.
- Modification errors such as out-of-range `index` or unsupported modification `type`.

Actions:

1. Run `python scripts/validate_helixfold3_input.py input.json --mode helixfold3` or `--mode helixfold-s1`.
2. Confirm polymer sequences are non-empty and counts are positive integers.
3. For ligands, provide exactly one of `ccd` or `smiles`; do not provide both.
4. For residue modifications, use 1-based indices and verify that the CCD code is intended for the replacement residue.
5. For S1, ensure `job_name` exists and that the expanded entity count is at least two chains.
6. For S1 interface sampling, ensure `s1_sample_constraint` uses different `left_entity`/`right_entity` values in `<entity>-<copy>` format and does not exceed 10 entries.

## Missing MSA Binaries

Symptoms:

- `jackhmmer`, `hhblits`, `hhsearch`, `kalign`, `hmmsearch`, `hmmbuild`, `nhmmer`, or `mmseqs`/ColabFold tools are not found.
- MSA stage fails before features are written.
- S1 output contains `job_status.json` with a featurization failure.

Actions:

- Ask the user where the MSA binaries are installed; do not guess private environment paths.
- Check command arguments point to executable files, not only a directory.
- Keep HelixFold3 and S1’s MSA/tool environment separate from the model Python environment when the user’s setup uses two environments.
- Do not install bioconda packages or mutate environments without approval.

## Missing Databases or Checkpoints

Symptoms:

- Required `--*_database_path` arguments point to absent files.
- Reduced database preset fails because the small BFD path is missing.
- Template search fails because `template_mmcif_dir` or `obsolete_pdbs_path` is missing.
- `FileNotFoundError` for `.pdparams`, CCD preprocessing, `params_<model>.pdparams`, or `params_<model>.npz`.

Actions:

1. Check exact file paths in the planned command.
2. Confirm that the selected `--preset` matches the provided database set.
3. For HelixFold3/S1, confirm the CCD preprocessed file is present.
4. For HelixFold, confirm `--data_dir/params/params_<model_name>.pdparams` or `.npz` exists.
5. Ask before downloading anything. Documented reduced database downloads are very large, and full DB support for HelixFold3/S1 is documented as unavailable in the README snapshot.

## CUDA, Paddle, and Optional Dependency Mismatch

Symptoms:

- `ModuleNotFoundError: paddle`, `pgl`, `openmm`, `pdbfixer`, `ml_collections`, `Bio`, or `jsonschema`.
- Paddle wheel imports but cannot see a GPU.
- Distributed launch errors or assertions that Paddle is not compiled with distributed support.
- CUDA/CuDNN/NCCL runtime errors at model load or first prediction.

Actions:

- Match PaddlePaddle GPU wheel to Python and CUDA version. HelixFold3/S1 docs use Python 3.10 and Paddle 3.1.0; classic HelixFold and HelixFold-Single docs use older Python/Paddle dev stacks.
- Install `ppfleetx` only when the user is planning BP/DAP/distributed HelixFold modes.
- HelixFold relaxation needs OpenMM/PDBFixer; use `--disable_amber_relax` only when the user accepts unrelaxed output.
- Do not claim the lightweight PaddleHelix inspection environment is sufficient for structure inference; it was prepared only for source/package inspection. PaddlePaddle GPU, `pgl`, RDKit, OpenMM/PDBFixer, MSA tools, databases, and checkpoints remain optional workflow dependencies to check separately.

## Unsupported `bf16` or AMP Mode

Symptoms:

- Runtime errors when using `--precision bf16`.
- V100-class GPU request with `bf16`.
- HelixFold3 entrypoint raises that `bf16` AMP level `O2` is not supported.

Actions:

- Use `--precision fp32` for V100-class GPUs or unknown hardware.
- Use `bf16` only after confirming A100/H100-class support and a compatible Paddle build.
- Keep `--amp_level O1` unless the workflow docs and code support another setting.
- For resource-safe planning, first reduce `--infer_times` and `--diff_batch_size` before considering deeper config edits.

## Token and Memory Limits

Symptoms:

- Out-of-memory during feature processing or inference.
- Long multimodal inputs fail even when protein-only examples fit.
- Large nucleic-acid or ligand-heavy inputs use more memory than token count alone suggests.

Actions:

1. Use the validator token summary to estimate expanded polymer tokens.
2. For A100-40G with `bf16`, treat about 1200 tokens as the documented HelixFold3 planning ceiling.
3. For V100-32G with `fp32`, treat about 1000 tokens as the documented HelixFold3 planning ceiling.
4. Reduce `infer_times`, `diff_batch_size`, recycle count, or subbatch size where the chosen workflow exposes those controls.
5. Split or simplify inputs only if doing so preserves the biological question; do not silently change stoichiometry.

## Output Interpretation Problems

Symptoms:

- User cannot find final structures.
- User sees many prediction folders and is unsure which one to use.
- Confidence metric JSON appears different between versions.

Actions:

- HelixFold3 final ranked outputs are under `<output_dir>/<input-stem>/<input-stem>-rank*`; top rank is `rank1` or the lowest rank index depending on the workflow’s naming convention.
- HelixFold-S1 final structures are under `module2/`, with interface outputs under `interface_infos/` and chain mapping in `chain_id_mapping.csv`.
- Classic HelixFold top ranked PDB is `ranked_0.pdb`; `ranking_debug.json` records order and pLDDT scores.
- HelixFold-Single writes only `unrelaxed.pdb` unless the user adds downstream relaxation.
- Treat `all_results.json`, `ranking_debug.json`, and `timings.json` as diagnostics; do not overwrite them when post-processing.

## Unsafe or Out-of-Scope Requests

Decline or pause for explicit user approval when a request asks to:

- Run `download_all_data.sh`, checkpoint download scripts, training scripts, or GPU inference launchers.
- Install GPU Paddle wheels, conda packages, MSA tools, OpenMM, or PPFleetX into an existing environment.
- Use server/API outputs for commercial purposes without confirming license/commercial access.
- Route compound docking to HelixFold structure prediction; use `../compound-drug-discovery/SKILL.md` instead.
- Treat protein sequence classification/function-prediction work as a structure task; use `../protein-sequence-function/SKILL.md` instead.

## Evidence Labels

This reference distills failure modes from HelixFold3, HelixFold-S1, HelixFold, and HelixFold-Single README files, launchers, parser arguments, output writers, and the private inspection environment handoff.
