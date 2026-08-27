# Troubleshooting

## Install and import failures

- `ImportError` from `torch` usually means the environment has the wrong wheel family or a conflicting binary dependency. Reinstall a torch build that matches the target backend and re-run `python -m pip check`.
- If you see a NumPy ABI warning, pin `numpy<2` and retry the imports.
- Missing optional packages produce straightforward import errors in advanced flows: install `sentencepiece`, `safetensors`, `pandas`, `gradio`, or `bitsandbytes` only when the corresponding workflow is in scope.

## CUDA or backend failures

- `torch.cuda.is_available()` false on a GPU host usually means the wheel/backend mix is wrong or CUDA libraries are missing.
- If a CUDA smoke fails, check the wheel tag, driver compatibility, and `python -c "import torch; print(torch.version.cuda)"`.
- `bitsandbytes` fine-tuning and 8-bit loading require CUDA and are not CPU substitutes.

## Data and config failures

- `build_vocab` and `train` both require valid YAML corpus definitions with source/target paths.
- Source features require `inferfeats` in the corpus transforms and a matching `n_src_feats` / `src_feats_defaults` count.
- `lambda_align` is incompatible with on-the-fly tokenization and token-deleting transforms.
- `world_size` and `gpu_ranks` must agree.
- `gold_align` requires `report_align` and a target file.

## Inference and server failures

- Missing model paths, tokenizer model paths, or CTranslate2 artifacts are the most common translation/server failures.
- REST configs must define `models`, and tokenizers must specify the right type and path fields.
- If the server or translation path reports a missing tokenizer, check `sentencepiece` or `pyonmttok` availability and the model-root-relative paths.

## Conversion failures

- Model conversion utilities usually fail because the wrong checkpoint family, tokenizer, or shard layout was selected.
- `release_model` and `lora_weights` require compatible checkpoints from the same model family.
- `extract_vocabulary.py` needs the correct side (`src` or `tgt`).

## Recovery pattern

1. Re-run the relevant `--help` or validation helper from the skill scripts.
2. Check file existence and relative paths.
3. Confirm the package version and dependency set with `python -m pip check`.
4. If a GPU path is involved, confirm CUDA with `scripts/check_cuda.py`.
