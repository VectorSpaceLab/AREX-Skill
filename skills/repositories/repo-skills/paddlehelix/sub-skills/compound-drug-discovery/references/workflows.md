# Compound and Drug-Discovery Workflow Routes

This reference distills command anatomy from PaddleHelix compound apps. Treat these as planning templates: verify local data/configs first, then ask before running heavyweight training, preprocessing, distributed jobs, downloads, or docking.

## Compound Representation and Property Prediction

### GEM / GeoGNN

Use GEM when the user asks for geometry-enhanced molecular representation learning or downstream molecular property prediction with 3D-aware atom, bond, and bond-angle features.

Command anatomy:

```bash
# Pretraining template; long MMFF/3D preprocessing can take hours even on demo data.
python pretrain.py \
  --dataset zinc \
  --data_path DATA_ROOT_OR_SMILES_DIR \
  --compound_encoder_config model_configs/geognn_l8.json \
  --model_config model_configs/pretrain_gem.json \
  --model_dir OUTPUT_MODEL_DIR \
  --batch_size 256 \
  --max_epoch 100 \
  --lr 0.001 \
  --dropout_rate 0.2

# Downstream finetuning scripts use classification/regression datasets and pretrained checkpoints.
sh scripts/finetune_class.sh
sh scripts/finetune_regr.sh
```

Expected inputs and outputs:

- Input SMILES/data path: a directory or file list accepted by the GEM pretrain code; each molecule must be parseable and 3D feature generation may require RDKit.
- Configs: compound encoder JSON plus model JSON; key groups include `atom_names`, `bond_names`, `bond_float_names`, `bond_angle_float_names`, `pretrain_tasks`, and `mask_ratio`.
- Init model: optional `.pdparams` checkpoint for the compound encoder.
- Output: epoch checkpoint files under the selected model directory and logs/results for downstream tasks.

Planning notes:

- GEM depends on PaddlePaddle, PGL, RDKit, NumPy, pandas, NetworkX, and scikit-learn; missing Paddle/PGL/RDKit is an expected environment failure for inspection-only installs.
- Full pretraining/finetuning is GPU/data-heavy; avoid running automatically.

### GEM-2

Use GEM-2 when the user asks about PCQM4Mv2, full-range many-body interactions, Optimus blocks, OGB-LSC molecular property prediction, or LIT-PCBA virtual screening.

Command anatomy:

```bash
# Training and inference are script-driven and assume prepared data/configs/checkpoints.
sh scripts/train.sh
sh scripts/inference.sh
```

Expected inputs and outputs:

- Dataset config: `data_dir` points to PCQM4Mv2 or processed GEM-2 data; `task_names` identifies label columns.
- Model config: model channel/dropout structure and data transform settings.
- Train config: learning rate, warmup steps, decay/mid-step settings, and checkpoint output under a model directory.
- Checkpoint: optional pretrained `.pdparams` file for inference or downstream initialization.

Planning notes:

- Published runtime notes mention around 60 minutes per PCQM4Mv2 epoch on 16 A100 cards with total batch size 512; treat as heavyweight.
- Prefer validating configs and data presence over launching training.

### PretrainGNNs

Use PretrainGNNs for GIN/GAT/GCN compound graph pretraining, attribute masking, graph-level supervised pretraining, and MoleculeNet-style downstream finetuning.

Command anatomy:

```bash
# Node-level attribute masking.
python pretrain_attrmask.py \
  --batch_size 256 \
  --num_workers 4 \
  --max_epoch 100 \
  --data_path data/chem_dataset/zinc_standard_agent \
  --compound_encoder_config model_configs/pregnn_paper.json \
  --model_config model_configs/pre_Attrmask.json \
  --model_dir output/pretrain_attrmask \
  --lr 0.001 \
  --dropout_rate 0.2

# Graph-level supervised pretraining; often starts from an attrmask checkpoint.
python pretrain_supervised.py \
  --batch_size 256 \
  --max_epoch 100 \
  --data_path data/chem_dataset/chembl_filtered \
  --compound_encoder_config model_configs/pregnn_paper.json \
  --model_config model_configs/pre_Supervised.json \
  --init_model output/pretrain_attrmask/epoch40/compound_encoder.pdparams \
  --model_dir output/pretrain_supervised \
  --lr 0.001

# Downstream MoleculeNet finetuning.
python finetune.py \
  --batch_size 32 \
  --max_epoch 100 \
  --dataset_name tox21 \
  --data_path data/chem_dataset/tox21 \
  --split_type scaffold \
  --compound_encoder_config model_configs/pregnn_paper.json \
  --model_config model_configs/down_linear.json \
  --init_model output/pretrain_supervised/epoch40/compound_encoder.pdparams \
  --model_dir output/finetune/tox21 \
  --encoder_lr 0.001 \
  --head_lr 0.001 \
  --dropout_rate 0.2
```

