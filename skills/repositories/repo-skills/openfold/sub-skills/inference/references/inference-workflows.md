# OpenFold Inference Workflows

Use this reference to turn a user request into a safe OpenFold inference plan. Assume model weights, sequence databases, external binaries, and runtime dependencies are already prepared; route acquisition and readiness checks to `../installation-assets/`.

## Decision Tree

| User intent | Use | Critical choices |
| --- | --- | --- |
| Predict one protein with conventional MSAs | `run_pretrained_openfold.py` monomer | Select a monomer preset such as `model_1_ptm`; provide database paths or `--use_precomputed_alignments`. |
| Predict a protein complex with AlphaFold-Multimer behavior | `run_pretrained_openfold.py` multimer | Use `model_1_multimer_v3`; use PDB SeqRes/HMMSearch/HMBuild plus UniProt/UniRef30. |
| Predict without conventional MSAs or from ESM embeddings | SoloSeq | Use `seq_model_esm1b_ptm`; provide a SoloSeq checkpoint; validate the 1022-residue limit. |
| Reuse existing MSA/template outputs | Precomputed alignments | Pass `--use_precomputed_alignments` and check one subdirectory per query tag. |
| Use all provided local `.cif` files as templates | Custom templates | Add `--use_custom_template`; require chain `A` and query/template length compatibility. |
| Fit a long protein or complex into memory | Long-sequence inference | Add `--long_sequence_inference`; choose conservative precision/backend flags. |
| Put one sequence onto one template chain | `thread_sequence.py` | Require exactly one FASTA record, one mmCIF file, `--template_id`, and `--chain_id`. |

## Safe Planning Procedure

1. Identify the mode: monomer, multimer, SoloSeq, precomputed alignments, custom template, long sequence, or threading.
2. Validate the input shape with `scripts/validate_inference_inputs.py` before building the command.
3. Build the dry-run command with `scripts/build_inference_command.py` and review it with the user.
4. Check whether parameters, databases, external binaries, GPU, OpenMM, TensorRT, DeepSpeed, or cuEquivariance are ready; route missing assets to `../installation-assets/`.
5. Check whether alignments or caches need to be produced; route production and conversion to `../data-preparation/`.
6. Ask before running real inference, because prediction can require large databases, model weights, GPU time, and relaxation dependencies.

## Monomer Inference

### Inputs

- `fasta_dir`: directory of query FASTA files. Each monomer file should usually contain one FASTA record.
- `template_mmcif_dir`: directory of template mmCIF files. It remains a required positional even for template-free or precomputed-template workflows.
- Parameters: either matching AlphaFold JAX `.npz` parameters via `--jax_param_path`, a compatible OpenFold checkpoint via `--openfold_checkpoint_path`, or a default resource path that the OpenFold script can derive from `--config_preset`.
- Alignments: either generated during inference from databases/binaries or supplied via `--use_precomputed_alignments`.

### Preset and Template Choices

- `model_1` and `model_2` are monomer template presets without pTM.
- `model_1_ptm` and `model_2_ptm` are monomer template presets with pTM.
- `model_3`, `model_4`, and `model_5` are monomer no-template presets.
- `model_3_ptm`, `model_4_ptm`, and `model_5_ptm` are monomer no-template presets with pTM.
- For AlphaFold JAX parameters, keep parameter names aligned to the selected preset. For OpenFold checkpoints, confirm compatibility before running.

### Precomputed Alignment Layout

A typical monomer precomputed alignment root looks like this:

```text
ALIGNMENTS_DIR/
└── QUERY_TAG/
    ├── bfd_uniclust_hits.a3m        # or bfd_uniref_hits.a3m
    ├── mgnify_hits.sto
    ├── uniref90_hits.sto
    └── hhsearch_output.hhr          # or pdb70_hits.hhr when templates are used
```

The subdirectory name should match the FASTA record tag OpenFold derives from the header. If the FASTA filename and record ID differ, validate both possible names before assuming the layout is wrong.

### Outputs

OpenFold writes prediction artifacts under `--output_dir`:

- `alignments/` when alignments are generated during inference.
- Structure outputs under model-specific output directories, including unrelaxed files and relaxed files unless `--skip_relaxation` is set.
- Optional raw model output pickle files when `--save_outputs` is set.
- PDB by default, or ModelCIF when `--cif_output` is set.

## Multimer Inference

Use multimer when the user wants AlphaFold-Multimer behavior for protein complexes and has compatible multimer parameters and databases.

### Key Differences from Monomer

