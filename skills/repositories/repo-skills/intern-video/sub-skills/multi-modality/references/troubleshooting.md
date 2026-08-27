# Multi-Modality Troubleshooting

## Relative imports or PYTHONPATH failures

Symptoms:

- `ModuleNotFoundError: utils`
- `ModuleNotFoundError: models`
- `ModuleNotFoundError: easydict`
- Demo or config files work only when run from one exact directory

Fixes:

- Add the multi-modality folder to `PYTHONPATH` before running demo/config helpers.
- Prefer running from the `InternVideo2/multi_modality` directory when using the source scripts.
- The demo guide shows absolute-import rewrites such as `from utils.easydict import EasyDict` and `from models.backbones...` to avoid relative-import ambiguity.

## FlashAttention, Apex, or DeepSpeed imports fail

Symptoms:

- `ModuleNotFoundError: flash_attn`
- `ModuleNotFoundError: fused_dense_lib`
- `ModuleNotFoundError: dropout_layer_norm`
- `ModuleNotFoundError: apex`
- `ModuleNotFoundError: deepspeed`
- CUDA extension build failures or compiler/toolchain errors

Fixes:

- Install only the backend packages required by the selected workflow.
- Match the repo-documented torch/CUDA combination when building FlashAttention2 or other CUDA extensions.
- Build the FlashAttention2 `csrc/fused_dense_lib` and `csrc/layer_norm` extensions only in the target CUDA environment.
- Do not treat a CPU import as proof that a 6B or flash-attention workflow is ready.

## Checkpoint or tokenizer path mismatch

Symptoms:

- The tokenizer tries to download unexpectedly.
- `local_files_only=True` fails for the BERT tokenizer.
- State-dict keys do not match the chosen branch.
- A config points `vision_ckpt_path`, `text_ckpt_path`, or `pretrained_path` at the wrong kind of file.

Fixes:

- Stage2 BERT tokenizers need a local folder, not a checkpoint file path.
- Stage2 vision weights and CLIP vision checkpoints are file paths.
- CLIP branch text and vision assets are different from Stage2 bootstrap checkpoints.
- If the path is meant to be a directory, do not append the file name twice.

## Dataset JSON or media-root mismatch

Symptoms:

- Evaluation returns zero hits or the wrong split size.
- File-not-found errors appear for video/image roots.
- SQLite conversion produces a table but the data loader cannot read the media column.

Fixes:

- Validate that the annotation JSON matches the expected key (`image` or `video`) and caption field.
- Confirm the dataset root points to the original media used by the evaluation split.
- For retrieval evaluation, follow the original JSON splits rather than compressed surrogates.
- For audio/video workflows, confirm the audio path, sample rate, and reader backend are installed.

## Launcher side effects

`tools/run.py` can create output directories, copy the source tree, and submit jobs. If the printed command looks correct but you only wanted a review, use the bundled helper instead of the source submitter.

If a printed launcher still fails, re-check:

- `VL_EXP_DIR` or the selected output root.
- SLURM partition, node count, and GPU count.
- `MASTER_PORT` collisions.
- Whether the config already encodes `evaluate True`, `zero_shot True`, or `deepspeed.enable`.

## Evaluation differences

- Disabling DeepSpeed for evaluation can slightly change retrieval metrics.
- Some configs need `evaluate True` plus `pretrained_path`; a separate `zero_shot True` flag may or may not be necessary.
- If a demo uses a tokenizer or checkpoint path that only exists in a notebook cell, mirror it into the config file before running the helper.
