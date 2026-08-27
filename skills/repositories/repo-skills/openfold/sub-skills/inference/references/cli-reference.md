# OpenFold Inference CLI Reference

This reference distills OpenFold inference command surfaces into reusable planning guidance. The bundled scripts in this sub-skill print or validate commands only; they do not download assets, import OpenFold model code, or run prediction.

## `run_pretrained_openfold.py`

Use `run_pretrained_openfold.py` for monomer, multimer, SoloSeq, precomputed-alignment, custom-template, and long-sequence prediction.

### Required Positionals

| Argument | Meaning | Planning guidance |
| --- | --- | --- |
| `fasta_dir` | Directory of `.fa` or `.fasta` query files. | OpenFold iterates files in this directory. For monomer and SoloSeq, prefer one sequence per file. For multimer, a file can encode all chains of a complex. |
| `template_mmcif_dir` | Directory of template mmCIF files. | Required as a positional even when templates are skipped or precomputed template hits are used. Use an existing empty directory only for intentionally template-free runs. |

### Core Flags

| Flag | Meaning | Planning guidance |
| --- | --- | --- |
| `--output_dir PATH` | Prediction output root. | Set explicitly; OpenFold also uses it for temporary FASTA files and generated alignments. |
| `--config_preset NAME` | Model preset from OpenFold config. | Common choices are `model_1`, `model_1_ptm`, `model_1_multimer_v3`, and `seq_model_esm1b_ptm`. |
| `--model_device DEVICE` | Torch device, such as `cpu` or `cuda:0`. | CPU is valid but slow. Confirm GPU readiness in `../installation-assets/` before promising GPU execution. |
| `--jax_param_path PATH` | AlphaFold JAX `.npz` parameter file. | If omitted with no OpenFold checkpoint, the script derives a default resource filename from the config preset. |
| `--openfold_checkpoint_path PATH` | OpenFold `.pt` checkpoint or DeepSpeed checkpoint directory. | Required for common SoloSeq examples and useful for OpenFold-trained weights. Do not use OpenFold checkpoints for documented multimer mode. |
| `--data_random_seed INT` | Data/random seed. | Use for reproducible command examples. |
| `--output_postfix TEXT` | Extra suffix in output filenames. | Useful for comparing presets, seeds, or acceleration options. |

### Alignment, Database, and Binary Flags

| Flag | Mode | Meaning |
| --- | --- | --- |
| `--use_precomputed_alignments DIR` | Monomer, multimer, SoloSeq | Skip alignment generation and read per-query alignment or embedding subdirectories. |
| `--uniref90_database_path PATH` | Monomer, multimer, SoloSeq template search | UniRef90 FASTA for JackHMMER. |
| `--mgnify_database_path PATH` | Monomer, multimer | MGnify FASTA. |
| `--pdb70_database_path PATH` | Monomer, SoloSeq templates | PDB70 database prefix for HHSearch. Do not substitute this for multimer template search. |
| `--pdb_seqres_database_path PATH` | Multimer | PDB SeqRes database for HMMSearch. |
| `--uniref30_database_path PATH` | Multimer, some full-database workflows | UniRef30 database prefix. |
| `--uniclust30_database_path PATH` | Monomer full database workflows | UniClust30 database prefix. |
| `--uniprot_database_path PATH` | Multimer | UniProt FASTA for multimer feature generation. |
| `--bfd_database_path PATH` | Monomer, multimer | BFD database prefix. |
| `--preset full_dbs|reduced_dbs` | Alignment planning | Describes database set size; still provide concrete paths needed by the workflow. |
| `--cpus INT` | Alignment generation | CPU threads for external alignment tools. |
| `--jackhmmer_binary_path PATH` | Monomer, multimer, SoloSeq templates | JackHMMER executable. |
| `--hhblits_binary_path PATH` | Monomer, multimer MSA generation | HHblits executable. |
| `--hhsearch_binary_path PATH` | Monomer, SoloSeq templates | HHSearch executable for PDB70 template search. |
| `--hmmsearch_binary_path PATH` | Multimer templates | HMMSearch executable for PDB SeqRes. |
| `--hmmbuild_binary_path PATH` | Multimer templates | HMMBuild executable used with HMMSearch. |
| `--kalign_binary_path PATH` | Templates, custom templates, threading | Kalign executable. |

