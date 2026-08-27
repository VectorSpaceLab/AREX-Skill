# HelixFold Family Reference

PaddleHelix contains several structure-prediction workflows with overlapping names but different inputs, dependencies, and outputs. Route requests by the biological target and command surface instead of by source folder names.

## Quick Distinctions

| Workflow | Best fit | Input | Heavy dependencies | Main output |
| --- | --- | --- | --- | --- |
| HelixFold3 | AlphaFold3-like biomolecular complexes: protein, DNA, RNA, ligands, ions, modified residues | Entity JSON | Paddle GPU 3.1.0-era stack, MSA tools/databases, CCD preprocessing, checkpoint | Ranked mmCIF folders with `all_results.json` |
| HelixFold-S1 | Interface-focused multi-chain biomolecular prediction with a staged S1 flow | Entity JSON with `job_name`, usually at least two chains | Same broad HelixFold3-style stack plus S1 checkpoints and `anarci` in docs | `final_features.pkl`, `interface_infos/`, `module1/`, `module2/` ranked mmCIF folders |
| HelixFold | AlphaFold2-style protein monomer/multimer inference and training | FASTA | Paddle dev/GPU stack, OpenMM/PDBFixer for relaxation, MSA tools/databases, AlphaFold parameters | Ranked PDB files, feature caches, model result pickles |
| HelixFold-Single | MSA-free protein-only inference using a protein language model | FASTA | Paddle dev/GPU stack and the HelixFold-Single checkpoint | `unrelaxed.pdb` |

For general protein sequence modeling that is not a 3D structure run, route to `../protein-sequence-function/SKILL.md`. For docking workflows such as HelixDock, route to `../compound-drug-discovery/SKILL.md`.

## HelixFold-S1 Module Flow

HelixFold-S1 wraps a multi-stage pipeline around HelixFold3-like all-atom models. Its shell launcher accepts two user inputs:

```bash
sh run_inference.sh input.json output_dir
```

Treat the launcher as reference-only. Distill it into these stages:

1. MSA module: `run_msa_module.py` reads `--json_path`, copies `user_input.json`, writes `job_status.json`, validates schema, creates `final_features.pkl`, writes `timings_featurization.json`, and stores MSA hits under `msas/`.
2. Generation module 1: `run_inference_module.py` reads the same JSON/output directory, `--model_names`, a module-1 checkpoint, and the CCD preprocessed file. It writes intermediate outputs under `module1/` and interface probability files used by the next stage.
3. Inference module 2: `run_inference_S1_module2.py` reads module-1 interface outputs, a module-2 checkpoint, and the CCD preprocessed file. It writes final ranked predictions under `module2/`, interface visualizations/data under `interface_infos/`, and sampling history under `previous_sampled_interface/`.

S1 top-level JSON fields:

- `job_name`: required by the Python inference modules and used in output naming.
- `recycle`: optional integer; documented default is 10.
- `ensemble`: optional integer; documented default is 30 in README examples, while module code falls back to 1 when absent.
- `entities`: same general entity array shape as HelixFold3.
- `model_type`: defaults to a HelixFold3-like value in module code; S1 examples set `HelixFold-S1`.
- `s1_sample_constraint`: optional extra field consumed by module-2 code when present.
- `constraint`: not supported for S1; use `s1_sample_constraint` for interface sampling constraints.

The README warns that HelixFold-S1 supports at least two chains in the input JSON. Treat a single expanded chain as a likely misuse for S1, even if it is syntactically valid JSON.

S1 also accepts `sidechain_replace` modification objects in examples. These use `index`, `R_smiles`, and zero-based-or-higher `R_connect_idx`; keep them S1-only and do not apply them to ordinary HelixFold3 planning unless the user has newer local documentation.

## HelixFold-S1 Output Layout

For a `job_name` such as `demo`, outputs are written directly under the chosen output directory:

```text
output_dir/
  final_features.pkl
  user_input.json
  job_status.json
  timings_featurization.json
  msas/
  interface_infos/
    predicted_interface.png
    predicted_interface.json
    sample_infos.csv
  module1/
  module2/
    job-demo-17-rank1/
      all_results.json
      predicted_structure.cif
      predicted_structure.cifABC
      timings.json
      chain_id_mapping.csv
  previous_sampled_interface/
```

The final ranked structure is in `module2/`. `chain_id_mapping.csv` maps output chain IDs back to input entity indices.

## HelixFold Inference

HelixFold is the AlphaFold2-style protein structure workflow. It takes one or more FASTA files and creates an output subdirectory per FASTA basename. The parser requires unique FASTA basenames because they become output directory names.

Single-GPU command shape:

