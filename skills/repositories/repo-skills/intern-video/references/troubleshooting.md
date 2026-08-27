# Cross-Cutting Troubleshooting

## Missing data or model paths

**Symptoms:** commands still contain `your_data_path`, `your_model_path`, `train_1.1M.csv`, missing `pretrained_path`, or environment variables such as `INTERNVIDEO2_DATA_PATH`, `INTERNVIDEO2_MODEL_PATH`, `META_DATA_PATH`, `LOAD_FROM`, or `PROCESSOR_PATH` are unset.

**Recovery:** choose the generation-specific sub-skill, then run the root environment checker with `--data-root` and `--model-root`. Replace placeholders before submitting a job. Keep dataset and checkpoint paths outside generated skill files.

## FlashAttention, Apex, DeepSpeed, and CUDA extension failures

**Symptoms:** `ModuleNotFoundError: flash_attn`, `fused_dense_lib`, `dropout_layer_norm`, `apex`, `deepspeed`; CUDA compiler errors; unsupported GPU architecture; torch/CUDA version mismatch.

**Recovery:** first decide whether the workflow actually needs the 6B/large-model CUDA extension path. If yes, match the repo-documented torch/CUDA version, install/build extensions in the target environment, and run a tiny CUDA allocation plus package import before launching training. Do not count CPU import success as proof of a required CUDA workflow.

## Relative import and PYTHONPATH failures

**Symptoms:** InternVideo2 multi-modality demo/config imports fail with modules such as `utils`, `models`, or `easydict` not found.

**Recovery:** run from the correct generation directory or set `PYTHONPATH` so the multi-modality folder is on the module search path. The multi-modality demo guide explicitly discusses changing relative imports or rooting `PYTHONPATH` at that folder.

## SLURM launcher mismatch

**Symptoms:** `srun: command not found`, wrong `PARTITION`, incorrect GPU count, `MASTER_PORT` collision, job exits immediately, or cluster-specific flags such as `--quotatype` are rejected.

**Recovery:** use generation references to identify the intended Python entry point and config, then adapt only the launcher layer. For local smoke work, prefer a one-process `torchrun` or parser/config validation; do not submit a large job just to test routing.

## Large downloads, credentials, and benchmark datasets

**Symptoms:** Hugging Face/Drive/OpenDataLab downloads fail, private benchmark paths are absent, or scripts hard-code placeholder roots.

**Recovery:** stop and ask for storage, credentials, and download approval before fetching large assets. For benchmark evaluations, verify dataset-specific JSON/video layout first with the `datasets` sub-skill.

## Checkpoint/key mismatch

**Symptoms:** missing or unexpected state-dict keys, positional embedding shape mismatch, tokenizer path errors, or wrong text/vision encoder pairing.

**Recovery:** match the model family and branch: Stage1/single-modality visual checkpoints are not interchangeable with Stage2/CLIP multimodal checkpoints; InternVideo3/2.5 MLLM checkpoints use processor/tokenizer conventions from their Hugging Face model families.
