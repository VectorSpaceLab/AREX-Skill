# HelixDock Reference

Use this reference for PaddleHelix HelixDock planning, validation, and troubleshooting. HelixDock is a protein-ligand structure prediction workflow; it is not a lightweight local smoke test.

## When to Use

Use HelixDock guidance when the user asks about:

- Protein-ligand docking or predicted ligand conformations.
- Reproducing PDBbind core or PoseBusters docking results.
- HelixDock model/data/config/output layout.
- OpenBabel/RDKit setup for ligand pose evaluation.
- The PaddleHelix online HelixDock service or non-commercial license caveats.

Route protein structure prediction without docking to the structure-prediction sub-skill; route sequence-only protein property work to protein-sequence-function.

## License and Service Caveats

- HelixDock documentation states a Creative Commons non-commercial license for this project area. Confirm intended use before helping with commercial workflows.
- PaddleHelix provides an online HelixDock service; using it may involve external service terms, uploaded structures, network access, and possibly commercial rules. Do not send user data to the service without explicit approval.
- Training data access is described as available to academic researchers via a partnership/contact flow; do not automate requests or downloads.

## Environment Contract

Documented setup concepts:

- Use a dedicated Python 3.7-era environment for HelixDock rather than modifying a shared environment.
- Install the HelixDock requirements file and an OpenBabel build compatible with the workflow.
- Confirm the PaddlePaddle/CUDA combination before running distributed reproduction commands.

Important notes:

- RDKit version matters; documentation warns that versions other than `2022.3.3` may cause model parameter loading errors.
- OpenBabel is needed to calculate aligned RMSD between predicted and crystal poses, and may also be needed for structure conversion workflows.
- PaddlePaddle distributed launch is used in reproduction scripts; confirm Paddle/CUDA compatibility and available GPUs before running.
- Do not install or downgrade chemistry packages in a shared environment without user approval.

## Data and Model Layout

### Model Parameters

Expected model directory:

```text
model/
└── helixdock.pdparams
```

The reproduction scripts set `init_model=model/helixdock.pdparams`.

### Raw PDBbind Core Data

Expected raw complex concept:

```text
../data/PDBbind_v2020/complex/
└── <complex_id>/... protein/ligand structure files ...
```

The PDBbind dataset config refers to:

- `data_dir`: raw complex directory.
- `label_file`: PDBbind label/index file.
- `complex_id_file`: list of test complex identifiers.
- `cache_dir`: processed/cache directory.

### Processed Data

Expected processed roots:

```text
data/processed/
├── pdbbind_core_processed/
└── posebuster_processed/
```

Processed data avoid repeated feature generation. Validate these directories before reproducing results.

### Config Files

Reproduction uses four config paths:

```text
configs/dataset_configs/pdbbind_core.json
configs/dataset_configs/poesbusters.json
configs/model_configs/helixdock_model.json
configs/model_configs/helixdock_encoder.json
configs/train_configs/lr8e-4_ema.json
```

Dataset config example keys:

- `test.<dataset>.data_dir`: raw complex path.
- `test.<dataset>.label_file`: labels/index file.
- `test.<dataset>.complex_id_file`: selected complex IDs.
- `test.<dataset>.cache_dir`: processed feature cache.
- `metric_type`: usually `DTI`.
- `save_output`, `save_rmsd`, `output_num`.
- `use_diffusion` and nested `diffusion_params` such as `T`, `S`, `eta`, `mean_type`, `normal_mean`, and `normal_std`.
- `label_mean` and `label_std`.

Model config example keys:

- `model.heads.ligand_atom_pos_head.loss_scale`.
- `drop_head_param`.
- `model.diffusion_params.in_use`.
- `model.diffusion_params.mean_type`.
- `model.heads.ligand_atom_pos_head.use_diffusion`.

Train config example keys:

- `lr`.
- `warmup_step`.
- `ema_decay`.
- `ema_start_step`.

## Command Anatomy

Do not run these automatically. They start distributed Paddle evaluation and require model/data/configs.

```bash
# PDBbind core reproduction contract.
python -m paddle.distributed.launch --log_dir log/reproduce_core evalute.py \
  --batch_size 2 \
  --init_model model/helixdock.pdparams \
  --distributed \
  --encoder_config configs/model_configs/helixdock_encoder.json \
  --dataset_config configs/dataset_configs/pdbbind_core.json \
  --train_config configs/train_configs/lr8e-4_ema.json \
  --model_config configs/model_configs/helixdock_model.json \
  --log_dir log/reproduce_core

# PoseBusters reproduction contract.
python -m paddle.distributed.launch --log_dir log/reproduce_posebuster evalute.py \
  --batch_size 2 \
  --init_model model/helixdock.pdparams \
  --distributed \
  --encoder_config configs/model_configs/helixdock_encoder.json \
  --dataset_config configs/dataset_configs/poesbusters.json \
  --train_config configs/train_configs/lr8e-4_ema.json \
  --model_config configs/model_configs/helixdock_model.json \
  --log_dir log/reproduce_posebuster
```