### Template Metadata and Custom Templates

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--max_template_date YYYY-MM-DD` | Last allowed template release date. | Important for leakage-safe benchmarks. |
| `--obsolete_pdbs_path PATH` | Obsolete PDB mapping. | Optional metadata for template featurizers. |
| `--release_dates_path PATH` | PDB release dates. | Useful with strict template cutoffs. |
| `--use_custom_template` | Treat `.cif` files in `template_mmcif_dir` as custom templates. | Templates should use chain `A` for the target and match the query sequence length. The same template set applies to all queries in the run. |

### Output and Relaxation Flags

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--skip_relaxation` | Skip Amber/OpenMM relaxation. | Useful for fast debugging or when relaxation dependencies fail. |
| `--save_outputs` | Save raw model outputs. | Produces larger output artifacts for debugging or analysis. |
| `--cif_output` | Write ModelCIF instead of PDB. | Applies to unrelaxed and relaxed structure outputs. |
| `--subtract_plddt` | Store `100 - pLDDT` in B-factor fields. | Use only when downstream visualization expects this convention. |

### Acceleration and Memory Flags

| Flag | Meaning | Caveat |
| --- | --- | --- |
| `--precision tf32|fp32|fp16|bf16` | Numeric precision mode. | `tf32` is the script default. `bf16` can help memory on compatible hardware; `fp16` can be unstable. |
| `--long_sequence_inference` | Enable long-sequence memory-saving config options. | Trades speed for memory. Use for large proteins or complexes. |
| `--trace_model` | TorchScript tracing for repeated/batch inference. | Initial compilation can be slow and fixed-size prediction config is required. |
| `--experiment_config_json PATH` | Apply flattened config overrides from JSON. | Use for advanced chunking/offload/FlashAttention choices; route config construction to `../model-apis/`. |
| `--use_deepspeed_evoformer_attention` | DeepSpeed Evoformer attention kernel. | Requires compatible DeepSpeed/DS4Sci installation. |
| `--use_cuequivariance_attention` | cuEquivariance attention kernel. | Requires compatible cuEquivariance packages and hardware. |
| `--use_cuequivariance_multiplicative_update` | cuEquivariance triangle multiplicative update kernel. | Often paired with DeepSpeed fallback after backend validation. |
| `--trt_mode build|run` | TensorRT engine build or run mode. | Requires TensorRT setup and an engine directory. |
| `--trt_engine_dir PATH` | TensorRT `.onnx`/`.plan` directory. | Must be writable in build mode and compatible in run mode. |
| `--trt_max_sequence_len INT` | Maximum sequence length supported by TensorRT engines. | Default parser value is 640. |
| `--trt_num_profiles INT` | Number of TensorRT optimization profiles. | Documented values include 1, 2, and 4. |
| `--trt_optimization_level INT` | TensorRT optimization level. | Parser help documents values from 0 to 5. |

## Command Patterns

### Monomer with On-the-Fly Alignments

```bash
python run_pretrained_openfold.py \
  FASTA_DIR TEMPLATE_MMCIF_DIR \
  --output_dir OUTPUT_DIR \
  --config_preset model_1_ptm \
  --model_device cuda:0 \
  --uniref90_database_path DB/uniref90/uniref90.fasta \
  --mgnify_database_path DB/mgnify/mgy_clusters.fa \
  --pdb70_database_path DB/pdb70/pdb70 \
  --uniclust30_database_path DB/uniclust30/uniclust30 \
  --bfd_database_path DB/bfd/bfd_metaclust
```

Use explicit binary flags only when the runtime environment does not already expose JackHMMER, HHblits, HHSearch, and Kalign at the expected paths.

### Monomer with Precomputed Alignments

```bash
python run_pretrained_openfold.py \
  FASTA_DIR TEMPLATE_MMCIF_DIR \
  --output_dir OUTPUT_DIR \
  --config_preset model_1_ptm \
  --model_device cuda:0 \
  --use_precomputed_alignments ALIGNMENTS_DIR
```

For a typical monomer, `ALIGNMENTS_DIR` contains one subdirectory per query tag with `uniref90_hits.sto`, `mgnify_hits.sto`, a BFD/clustered A3M such as `bfd_uniclust_hits.a3m` or `bfd_uniref_hits.a3m`, and a template hit file such as `hhsearch_output.hhr` or `pdb70_hits.hhr`.

### Multimer