```bash
python run_helixfold.py \
  --fasta_paths target.fasta \
  --data_dir data \
  --bfd_database_path data/bfd/bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt \
  --small_bfd_database_path data/small_bfd/bfd-first_non_consensus_sequences.fasta \
  --uniclust30_database_path data/uniclust30/uniclust30_2018_08/uniclust30_2018_08 \
  --uniref90_database_path data/uniref90/uniref90.fasta \
  --mgnify_database_path data/mgnify/mgy_clusters_2018_12.fa \
  --pdb70_database_path data/pdb70/pdb70 \
  --template_mmcif_dir data/pdb_mmcif/mmcif_files \
  --obsolete_pdbs_path data/pdb_mmcif/obsolete.dat \
  --max_template_date 2020-05-14 \
  --model_names model_5 \
  --output_dir helixfold_output \
  --preset reduced_dbs \
  --jackhmmer_binary_path <msa-bin>/jackhmmer \
  --hhblits_binary_path <msa-bin>/hhblits \
  --hhsearch_binary_path <msa-bin>/hhsearch \
  --kalign_binary_path <msa-bin>/kalign \
  --precision fp32
```

Distributed inference adds `python -m paddle.distributed.launch`, `--distributed`, `--dap_degree`, and GPU selection flags. It also requires a Paddle build compiled with distributed support and `ppfleetx` for BP/DAP modes.

HelixFold output subdirectory contents mirror AlphaFold-style outputs:

- `features.pkl` and optional `features.npz`: cached feature arrays.
- `msas/`: MSA hits.
- `unrelaxed_model_*.pdb`, `relaxed_model_*.pdb`, `ranked_*.pdb`.
- `result_model_*.pkl`: raw model outputs.
- `ranking_debug.json`: confidence scores and model ranking order.
- `timings.json`: per-stage timings.

The code also supports `--precision fp32|bf16`, `--disable_amber_relax`, `--enable_low_memory`, and `--subbatch_size`. Use `--enable_low_memory` only for long protein planning after the user confirms suitable model parameters and hardware.

## HelixFold Training Boundary

HelixFold training is not a safe default operation. The docs describe full training using single-node/multi-node GPU modes, branch parallelism (BP), dynamic axial parallelism (DAP), data parallelism (DP), and multi-node environment variables. Examples include 8-node/64-GPU modes and long wall-clock times. Treat training requests as planning-only until the user explicitly approves data downloads, environment mutation, cluster settings, and execution.

Training command modes are selected through `gpu_train.sh` names such as `demo_initial_N1C1`, `demo_finetune_N1C8`, and `demo_initial_N8C64_dp16_bp2_dap2`. Do not run these as part of skill validation.

## HelixFold-Single

HelixFold-Single is the MSA-free protein-only route. It combines a protein language model with AlphaFold2-style geometry and needs only a FASTA file plus the trained checkpoint, not MSA databases.

Command shape:

```bash
python helixfold_single_inference.py \
  --init_model helixfold-single.pdparams \
  --fasta_file target.fasta \
  --output_dir output
```

The output directory contains `unrelaxed.pdb`. The FASTA reader uses the first header and then accumulates sequence lines until another `>` header or EOF; prefer one protein per FASTA file for this script. Route FASTA syntax and protein alphabet validation questions to `references/data-formats.md` and, for non-structure protein tasks, `../protein-sequence-function/SKILL.md`.

## Resource and Precision Notes

- HelixFold3 and S1 docs recommend at least about 32 GB GPU memory for inference.
- A100/H100-class GPUs can support `bf16` in documented guidance; V100 is documented as `fp32` only for HelixFold3 token planning.
- HelixFold code paths support `bf16` and `fp32`, but hardware and Paddle build compatibility decide whether `bf16` is safe.
- For long protein or large multimodal inputs, reduce diffusion batch size/inference repetitions first, then consider lower subbatch/recycle settings if the workflow exposes them.

## Evidence Labels

This reference distills evidence from `apps/protein_folding/HelixFold-S1/README.md`, `apps/protein_folding/HelixFold-S1/run_inference.sh`, `apps/protein_folding/HelixFold-S1/run_msa_module.py`, `apps/protein_folding/HelixFold-S1/run_inference_module.py`, `apps/protein_folding/HelixFold-S1/run_inference_S1_module2.py`, `apps/protein_folding/helixfold/README.md`, `apps/protein_folding/helixfold/README_inference.md`, `apps/protein_folding/helixfold/README_train.md`, `apps/protein_folding/helixfold/run_helixfold.py`, `apps/protein_folding/helixfold-single/README.md`, and `apps/protein_folding/helixfold-single/helixfold_single_inference.py`.