Planning notes:

- `evalute.py` spelling in the app is intentional.
- PoseBusters reproduction documentation notes that multi-sampling and ranking using RTMScore and PoseBusters score are required.
- Treat `--batch_size 2` as a published reproduction default, not a universal setting.

## Output Contract

PDBbind core output layout:

```text
log/reproduce_core/save_output/step0/pdbbind_core/
└── mol_name.sdf
```

PoseBusters output layout:

```text
log/reproduce_posebuster/save_output/step0/posebuster/
└── mol_name.sdf
```

Each `mol_name.sdf` is the predicted conformation for an input molecule. The README shows `step-1`, while the current `evalute.py` writes `step0/<dataset-name>` during the default single evaluation pass; inspect the selected app revision if an output directory looks empty. Additional logs, metrics, RMSD files, and cache artifacts may appear under the selected `log_dir` and processed data directories depending on config flags.

## Skip-Network and Heavy-Run Guidance

Never assume downloads are approved. Ask first before:

- Downloading `helixdock.pdparams` or processed/raw datasets.
- Contacting the PaddleHelix service or partnership endpoint.
- Installing OpenBabel/RDKit/Paddle into a shared environment.
- Running distributed launch, multi-sampling, ranking, or full-dataset evaluation.
- Moving raw complexes into shared `../data`-style folders.

When the user wants a dry preflight, validate only:

- Model checkpoint path exists.
- Dataset config JSON parses and points to existing data/cache paths.
- Model/encoder/train config JSON parse.
- Output/log parent directories are writable.
- Optional tools (`python`, `paddle`, `rdkit`, `obabel`) are available if the requested step requires them.

## Troubleshooting and Safe Operation

### RDKit Version or Model Loading Fails

Symptoms:

- Model parameters fail to load after changing chemistry environment.
- Featurization or molecule parsing errors appear before inference.

Actions:

- Check the RDKit version; HelixDock notes RDKit `2022.3.3` as expected.
- Recreate an isolated environment rather than changing a shared one.
- Validate the model checkpoint exists and is not a partial download.

### OpenBabel Missing

Symptoms:

- Aligned RMSD cannot be calculated.
- Structure conversion steps fail with `obabel` missing.

Actions:

- If only inference output SDFs are needed, clarify whether RMSD evaluation can be skipped.
- If RMSD is required, install OpenBabel in an isolated environment with user approval.

### Dataset Config Points to Missing Paths

Symptoms:

- `data_dir`, `label_file`, `complex_id_file`, or `cache_dir` not found.
- Empty output under `save_output`.

Actions:

- Open the JSON config and resolve paths relative to the intended HelixDock working directory.
- Verify raw or processed data were unpacked into the expected structure.
- Do not silently switch from raw to processed data; ask the user which source to use.

### GPU or Distributed Launch Problems

Symptoms:

- Paddle distributed launch fails.
- CUDA device unavailable or out of memory.
- Batch size 2 still fails.

Actions:

- Confirm `paddle` is installed with CUDA support and matches the driver/runtime.
- Try a smaller batch size only with user approval because it can affect throughput and runtime.
- For CPU-only environments, explain that reproduction-scale HelixDock is not a practical smoke test.

### Long Runtime or Large Outputs

Symptoms:

- Evaluation appears hung while generating many samples.
- Logs/output SDF directories grow unexpectedly.

Actions:

- Confirm `output_num`, diffusion sampling parameters, dataset size, and whether PoseBusters ranking is enabled.
- Run a tiny user-provided subset only if the user approves creating such a subset.

## Preflight Checklist

- `model/helixdock.pdparams` exists and is complete.
- Dataset config JSON parses and contains a `test` section with one or more datasets.
- Referenced `data_dir`, `label_file`, `complex_id_file`, and `cache_dir` are present or intentionally to be generated.
- Model, encoder, and train config JSON files parse.
- Requested output `log_dir` can be created.
- RDKit/OpenBabel/Paddle requirements are explicit for the requested step.
- User has approved any network, install, distributed, GPU, or long-running action.
