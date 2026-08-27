# Qwen-VL evaluation troubleshooting

## CUDA / distributed launch

- The official benchmark inference scripts use `torch.distributed` and NCCL.
- If a script hangs at launch, confirm the GPU count, `WORLD_SIZE`, `RANK`, `MASTER_ADDR`, and `MASTER_PORT` settings before changing the code.
- If the user only wants a CLI parse or data conversion step, prefer the CPU-capable helpers instead of a distributed run.

## Dataset / layout errors

Symptoms:

- File-not-found errors for `data/.../*.jsonl` or benchmark TSV/JSON files.
- `KeyError` for a dataset key such as `vqav2_val` or `mmbench_test_20230712`.
- Empty or malformed JSONL results because the converter was pointed at the wrong root.

Recovery:

1. Check [data-layouts.md](data-layouts.md).
2. Confirm the split name matches the script's dataset key table.
3. Make sure the local images and annotations were actually downloaded.

## VQA scoring issues

- `vqa.py` and `vqa_eval.py` assume the standard VQA annotation/question layout.
- `infographicsvqa_eval.py` expects a ground-truth JSON and a submission JSON with `questionId` and `answer` fields.
- If ANLS or exact accuracy looks wrong, inspect whether the answer text was normalized before scoring.

## MMBench issues

- The converters expect the official TSV layout and will save images into a sibling `images/` directory.
- Prediction files must match the `index` field expectations used by the evaluation helpers.
- If the consistency-constrained evaluation is used, keep the repeated-cycle indexing behavior in mind.

## SEED-Bench issues

- Image conversion is CPU-friendly and only needs the local question JSON plus image root.
- Video conversion may require Decord or an alternate decoder plus local video assets.
- The bundled environment intentionally omitted Decord because the platform-specific install was not clean; treat video conversion as optional unless you have prepared a compatible decoder.

## MME / TouchStone

- `get_images.py` from the source repo is not bundled as an executable helper because it mutates local directories and assumes external hard-coded dataset paths.
- TouchStone is documented as methodology/reference-only here; there is no bundled judge pipeline.

## Model / checkpoint problems

- If the script loads a checkpoint but produces nonsense metrics, confirm you selected the expected checkpoint family (`Qwen-VL` vs `Qwen-VL-Chat`) and that the model weights were fully downloaded.
- Many benchmark runs use `device_map='cuda'`; a CPU-only import is not a substitute for the actual distributed forward pass.

## Submission-format errors

- For MMBench and similar tasks, make sure the output file name and column names match the benchmark's expected submission format.
- For SEED-Bench, concatenate the per-rank result shards only after the distributed run finishes.