- Use a multimer preset such as `model_1_multimer_v3`.
- Template search uses PDB SeqRes with HMMSearch/HMBuild, not PDB70 with HHSearch.
- Include multimer sequence inputs such as UniProt and UniRef30 in addition to UniRef90, MGnify, BFD, and PDB SeqRes as required by the selected workflow.
- Documented multimer inference uses AlphaFold multimer parameter weights; do not plan an OpenFold checkpoint for multimer unless the user has a known compatible checkpoint and model API guidance.
- `--use_precomputed_alignments` remains valid when the multimer alignment layout is already prepared.

### Multimer Checklist

1. Confirm the FASTA represents a complex or multiple complexes.
2. Set `--config_preset model_1_multimer_v3` unless the user names another verified multimer preset.
3. Include `--pdb_seqres_database_path`, `--hmmsearch_binary_path`, and `--hmmbuild_binary_path` for template search when alignments are not precomputed.
4. Include `--uniprot_database_path` and `--uniref30_database_path` for multimer feature generation.
5. Avoid copying monomer-only PDB70/HHSearch template flags into the multimer command.
6. Route database date/version compatibility questions to `../installation-assets/`.

## SoloSeq / Single-Sequence Inference

SoloSeq predicts from ESM-1b sequence embeddings rather than conventional MSAs.

### Modes

| Mode | Command choice | Notes |
| --- | --- | --- |
| Precomputed embeddings | `--use_precomputed_alignments EMBEDDINGS_DIR` | Embedding subdirectories use the same per-query convention. Optional `*.hhr` files provide template hits. |
| On-the-fly embeddings without templates | Omit `--use_precomputed_alignments` and omit template database/tool flags intentionally | OpenFold generates ESM embeddings and performs template-free SoloSeq. |
| On-the-fly embeddings with templates | Provide UniRef90, PDB70, JackHMMER, HHSearch, and Kalign | Generates ESM embeddings plus HHSearch template information. |

### Guardrails

- Use `--config_preset seq_model_esm1b_ptm`.
- Provide `--openfold_checkpoint_path` for the SoloSeq OpenFold checkpoint.
- Validate every query sequence is at most 1022 residues; ESM-1b embedding generation truncates longer sequences, so reject or redesign long SoloSeq requests.
- If templates are skipped, still pass an existing `template_mmcif_dir` positional and explain that it is unused by that template-free mode.

## Custom Template Inference

Use `--use_custom_template` when the user wants OpenFold to treat all `.cif` files in `template_mmcif_dir` as local template input.

Planning constraints:

- Template chains should use chain ID `A` for the target chain.
- Template chain length should match the query sequence length.
- The same template collection is read for every sequence in the run.
- If different queries need different templates, plan separate runs or precomputed template-hit directories.
- If the user wants to thread exactly one sequence onto exactly one template chain, prefer `thread_sequence.py`.

## Long-Sequence and Memory-Constrained Inference

Use `--long_sequence_inference` when memory, not command syntax, is the likely blocker. This flag enables long-sequence-oriented config changes that trade runtime for lower memory.

Additional planning notes:

- Consider `--precision bf16` on compatible hardware; keep `tf32` as the conservative default for Ampere-class GPUs when no evidence supports BF16.
- Avoid FlashAttention-like config overrides for very long sequences unless the target environment has already validated them.
- Disable optional acceleration flags when their imports fail, then re-enable only after backend checks pass.
- Use `--experiment_config_json` for advanced chunking/offload overrides and route detailed config editing to `../model-apis/`.
- If TensorRT is used, ensure `--trt_max_sequence_len` covers the real sequence length and `--trt_engine_dir` is compatible with build/run mode.

## Threading Workflow

Use `thread_sequence.py` for one query sequence threaded onto one template mmCIF chain.

Checklist:

1. Confirm `input_fasta` contains exactly one FASTA record.
2. Confirm `input_mmcif` is one `.cif` or `.mmcif` file, not a directory.
3. Provide `--template_id` for traceable template metadata.
4. Provide `--chain_id` to avoid ambiguous template-chain selection.
5. Choose a compatible `--config_preset` and parameter source.
6. Set `--output_dir` explicitly.
7. Expect one unrelaxed PDB and, if relaxation succeeds, one relaxed PDB.

Do not use threading as a substitute for multimer prediction. Route multiple-chain query planning to multimer inference.

## Programmatic API Notes

OpenFold inference scripts call lower-level helpers such as model loading, model execution, output preparation, and relaxation utilities. For normal user workflows, prefer CLI planning because the scripts coordinate feature generation and output writing. Route direct model construction, config mutation, checkpoint conversion, tensor-shape debugging, and output object APIs to `../model-apis/`.