Expected inputs and outputs:

- Pretraining data: ZINC-style unlabeled molecules for node-level pretraining; ChEMBL filtered/cached data for graph-level supervised pretraining.
- Finetuning data: MoleculeNet-style task directory for datasets such as `tox21`, `hiv`, `bace`, `bbbp`, `clintox`, `muv`, `sider`, or `toxcast`.
- Configs: compound encoder JSON plus pretraining/downstream model JSON.
- Output: per-epoch `compound_encoder.pdparams`, full model `.pdparams`, and result summaries under `model_dir`.

Planning notes:

- GIN/GAT/GCN selection is controlled by the compound encoder config fields such as `gnn_type`, `hidden_size`, `embed_dim`, `layer_num`, `dropout`, residual/norm settings, and pooling.
- Scaffold splits need valid SMILES and RDKit; if RDKit is unavailable, prefer random/index split planning or route core splitter details to `core-api-data`.

### InfoGraph

Use InfoGraph for unsupervised graph-level representations on MUTAG/PTC-MR-style molecular graph datasets.

Command anatomy:

```bash
python scripts/preprocess_data.py

python unsupervised_pretrain.py \
  --task_name train \
  --use_cuda \
  --config model_configs/unsupervised_pretrain_config.json \
  --root data \
  --dataset mutag \
  --model_dir model_dir/mutag/run_1 \
  --emb_dir emb_dir/mutag/run_1 \
  --batch_size 256 \
  --max_epoch 100 \
  --lr 0.001
```

Expected inputs and outputs:

- Raw inputs: MUTAG/PTC-MR `.can` SMILES-like files and target files, then processed `data.npz` plus `smiles.txt` under each dataset's `processed` directory.
- Config: `unsupervised_pretrain_config.json` with atom/bond feature names and InfoGraph hyperparameters.
- Outputs: model checkpoints under `model_dir`, embedding pickles under `emb_dir`, and evaluation metrics from saved embeddings.

## Drug-Target Interaction (DTI)

### GraphDTA

Use GraphDTA when the user asks for drug-target affinity prediction with molecular graph encoders and sequence-convolution protein encoders on Davis/Kiba-like data.

Command anatomy:

```bash
# Data preprocessing is required before training.
python scripts/preprocess_data.py

# Shell wrapper contract.
./scripts/train.sh davis model_configs/fix_prot_len_gin_config.json
./scripts/train.sh kiba model_configs/fix_prot_len_gin_config.json --use_kiba_label

# Direct train.py contract.
python train.py \
  --device gpu \
  --train_data data/davis/processed/train/ \
  --test_data data/davis/processed/test/ \
  --model_config model_configs/fix_prot_len_gin_config.json \
  --model_dir model_dir/davis_fix_prot_len_gin_config \
  --batch_size 512 \
  --max_epoch 1000 \
  --lr 0.0005
```

Expected inputs and outputs:

- Davis/Kiba raw metadata: `ligands_can.txt`, `proteins.txt`, `Y`, and `folds/train_fold_setting1.txt` plus `folds/test_fold_setting1.txt`.
- Processed NPZ: `processed/train/<dataset>_train.npz` and `processed/test/<dataset>_test.npz`.
- Config: JSON with `compound` atom/bond fields, `gnn_type`, embedding/layer sizes, and `protein.max_protein_len`.
- Outputs: model checkpoints and printed MSE/CI metrics; lower MSE and higher CI are better.

Planning notes:

