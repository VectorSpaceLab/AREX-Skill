# Protein Sequence and Function Troubleshooting

Use this reference to diagnose PaddleHelix protein sequence/function requests before running expensive training, prediction, graph preprocessing, or GPU jobs.

## Unknown or Malformed Residues

Symptoms:

- Validation reports `<unk>` token ids.
- TAPE prediction runs but gives poor or surprising output.
- Lowercase sequences produce many unknown residues.

Likely causes and fixes:

- `ProteinTokenizer` is uppercase and character-based; normalize lowercase sequences to uppercase only if that is biologically appropriate for the user's data.
- In-vocabulary ambiguous/non-standard symbols include `B`, `O`, `U`, `X`, and `Z`; these are not unknown to PaddleHelix.
- Gaps (`-`), stop symbols (`*`), whitespace, FASTA headers, punctuation, and digits map to `<unk>` id `4` unless removed or converted.
- FASTA files must be converted to plain sequence lines before TAPE prediction; the bundled validator can identify headers and emit token ids.

## TAPE Data and Config Failures

| Symptom | Probable cause | Fix |
| --- | --- | --- |
| `Task ... is unsupport` | `model_config.task` is not one of `pretrain`, `seq_classification`, `classification`, `regression` | Correct the config before running |
| Key error for labels | `model_config.label_name` does not exist in the `.npz` shards | Inspect or regenerate shards with the expected label key |
| Empty data iteration | `train_data`, `valid_data`, or `eval_data` points to the wrong directory | Pass a directory containing `.npz` files, not a parent folder or single archive |
| Unexpected default model depth | Config uses old prose keys such as `layer_num`/`head_num` | Use current code keys `n_layers` and `n_heads` |
| Prediction reads FASTA headers as sequences | `predict_data` contains raw FASTA | Convert FASTA records to one sequence per line first |
| TAPE predict rejects README-style flags | README prose mentions stdin/`--model`, but parser expects `--predict_data`/`--predict_model` | Generate commands from parser-backed flags |
| TAPE eval unexpectedly requires GPU/distributed setup | Scoped eval launcher calls `paddle.set_device("gpu")` and initializes Fleet with no `--use_cuda` parser flag | Confirm GPU/Paddle or patch the user's launcher before promising CPU eval |
| Checkpoint load failure | Full model checkpoint and encoder-only checkpoint are mixed up | For warm start, choose full-model `hot_start` or encoder finetune intentionally |

## Missing Checkpoints and Paths

- TAPE `predict` needs `--predict_model`; TAPE `eval` needs `--eval_model`; both need a compatible `--model_config`.
- DeepFRI and ProteinSIGN test launchers require `--model_name` and `--label_data_path`; missing either should be treated as a command-construction error before execution.
- Function-prediction split files, graph directory, label `.npz`, and checkpoint must be aligned to the same protein chain identifiers and label branch.
- Function graph datasets join `--protein_chain_graphs` with `str(cmap_thresh)`; if `chain_graphs/10/` is missing for the default threshold, validation should fail before training/evaluation. For thresholds below 10, preprocessing may write zero-padded folders such as `08/`, so rename or point paths consistently before runtime.
- Do not rely on historical defaults in app scripts; pass explicit paths supplied or confirmed by the user.

## Paddle, PGL, and Optional Dependency Issues

Protein sequence/function workflows are not covered by a base `pahelix` import alone.

- TAPE train/eval/predict requires PaddlePaddle.
- DeepFRI, ProteinSIGN, and PTHL require PaddlePaddle plus PGL and scikit-learn/tqdm-era dependencies matching the app README expectations.
- The function-prediction app READMEs cite Python 3.7, PaddlePaddle 2.2.1, PGL 2.2.2, scikit-learn 1.0.1, and tqdm 4.62.3.
- If import errors mention `paddle`, `pgl`, `rdkit`, `Bio`, or `scipy`, install only the dependency set needed for the user's selected workflow rather than broad PaddleHelix app requirements.

## GPU and Distributed Flags

- TAPE `train` supports CPU/single GPU through `--use_cuda`, and multi-GPU through `paddle.distributed.launch` plus parser-backed `--is_distributed`.
- README prose may mention `--distributed`; prefer the actual scoped parser flag `--is_distributed` unless the user's checkout has changed.
- TAPE `eval` parser evidence may force GPU/distributed setup in some source versions; if CPU eval is needed, inspect the user's launcher version before promising CPU support.
- Function-prediction apps use `--cuda -1` for CPU in parser evidence and `--cuda 0` or another id for GPU.
- Confirm available GPU/Paddle build compatibility before running long jobs.
- Do not start multi-GPU training, large batch graph training, or HelixProtX inference without explicit user approval.

## PDB Graph Data Requirements

DeepFRI, ProteinSIGN, and PTHL are graph workflows. Common failures:

- `protein_chain_graphs` does not contain generated graph files for chains listed in `train_file`, `valid_file`, or `test_file`.
- `label_data_path` points to the wrong GO branch, is not a `.npz`, lacks metadata keys such as `idx_goterm_map`, or lacks entries for the requested chains.
- `cmap_thresh` used during training differs from graph preprocessing assumptions.
- PDB preprocessing dependencies such as Biopython or SciPy are missing.
- Raw PDB files, coordinate extraction output, graph directory, and label `.npz` are mixed from different preprocessing runs.

Safe remediation:

1. Validate path presence, `.npz` label extension, non-empty split files, and threshold graph subdirectory with the bundled helper.
2. Confirm whether the user already has preprocessed graphs and labels.
3. Ask before downloading PDB files or regenerating graph data at scale.
4. Keep chain split files, graph files, and labels together as one dataset version.

## PPI and HelixProtX Caveats

- The scoped PPI evidence only announces future S2F code release. Treat runnable PPI training/evaluation as a gap unless the user provides additional implementation evidence.
- HelixProtX is a multimodal protein generation/inference app, but scoped evidence says full module parameters and LLM code are not open-sourced and the license is non-commercial. Verify model availability, dependency installation, and license fit before any inference attempt.
- If a HelixProtX README command appears inconsistent with normal package-manager usage, verify against the user's environment rather than copying it blindly.

## Evidence Labels

`apps/pretrained_protein/tape/README.md`; `apps/pretrained_protein/tape/train.py`; `apps/pretrained_protein/tape/eval.py`; `apps/pretrained_protein/tape/predict.py`; `pahelix/utils/protein_tools.py`; `pahelix/model_zoo/protein_sequence_model.py`; DeepFRI, ProteinSIGN, PTHL parsers; `apps/protein_function_prediction/datasets_preprocess/PDB/README.md`; `apps/protein_protein_interaction/README.md`; `apps/helixprotx/README.md`.
