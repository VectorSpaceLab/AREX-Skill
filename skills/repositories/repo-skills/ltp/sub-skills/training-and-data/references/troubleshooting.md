# Training and Data Troubleshooting

## Optional dependency failures

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: hydra` or `pytorch_lightning` | Inference-only install lacks training dependencies. | Install the training dependency group intentionally before train/eval. |
| Logger package import or login error | Online logger config selected without package/credentials. | Set `logger=null` or use a local logger unless credentials are available. |
| `pyrootutils` missing | Train/eval entry point dependency absent. | Install train dependencies or add `pyrootutils` explicitly. |

## Hydra/config failures

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Config group not found | Wrong experiment/trainer/datamodule name or config tree unavailable. | Use `build_train_command.py` with known experiment/trainer names; verify config files are packaged/staged. |
| `_ltp_target_` instantiation error | Custom model component target string cannot be resolved. | Check package imports and model component names; avoid renaming modules without config updates. |
| Override parsing error | Shell quoting or Hydra list syntax issue. | Quote list overrides and pass each override as a separate argument. |

## Data failures

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Missing split file | `train/dev/test` files absent or named incorrectly. | Run the data validator and create all required split files. |
| Vocab lookup errors | Missing or mismatched vocab files. | Keep `vocabs/` with the dataset and regenerate vocabs consistently. |
| Empty dataset after tokenization | Format columns wrong, encoding issue, or all examples exceed filters. | Validate with tiny fixtures; inspect a few parsed examples before training. |
| Sequence too long/truncated | Tokenizer max length is exceeded. | Split long sentences/documents or adjust max length with awareness of memory cost. |

## Eval/checkpoint failures

- `ltp_core.eval` requires `ckpt_path`; the bundled command builder rejects eval commands without it.
- Ensure the checkpoint matches the model/task config and label vocab.
- If the best checkpoint path is empty after training, training code can warn and use current weights; record that limitation in results.

## Device and runtime failures

- CPU is safest for command validation and tiny checks.
- GPU training requires a compatible torch build, visible GPU, and enough memory.
- Distributed trainer configs require launcher/environment variables; do not select them for single-process smoke checks.
- Ask before long-running training, benchmark-scale data loading, or remote backbone downloads.