- Kiba needs `--use_kiba_label`; Davis uses default Kd labels.
- GraphDTA preprocessing and training require Paddle/PGL/RDKit-compatible environments; validate directory pieces before launching.

### MolTrans

Use MolTrans for DTI classification or regression with drug/protein substructure tokenization and transformer interaction modeling.

Command anatomy:

```bash
# Classification: allowed datasets are cls_davis, cls_biosnap, cls_bindingdb.
CUDA_VISIBLE_DEVICES=0 python train_cls.py \
  --batchsize 64 \
  --epochs 200 \
  --lr 5e-4 \
  --dataset cls_davis \
  --model_config config.json

# Regression: allowed datasets include raw_chembl_pkd, raw_chembl_kd,
# raw_bindingdb_kd, raw_davis, raw_kiba, benchmark_davis, benchmark_kiba.
CUDA_VISIBLE_DEVICES=0 python train_reg.py \
  --batchsize 64 \
  --epochs 200 \
  --lr 5e-4 \
  --dataset benchmark_davis \
  --model_config config.json
```

Expected inputs and outputs:

- Classification data: `dataset/classification/<name>/train.csv`, `val.csv`, and `test.csv`; BioSNAP variants may nest under `full_data`, `missing_data`, `unseen_drug`, or `unseen_protein`.
- Regression data: `dataset/regression/DAVIS/{affinity.txt,SMILES.txt,target_seq.txt}`, `KIBA/{affinity.txt,SMILES.txt,target_seq.txt}`, BindingDB/ChEMBL text files, or benchmark folders.
- Config keys: `drug_max_seq`, `target_max_seq`, `emb_size`, `input_drug_dim`, `input_target_dim`, `interm_size`, `num_attention_heads`, `flatten_dim`, `layer_size`, and dropout ratios.
- Outputs: AUROC for classification; MSE/CI for regression.

Planning notes:

- Source code uses CUDA-style tensor calls, so CPU-only operation may require code changes even if Paddle falls back to CPU.
- `subword-nmt`, SciPy, VisualDL, PyYAML, Paddle, and scikit-learn are documented dependencies.

### SIGN, SMAN, GIANT, and PDBbind-style DTI

Use SIGN, SMAN, or GIANT for protein-ligand binding affinity where the data are 3D complexes rather than only SMILES/sequence pairs.

Command anatomy:

```bash
# SIGN preprocessing and training.
python preprocess_pdbbind.py \
  --data_path_core DATASET_PATH \
  --data_path_refined DATASET_PATH \
  --dataset_name pdbbind2016 \
  --output_path OUTPUT_PATH \
  --cutoff 5

python train.py \
  --cuda 0 \
  --model_dir output/sign \
  --dataset pdbbind2016 \
  --data_dir data/ \
  --cut_dist 5 \
  --num_angle 6

# SMAN preprocessing/training/testing.
python preprocess.py \
  --data_path DATASET_PATH \
  --dataset_name v2016_LPHIN3f5t_Sp \
  --output_path OUTPUT_PATH \
  --cutoff 5

python train.py \
  --lr_d \
  --data_path DATA_PATH \
  --dataset v2016_LPHIN3f5t_Sp \
  --save_path RUNS_DIR \
  --gpu 0

python test.py \
  --data_path DATA_PATH \
  --dataset v2016_LPHIN3f5t_Sp \
  --model_path MODEL_PATH \
  --gpu 0
```

Expected inputs and outputs:

- Inputs: PDBbind/CSAR-style protein-ligand complexes and preprocessed graph/feature/coordinate files; OpenBabel may be needed only for preprocessing/conversion.
- Train/test split naming: SIGN/GIANT expect dataset-specific train/test/val subsets under `data_dir`; SMAN expects matching data path and dataset name.
- Outputs: checkpoints under model/save paths, pickled predictions or metrics under output paths.

Planning notes:

- Dependencies include Paddle/PGL and optionally OpenBabel; SIGN documents Python >=3.8, Paddle >=2.1.0, PGL >=2.1.4, and OpenBabel 3.1.1 for preprocessing.
- Treat raw PDBbind downloads, Chimera conversion, and feature preprocessing as user-approved heavy steps.

