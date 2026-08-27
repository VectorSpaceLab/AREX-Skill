# OpenFold Inference Troubleshooting

Use this reference when an inference command fails before, during, or after prediction. Keep environment setup, asset downloads, and low-level model internals routed to sibling sub-skills.

## Fast Triage

| Symptom | Likely cause | Fix or route |
| --- | --- | --- |
| `ModuleNotFoundError: attn_core_inplace_cuda` during CLI help or import | OpenFold's compiled extension is missing from the runtime import path. | Rebuild or reinstall OpenFold in the runtime environment; route build details to `../installation-assets/`. Use the bundled helper scripts meanwhile because they do not import OpenFold. |
| Parser reports missing `fasta_dir` or `template_mmcif_dir` | Required positional omitted. | Provide both positionals, even for SoloSeq/template-free workflows. |
| No alignments found under `--use_precomputed_alignments` | Root path points to the wrong directory or per-query subdirectory names do not match FASTA tags. | Validate with `scripts/validate_inference_inputs.py`; route layout conversion to `../data-preparation/`. |
| Multimer command uses PDB70/HHSearch only | Monomer template-search flags were copied into multimer planning. | Use PDB SeqRes with HMMSearch/HMBuild and include UniProt/UniRef30. |
| SoloSeq sequence is longer than 1022 residues | ESM-1b embedding limit. | Use MSA-based inference, split/redesign the task, or otherwise avoid SoloSeq truncation. |
| Checkpoint and `--config_preset` mismatch | Parameters do not match the model family. | Match AlphaFold JAX parameters to preset names or supply a compatible OpenFold checkpoint; route conversions to `../model-apis/`. |
| Optional kernel import error | DeepSpeed, cuEquivariance, FlashAttention, or TensorRT dependency is unavailable or incompatible. | Disable the optional flag or route backend readiness to `../installation-assets/` and internals to `../model-apis/`. |
| Relaxation fails after unrelaxed output exists | OpenMM/Amber dependency or structure-cleanup issue. | Re-run with `--skip_relaxation` to isolate model prediction; route install issues to `../installation-assets/`. |
| CPU inference is extremely slow | `--model_device` left as `cpu` or GPU unavailable. | Use `--model_device cuda:0` only after GPU/runtime validation. |

## Missing Parameters, Databases, or Binaries

Inference without `--use_precomputed_alignments` needs external databases and alignment binaries. Exact requirements depend on mode:

- Monomer: UniRef90, MGnify, PDB70, BFD and/or UniClust30 or UniRef30, plus JackHMMER, HHblits, HHSearch, and Kalign.
- Multimer: UniRef90, MGnify, PDB SeqRes, UniRef30, UniProt, BFD, plus JackHMMER, HHblits, HMMSearch, HMMBuild, and Kalign.
- SoloSeq with template generation: UniRef90, PDB70, JackHMMER, HHSearch, and Kalign.
- SoloSeq without templates: SoloSeq checkpoint and ESM embedding generation are primary; database/template flags can be intentionally absent.

Route missing paths, downloads, and binary installation to `../installation-assets/`. The inference helper scripts should never download assets or mutate environments.

## Preset and Weight Mismatches

| Preset family | Typical use | Weight guidance |
| --- | --- | --- |
| `model_1`, `model_2` | Monomer with templates, no pTM. | Use matching AlphaFold JAX parameter files or compatible OpenFold checkpoints. |
| `model_1_ptm`, `model_2_ptm` | Monomer with templates and pTM. | Use matching pTM parameters or compatible checkpoints. |
| `model_3`, `model_4`, `model_5` | Monomer without templates, no pTM. | Use matching no-template parameters or checkpoints. |
| `model_3_ptm`, `model_4_ptm`, `model_5_ptm` | Monomer without templates and pTM. | Use matching no-template pTM parameters or checkpoints. |
| `model_1_multimer_v3` | Multimer. | Use AlphaFold multimer parameters compatible with the multimer preset. |
| `seq_model_esm1b_ptm` | SoloSeq. | Provide the SoloSeq OpenFold checkpoint explicitly. |

