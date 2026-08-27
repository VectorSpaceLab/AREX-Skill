# Protein Sequence and Function Workflows

This reference distills PaddleHelix protein sequence and function workflows into command anatomy and decision rules. Evidence labels are repo-relative source labels only; this skill is self-contained and does not require future agents to reopen those files.

## Workflow Selection

| User intent | Use | Avoid |
| --- | --- | --- |
| Pretrain or finetune protein sequence encoders | TAPE sequence workflow | Function-prediction graph models unless the user asks for PDB/GO labels |
| Predict secondary-structure/remote-homology/fluorescence/stability from sequences | TAPE `predict` shape with a saved sequence model | HelixFold structure prediction |
| Predict GO/protein function from PDB-derived chain graphs | DeepFRI, ProteinSIGN, or PTHL function workflow | Plain-sequence TAPE unless only sequence features are requested |
| Protein-protein interaction | PPI route, but scoped S2F code is not released | Inventing nonexistent training commands |
| Any-to-any protein sequence/structure/text generation | HelixProtX high-level route with license/model-availability caveats | Treating it as a ready pretrained inference package |

## TAPE Command Anatomy

The TAPE app implements Transformer, LSTM, and ResNet sequence encoders with task heads for pretraining, sequence classification, classification, and regression. Launcher placeholders below represent the corresponding project entry point in a user's working checkout; they are not bundled skill scripts.

### Train

```bash
python <tape_train_launcher> \
  --train_data <train_npz_dir> \
  --valid_data <valid_npz_dir> \
  --model_config <model_config.json> \
  [--init_model <checkpoint.pdparams>] \
  [--hot_start hot_start|finetune] \
  [--use_cuda] \
  [--is_distributed]
```

- `--train_data` and `--valid_data` are directories containing one or more `.npz` shards.
- `--model_config` selects `task`, `model_type`, labels, class count, hidden dimensions, and optional regularization.
- `--init_model` can warm-start or finetune. `--hot_start hot_start` loads the whole model state; other values load encoder weights into the encoder.
- Parser evidence uses `--is_distributed`; README prose may say `--distributed`. Prefer `--is_distributed` for the scoped launcher unless the user's checkout differs.
- Multi-GPU training uses `paddle.distributed.launch` plus `--is_distributed`; single-GPU/CPU omits distributed launch.

### Evaluate

```bash
python <tape_eval_launcher> \
  --eval_data <eval_npz_dir> \
  --model_config <model_config.json> \
  --eval_model <checkpoint.pdparams>
```

- Evaluation consumes the same NPZ directory format as training/eval splits.
- The scoped parser has no `--use_cuda` flag even though README prose mentions it; the inspected launcher calls `paddle.set_device("gpu")` and initializes Fleet, so confirm GPU/Paddle compatibility or patch the user's launcher before promising CPU eval.
- Some eval code imports legacy `others.*` helper paths; if those fail, align the launcher imports with the packaged `pahelix`/TAPE modules before execution.

### Predict

```bash
python <tape_predict_launcher> \
  --predict_data <plain_sequence_file> \
  --model_config <model_config.json> \
  --predict_model <checkpoint.pdparams> \
  [--use_cuda]
```

- Current parser evidence uses `--predict_data` and reads one stripped sequence per non-empty line.
- Older README prose may describe stdin, `--batch_size`, or `--model`; prefer the actual parser shape `--predict_data`, `--model_config`, `--predict_model`, and optional `--use_cuda` when generating commands.
- Prediction tokenizes each sequence with `ProteinTokenizer`, pads examples to the longest sequence in the prediction file, and prints labels or scores according to `task`.

## TAPE Task Roles

| `task` | Typical PaddleHelix task | Data/label shape | Output/metric orientation |
| --- | --- | --- | --- |
| `pretrain` | Pfam masked-language pretraining | `token_ids`, `lengths`; mask labels generated during loading | accuracy/perplexity over masked positions |
| `seq_classification` | secondary structure | token-level labels such as `labels3` | per-position class predictions |
| `classification` | remote homology | one label per sequence | sequence class prediction/accuracy |
| `regression` | fluorescence, stability | one float target per sequence | scalar prediction/MSE and Spearman |

## Function Prediction Command Anatomy

DeepFRI, ProteinSIGN, and PTHL are graph-based protein function workflows built around PDB-derived chain graphs and GO/function label `.npz` files. They require PaddlePaddle and PGL, and they are data/checkpoint dependent.