```bash
python run_pretrained_openfold.py \
  FASTA_DIR TEMPLATE_MMCIF_DIR \
  --output_dir OUTPUT_DIR \
  --config_preset model_1_multimer_v3 \
  --model_device cuda:0 \
  --uniref90_database_path DB/uniref90/uniref90.fasta \
  --mgnify_database_path DB/mgnify/mgy_clusters.fa \
  --pdb_seqres_database_path DB/pdb_seqres/pdb_seqres.txt \
  --uniref30_database_path DB/uniref30/UniRef30 \
  --uniprot_database_path DB/uniprot/uniprot.fasta \
  --bfd_database_path DB/bfd/bfd_metaclust \
  --hmmsearch_binary_path BIN/hmmsearch \
  --hmmbuild_binary_path BIN/hmmbuild \
  --kalign_binary_path BIN/kalign
```

For multimer, use PDB SeqRes with HMMSearch/HMBuild. Do not plan PDB70/HHSearch as the primary template search.

### SoloSeq with Precomputed ESM Embeddings

```bash
python run_pretrained_openfold.py \
  FASTA_DIR TEMPLATE_MMCIF_DIR \
  --output_dir OUTPUT_DIR \
  --config_preset seq_model_esm1b_ptm \
  --openfold_checkpoint_path SOLOSEQ_CHECKPOINT.pt \
  --model_device cuda:0 \
  --use_precomputed_alignments EMBEDDINGS_DIR
```

Embedding subdirectories can include optional `*.hhr` files for templates. If no `*.hhr` file exists, treat the run as template-free SoloSeq if the user confirms that choice.

### SoloSeq with On-the-Fly Embeddings and Optional Templates

```bash
python run_pretrained_openfold.py \
  FASTA_DIR TEMPLATE_MMCIF_DIR \
  --output_dir OUTPUT_DIR \
  --config_preset seq_model_esm1b_ptm \
  --openfold_checkpoint_path SOLOSEQ_CHECKPOINT.pt \
  --model_device cuda:0 \
  --uniref90_database_path DB/uniref90/uniref90.fasta \
  --pdb70_database_path DB/pdb70/pdb70 \
  --jackhmmer_binary_path BIN/jackhmmer \
  --hhsearch_binary_path BIN/hhsearch \
  --kalign_binary_path BIN/kalign
```

For template-free SoloSeq, omit the database and template-search binary flags intentionally, still provide the required `template_mmcif_dir` positional, and validate sequence lengths.

### Long Sequence Inference

```bash
python run_pretrained_openfold.py \
  FASTA_DIR TEMPLATE_MMCIF_DIR \
  --output_dir OUTPUT_DIR \
  --config_preset model_1_ptm \
  --model_device cuda:0 \
  --use_precomputed_alignments ALIGNMENTS_DIR \
  --long_sequence_inference \
  --precision bf16
```

Use `--precision bf16` only when hardware and runtime support it. Keep deeper offload/chunking config choices in `--experiment_config_json` and route low-level config questions to `../model-apis/`.

## `thread_sequence.py`

Use `thread_sequence.py` when a user wants to thread one query sequence onto one template mmCIF chain before prediction.

### Required Positionals

| Argument | Meaning |
| --- | --- |
| `input_fasta` | FASTA file containing exactly one sequence. |
| `input_mmcif` | Template mmCIF file to thread the sequence onto. |

### Important Flags

| Flag | Meaning |
| --- | --- |
| `--template_id TEXT` | PDB ID or other identifier for the template. |
| `--chain_id TEXT` | Chain ID in the template to use. |
| `--config_preset NAME` | Model config preset, default `model_1`. |
| `--model_device DEVICE` | Torch device, default `cpu`. |
| `--jax_param_path PATH` | JAX parameters; defaults to the derived resource path if no OpenFold checkpoint is provided. |
| `--openfold_checkpoint_path PATH` | OpenFold checkpoint directory or `.pt` file. |
| `--output_dir PATH` | Prediction output directory. |
| `--subtract_plddt` | Write `100 - pLDDT` in B-factor fields. |
| `--data_random_seed VALUE` | Random seed. |
| `--kalign_binary_path PATH` | Kalign executable for template feature generation. |

### Threading Pattern

```bash
python thread_sequence.py \
  QUERY.fasta TEMPLATE.cif \
  --template_id TEMPLATE_ID \
  --chain_id A \
  --config_preset model_1 \
  --model_device cuda:0 \
  --output_dir OUTPUT_DIR \
  --jax_param_path PARAMS.npz
```

Threading is single-sequence and single-template-chain oriented. For complexes or multiple chains, plan multimer inference instead.
