# Workflows

## Standard fine-tuning

1. Load a base model and processor.
2. Prepare DaTikZ-style training data, often from a parquet file or a dataset loader.
3. Train the model with the desired sketch ratio and checkpoint policy.
4. Save the resulting checkpoint directory and keep the training configuration that produced it.

## Projection pretraining

1. Load the base model.
2. Stream or sample a large figure dataset.
3. Run a lightweight projection pretraining phase before full fine-tuning.
4. Preserve the output directory because later workflows may depend on the saved projector.

## Refinement / GRPO

1. Load the base model with the correct inference precision and attention implementation.
2. Build the reward dataset from the available figure sources.
3. Ensure TeX-backed compile/rasterize support is available.
4. Use the strictness flag when compile failures should count as fatal during reward scoring.

## Sketchification

1. Build or load the source figure dataset.
2. Run sketchification on GPU hardware and store the generated parquet artifacts.
3. Reuse the produced sketches as training inputs for later fine-tuning.

## TikZero adapters

1. Pretrain the adapter against the embedding model.
2. Fine-tune end-to-end with the adapter checkpoint and optional caption conditioning.
3. Keep the embedding model identity consistent between pretraining and fine-tuning.
4. When you invoke `examples/tikzero/pretrain.py` or `examples/tikzero/train.py` directly, seed the distributed environment variables (`RANK`, `WORLD_SIZE`, `MASTER_ADDR`, and a free `MASTER_PORT`) before `--help` or any debug run.

## Typical decision points

- Whether the run needs `deepspeed`.
- Whether `gradient_checkpointing` is worth the memory trade-off.
- Whether the chosen model family is legacy / v1 or the newer v2 path.
- Whether the output directory should resume or start fresh.