### DeepFRI Train

```bash
python <deepfri_train_launcher> \
  --train_file <train_chain_list.txt> \
  --valid_file <valid_chain_list.txt> \
  --protein_chain_graphs <chain_graph_dir> \
  --label_data_path <labels.npz> \
  [--cuda -1|0] [--batch_size 64] [--epochs 200]
```

Important knobs include graph convolution layer choice (`--gc_layer GraphConv|SAGEConv|GAT`), graph/FC dimensions, `--pad_len`, optional language-model checkpoint (`--lm_model_name`), `--cmap_thresh`, `--n_channels`, and `--use_cache 0|1`.

### DeepFRI Test

```bash
python <deepfri_test_launcher> \
  --test_file <test_chain_list.txt> \
  --protein_chain_graphs <chain_graph_dir> \
  --label_data_path <labels.npz> \
  --model_name <saved_model.pdparams> \
  [--cuda -1|0] [--batch_size 64]
```

`--model_name` and `--label_data_path` are required. A saved state is expected to contain model parameters and training args that the test launcher merges into runtime args.

### ProteinSIGN Train/Test

```bash
python <proteinsign_train_launcher> \
  --train_file <train_chain_list.txt> \
  --valid_file <valid_chain_list.txt> \
  --protein_chain_graphs <chain_graph_dir> \
  --label_data_path <labels.npz> \
  [--cuda -1|0] [--batch_size 32] [--epochs 200]

python <proteinsign_test_launcher> \
  --test_file <test_chain_list.txt> \
  --protein_chain_graphs <chain_graph_dir> \
  --label_data_path <labels.npz> \
  --model_name <saved_model.pdparams> \
  [--cuda -1|0] [--batch_size 32]
```

ProteinSIGN adds angle/edge-node merge hyperparameters such as `--num_angle`, `--merge_e2e`, `--merge_e2n`, `--merge_n2g`, `--num_heads`, and dense hidden dimensions.

### PTHL Train

```bash
python <pthl_train_launcher> \
  --train_file <train_chain_list.txt> \
  --valid_file <valid_chain_list.txt> \
  --protein_chain_graphs <chain_graph_dir> \
  --label_data_path <labels.npz> \
  [--cuda -1|0] [--batch_size 16] [--epochs 200]
```

PTHL combines primary sequence and tertiary graph signals. Always pass explicit file/graph/label paths; some app defaults are machine-specific data locations and should not be trusted.

## PDB Graph Preprocessing Roles

Function-prediction data preparation has four conceptual stages:

1. Download or provide PDB files for listed proteins/chains.
2. Extract chain residue sequences and coordinates.
3. Convert chains to graph representations using a contact-map threshold. Runtime datasets look under a threshold subdirectory such as `<protein_chain_graphs>/10/`; preprocessing scripts format the save directory as zero-padded `<save_dir>/08/` for thresholds below 10, so keep preprocessing output names aligned with the runtime `--cmap_thresh` lookup.
4. Generate label `.npz` files for GO branches such as molecular function, cellular component, or biological process. Label archives also expose metadata keys such as `name`, `counts`, and `idx_goterm_map`, plus per-chain label arrays.

These preprocessing steps can download data and process many structures; get explicit user approval before running them at scale.

## PPI and HelixProtX Routing

- PPI: scoped evidence only states that S2F code will be released later. Do not fabricate runnable commands; route to adjacent protein sequence/function or ask for an external implementation if the user needs PPI now.
- HelixProtX: route broad protein sequence/structure/description any-to-any generation requests here only for high-level planning. The scoped evidence states that full module parameters and LLM code are not open-sourced, provides a Llama demo path, and uses a non-commercial license. Confirm model availability and license fit before attempting inference.

## Evidence Labels

`apps/pretrained_protein/tape/README.md`; `apps/pretrained_protein/tape/train.py`; `apps/pretrained_protein/tape/eval.py`; `apps/pretrained_protein/tape/predict.py`; `apps/protein_function_prediction/DeepFRI/`; `apps/protein_function_prediction/ProteinSIGN/`; `apps/protein_function_prediction/PTHL/`; `apps/protein_function_prediction/datasets_preprocess/PDB/`; `apps/protein_protein_interaction/README.md`; `apps/helixprotx/README.md`.
