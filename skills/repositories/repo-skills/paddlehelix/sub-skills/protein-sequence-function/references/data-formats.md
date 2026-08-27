# Protein Data Formats

Use this reference to validate user inputs before building PaddleHelix protein sequence or function commands.

## Plain Sequences and FASTA

- TAPE prediction parser evidence reads a plain text file: one non-empty protein sequence per line.
- FASTA headers are not consumed by the TAPE prediction parser directly. Convert FASTA records to plain sequence lines before invoking TAPE prediction.
- The bundled `scripts/validate_protein_inputs.py` accepts `--sequence`, `--fasta`, and `--predict-data` so agents can validate mixed FASTA/plain inputs before conversion.
- Preserve case when checking source behavior: the PaddleHelix tokenizer vocabulary is uppercase, so lowercase letters become `<unk>` unless the caller normalizes them before prediction.
- Interior whitespace, gap symbols, stop codons, and punctuation are not special-cased by `ProteinTokenizer`; they map to `<unk>`.

## ProteinTokenizer Vocabulary

`ProteinTokenizer.gen_token_ids(sequence)` wraps each sequence with `<cls>` and `<sep>` and then maps each character to an integer id.

| Token class | Tokens | IDs |
| --- | --- | --- |
| Special | `<pad>`, `<mask>`, `<cls>`, `<sep>`, `<unk>` | `0`, `1`, `2`, `3`, `4` |
| Residue/ambiguous symbols | `A B C D E F G H I K L M N O P Q R S T U V W X Y Z` | `5` through `29` |

Important consequences:

- `B`, `O`, `U`, `X`, and `Z` are in-vocabulary for PaddleHelix, even though some pipelines may treat them as ambiguous or non-standard.
- Any other character maps to `<unk>` id `4`; unknown residues do not automatically fail the model.
- Transformer and ResNet encoders include positional embeddings with a source max position length of `3000`; very long sequences need explicit handling before inference. The bundled validator warns when an input sequence exceeds this limit.

## TAPE NPZ Directories

TAPE train/eval data arguments point to directories, not single files. Each directory can contain multiple `.npz` shards.

Common keys:

| Key | Role |
| --- | --- |
| `token_ids` | Flattened protein token ids across examples |
| `lengths` | Sequence lengths used to slice `token_ids` back into examples |
| label key from `model_config.label_name` | Labels for supervised tasks, commonly `labels`, `labels3`, or another task-specific key |

Task-specific expectations:

- `pretrain`: requires `token_ids` and `lengths`; masked-language labels are generated during dataloader iteration.
- `seq_classification`: label arrays align per token; labels are padded with `-1` for ignored positions.
- `classification` and `regression`: labels are per sequence rather than per token.

## TAPE Model Config JSON

A minimal sequence-classification config resembles:

```json
{
  "model_name": "secondary_structure",
  "task": "seq_classification",
  "class_num": 3,
  "label_name": "labels3",
  "model_type": "transformer",
  "hidden_size": 512
}
```

Recognized task keys:

- `task`: one of `pretrain`, `seq_classification`, `classification`, or `regression`.
- `model_type`: one of `transformer`, `lstm`, or `resnet`.
- `class_num`: required for classification heads when the class count differs from the default.
- `label_name`: required when the NPZ label key is not the default `labels`.
- `emb_dim`, `hidden_size`, `n_layers`, `n_heads`, `kernel_size`, `dropout`, and `weight_decay`: model/hyperparameter controls.

Source code uses `n_layers`, `n_heads`, and `kernel_size`; older prose may mention `layer_num`, `head_num`, and `filter_num`. If a config only uses older names, the current model code will fall back to default layer/head/filter values.

## TAPE Path Roles

| Argument role | Expected value | Common failure |
| --- | --- | --- |
| `train_data`, `valid_data`, `eval_data` | Directory of `.npz` shards | Passing a single file or missing label key |
| `predict_data` | Plain sequence file, one sequence per line | Passing FASTA with headers directly |
| `model_config` | JSON model/task config | Unsupported `task` or legacy key names silently ignored |
| `init_model`, `eval_model`, `predict_model` | Paddle checkpoint/state path | Wrong checkpoint scope for full model vs encoder-only warm start |

## Function-Prediction Graph Data

DeepFRI, ProteinSIGN, and PTHL consume PDB-derived chain graph data rather than raw sequence-only input.

| Input | Role |
| --- | --- |
| `train_file`, `valid_file`, `test_file` | Text files listing protein chain identifiers, one per line |
| `protein_chain_graphs` | Parent directory containing contact-threshold graph subdirectories; runtime datasets join `str(cmap_thresh)` such as `10/`, while preprocessing writes zero-padded names such as `08/` for threshold 8 |
| `label_data_path` | `.npz` label mapping for a GO branch such as molecular function, cellular component, or biological process |
| `model_name` | Saved model state for evaluation/test launchers |
| `cmap_thresh` | Contact-map threshold used when constructing graphs; default evidence commonly uses `10` |

Preprocessing expectations:

1. PDB files must exist or be downloaded from a user-approved source.
2. Chain sequences and coordinates are extracted from PDB files.
3. Chain graphs are created from sequence/coordinate data and contact thresholds.
4. Label `.npz` files are generated from annotation TSVs.

Do not substitute raw FASTA or plain sequences for `protein_chain_graphs`; graph models expect graph features and labels aligned to chain identifiers.

Graph/label details visible in app dataset code:

- DeepFRI graph records use keys such as `seq`, `n2n_edges`, and `n2n_edge_dist` under the threshold directory.
- ProteinSIGN graph records add edge-angle features such as `e2e_edges` and `e2e_polar_ang`.
- PTHL graph records expect local-frame/vector features such as `coords`, `cb_coords`, `local_sys`, `pos_in_chain`, and `v_feats`-derived inputs.
- Label `.npz` files should contain global metadata (`name`, `counts`, `idx_goterm_map`) and chain-id keys matching the split files.

## Validator Scope

`scripts/validate_protein_inputs.py` is intentionally dependency-light:

- It prints PaddleHelix-compatible token ids with `<cls>`/`<sep>` boundaries and `<unk>` counts.
- It parses FASTA or plain sequence files and warns about lowercase, whitespace, punctuation, gaps, stop symbols, and sequences longer than 3000 tokens.
- It checks TAPE model config JSON for supported `task` and `model_type`, warns on legacy `layer_num`/`head_num`, and can parse extra `--json-config` files.
- It verifies local path existence for TAPE and function workflows and checks that function graph directories contain a `--cmap-thresh` subdirectory, accepting the plain numeric form and the zero-padded form written by preprocessing scripts.

## Evidence Labels

`pahelix/utils/protein_tools.py`; `apps/pretrained_protein/tape/data_gen.py`; `apps/pretrained_protein/tape/configs/`; `apps/pretrained_protein/tape/predict.py`; `apps/protein_function_prediction/datasets_preprocess/PDB/README.md`; DeepFRI, ProteinSIGN, and PTHL train/test parsers.