When the user asks for checkpoint conversion or internal config validation, route to `../model-apis/`.

## Precomputed Alignment Layout Errors

`--use_precomputed_alignments` should point to the root directory containing per-query subdirectories, not directly to one alignment file.

Common monomer files:

- `uniref90_hits.sto`
- `mgnify_hits.sto`
- `bfd_uniclust_hits.a3m` or `bfd_uniref_hits.a3m`
- `hhsearch_output.hhr` or `pdb70_hits.hhr` when template hits are used

Common multimer layouts can include per-chain alignment directories and UniProt, HMMSearch, or PDB SeqRes-related files depending on the preparation pipeline. If the layout is nonstandard, validate what exists and route conversion to `../data-preparation/`.

For SoloSeq precomputed embeddings:

- The root still uses one subdirectory per FASTA record tag or file stem.
- Each subdirectory should contain an embedding artifact such as `.pt`, `.npy`, `.npz`, `.pkl`, or `.pickle`.
- Optional `*.hhr` files provide template hits.
- Absence of `*.hhr` means template-free SoloSeq only if that is intentional.

## Custom Template Failures

Failures with `--use_custom_template` usually come from template/query mismatch:

- Template chains should use chain ID `A`.
- Template chain length should match the query sequence length.
- The same `.cif` set is used for every query in the run.
- Per-query custom template selection requires separate runs or precomputed template-hit directories.

For one query sequence threaded onto one template chain, use `thread_sequence.py` instead of a broad custom-template run.

## Long-Sequence and Memory Failures

Symptoms include CUDA out-of-memory, slow chunk-size tuning, TensorRT sequence-length mismatch, or unstable attention kernels.

Try these in order:

1. Add `--long_sequence_inference`.
2. Use `--precision bf16` only when hardware/runtime support it; otherwise use `tf32` or `fp32`.
3. Disable FlashAttention-like config overrides for very long sequences.
4. Avoid `--trace_model` for one-off debugging; reserve it for repeated or batch inference.
5. Disable TensorRT or increase `--trt_max_sequence_len` when engines were built for shorter sequences.
6. Disable cuEquivariance or DeepSpeed flags if optional imports fail, then re-enable after backend validation.

## Relaxation and Output Problems

| Problem | Action |
| --- | --- |
| Relaxation crashes but unrelaxed PDB/ModelCIF exists | Re-run with `--skip_relaxation` to check whether model prediction is healthy. |
| Output is PDB but the user expected ModelCIF | Add `--cif_output`. |
| Raw tensors/features are missing | Add `--save_outputs`, knowing output size increases. |
| pLDDT appears inverted in B-factor fields | Check whether `--subtract_plddt` was used. |
| Output filenames collide across comparisons | Use `--output_postfix` or separate `--output_dir` values. |

## Threading Failures

`thread_sequence.py` supports one query sequence and one template mmCIF file. If it fails:

- Confirm `input_fasta` has exactly one FASTA record.
- Confirm `input_mmcif` is a file, not a directory.
- Provide `--chain_id` when the template has multiple chains.
- Provide `--template_id` for traceable metadata.
- Provide a compatible parameter source via `--jax_param_path` or `--openfold_checkpoint_path`.

Route complexes or multiple query chains back to `run_pretrained_openfold.py` multimer planning.

## Safe Debugging Commands

These bundled helpers do not import or execute OpenFold:

```bash
python scripts/validate_inference_inputs.py run --mode soloseq --fasta-dir FASTA_DIR --template-mmcif-dir TEMPLATE_DIR --skip-templates
python scripts/build_inference_command.py run --mode multimer --fasta-dir FASTA_DIR --template-mmcif-dir TEMPLATE_DIR --output-dir OUT --pdb-seqres-database-path DB/pdb_seqres.txt --hmmsearch-binary-path BIN/hmmsearch --hmmbuild-binary-path BIN/hmmbuild
```

Use validation first to catch path and layout issues, then review the dry-run command before real prediction.