### BatchDTA

Use BatchDTA when the user wants batch-effect-aware DTA estimation or pairwise/pointwise baselines for DeepDTA, GraphDTA, or MolTrans.

Command anatomy:

```bash
# Pairwise BatchDTA examples.
python run_pairwise_deepdta_CV.py --data_path ../../Data/ --dataset DAVIS --is_mixed False
python -m torch.distributed.launch run_pairwise_GraphDTA_CV.py --data_path ../../Data/ --dataset DAVIS --is_mixed False
python run_pairwise_Moltrans_CV.py --data_path ../../Data/ --dataset DAVIS --is_mixed False

# Pointwise baseline examples.
CUDA_VISIBLE_DEVICES=0 python train_davis.py --batchsize 256 --epochs 100 --rounds 1 --lr 1e-3
python train_kiba.py --batchsize 512 --epochs 200 --rounds 1 --lr 5e-4 --cudanum 0 --model 2
```

Expected inputs and outputs:

- Processed BatchDTA data directory containing Davis/KIBA cross-validation, independent test sets, and BindingDB subsets for KD/KI/IC50/EC50.
- Dependencies include Python >=3.7, Torch, PaddlePaddle, RDKit, and scikit-learn.
- Pairwise GraphDTA can use distributed Torch launch; do not run automatically.

## Molecular Generation

### JT-VAE

Use JT-VAE for junction-tree molecular graph generation from SMILES and a vocabulary file.

Command anatomy:

```bash
# Build a vocabulary from a SMILES training file.
python -m src.mol_tree \
  --train_path data/zinc/250k_rndm_zinc_drugs_clean_sorted.smi \
  --vocab_path data/zinc/vocab.txt

# Preprocess SMILES into split processed data.
python preprocess.py \
  --train_path data/zinc/250k_rndm_zinc_drugs_clean_sorted.smi \
  --save_dir zinc_processed \
  --split 100 \
  --num_workers 8

# Train or fine-tune.
CUDA_VISIBLE_DEVICES=0 python vae_train.py \
  --train zinc_processed \
  --vocab data/zinc/vocab.txt \
  --config configs/config.json \
  --save_dir vae_models \
  --num_workers 1 \
  --epoch 50 \
  --batch_size 32 \
  --use_gpu True

# Sample from a checkpoint.
python sample.py \
  --nsample 10000 \
  --vocab data/zinc/vocab.txt \
  --model vae_models/model.iter-441000 \
  --config configs/config.json \
  --output sampling_output.txt
```

Expected inputs and outputs:

- Input SMILES file: one molecule per line; validate with the bundled script before preprocessing.
- Vocabulary file: generated from the training set and reused by train/sample.
- Config: `hidden_size`, `latent_size`, `depthT`, `depthG`, learning rate, KL annealing, print/save intervals.
- Outputs: processed shards, VAE checkpoints, and sampling text with generated SMILES plus metrics such as valid, unique, IntDiv, filters, and novelty.

Planning notes:

- Some README snippets use `--vocab_file`, but the current `src/mol_tree.py` parser expects `--vocab_path`; check the script parser when adapting older commands.

### SD-VAE

Use SD-VAE for grammar/semantics-directed molecular sequence generation.

Command anatomy:

```bash
python data_preprocessing/make_dataset_parallel.py \
  -info_fold data/data_SD_VAE/context_free_grammars \
  -grammar_file data/data_SD_VAE/context_free_grammars/mol_zinc.grammar \
  -smiles_file data/data_SD_VAE/zinc/250k_rndm_zinc_drugs_clean.smi

python data_preprocessing/dump_cfg_trees.py \
  -info_fold data/data_SD_VAE/context_free_grammars \
  -grammar_file data/data_SD_VAE/context_free_grammars/mol_zinc.grammar \
  -smiles_file data/data_SD_VAE/zinc/250k_rndm_zinc_drugs_clean.smi

CUDA_VISIBLE_DEVICES=0 python train_zinc.py -mode gpu

python sample_prior.py \
  -info_fold data/data_SD_VAE/context_free_grammars \
  -grammar_file data/data_SD_VAE/context_free_grammars/mol_zinc.grammar \
  -model_config model_config.json \
  -saved_model model/train_model_epoch499
```

Expected inputs and outputs:

- Data root contains context-free grammars and ZINC SMILES files.
- `model_config.json` sets latent dimension, maximum decode steps, encoder/RNN type, and reparameterization parameters.
- Outputs include binary cooked data, CFG dumps, trained model folders, generated samples, reconstruction output, and reported validity/uniqueness/diversity.

### Seq-VAE

Use Seq-VAE when the user wants a simpler sequence VAE over SMILES strings.

Command anatomy:

```bash
CUDA_VISIBLE_DEVICES=0 python trainer.py \
  --device gpu \
  --dataset_dir data/zinc_moses/train.csv \
  --model_config model_config.json \
  --model_save results/train_models/ \
  --config_save results/config/
```

Expected inputs and outputs:

- Dataset CSV: MOSES/ZINC-style `train.csv` and optional `test.csv`, with SMILES sequences.
- Config: `max_length`, encoder/decoder RNN cells/layers/dropout, latent dimension, and embedding options.
- Training args: epoch count, batch size, learning rate, KL schedule, and output directories.
- Sampling metrics include valid, novelty, unique@k, filters, and internal diversity.

## Drug Synergy and Few-Shot Property Workflows

### Drug-Drug Synergy

Use DTSyn when the user has DDI labels plus gene-expression/RNA feature tables; use RGCN when the user has DDI, DTI, PPI, and drug feature network files.

Command anatomy:

```bash
# DTSyn.
CUDA_VISIBLE_DEVICES=0 python3 main.py \
  --ddi data/ddi.csv \
  --lincs data/gene_vector.csv \
  --rna data/rna.csv \
  --epochs 150 \
  --batch_size 32 \
  --lr 5e-6

# RGCN; remove --cuda for CPU planning.
CUDA_VISIBLE_DEVICES=0 python3 train.py \
  --ddi data/DDI/DDs.csv \
  --dti data/DTI/drug_protein_links.tsv \
  --ppi data/PPI/protein_protein_links.txt \
  --d_feat data/all_drugs_name.fet \
  --epochs 10 \
  --num_graph 10 \
  --sub_neighbours 10 10 \
  --cuda
```

Expected inputs and outputs:

- DTSyn: DDI CSV represented by SMILES/drug pairs, LINCS gene vectors, RNA CSV, optional test DDI CSV.
- RGCN: DDI labels, DTI links, PPI links, and drug physicochemical feature file.
- Outputs: training logs, model state, and prediction/evaluation metrics depending on script configuration.

### Few-Shot Molecular Property (PAR)

Use this route for property-aware relation networks on few-shot MoleculeNet-style tasks.

Command anatomy:

```bash
python main.py \
  --dataset toxcast \
  --test-dataset toxcast \
  --data-dir data/ \
  --n-shot-train 10 \
  --n-shot-test 10 \
  --n-query 16 \
  --epochs 5000 \
  --enc_gnn gin \
  --pretrained 1 \
  --pretrained_weight_path PRETRAINED_ENCODER.pdparams \
  --result_path results
```

Expected inputs and outputs:

- Datasets: Tox21, SIDER, MUV, and ToxCast task directories downloaded from the documented SNAP-derived archive.
- Environment: PaddlePaddle, PGL, and PaddleHelix compatible with the app; tested development notes cite PaddlePaddle 2.0.2, PGL 2.1.5, and PaddleHelix 1.0.1.
- Outputs: meta-learning logs, saved checkpoints, and per-task few-shot results.

## Cross-Workflow Checklist

Before running any app command:

1. Confirm the task family and dataset kind.
2. Run `validate_compound_inputs.py` for SMILES, JSON config, and expected dataset directories when applicable.
3. Confirm optional dependencies: PaddlePaddle, PGL, RDKit, OpenBabel, Torch, subword-nmt, SciPy, VisualDL, PyYAML.
4. Confirm compute/resource assumptions: GPU count, CUDA/Paddle compatibility, expected training time, model checkpoint size, and whether downloads are approved.
5. Keep generated outputs in user-approved output directories and avoid mutating source app directories unless the user explicitly asks for that workflow style.
