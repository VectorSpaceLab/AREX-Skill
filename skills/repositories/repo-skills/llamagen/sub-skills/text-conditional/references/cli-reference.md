# CLI reference

All wrappers are intended to be run from the repository root.

## Training

### `scripts/train_t2i_stage1.sh`
- Wrapper env vars: `nnodes`, `nproc_per_node`, `node_rank`, `master_addr`, `master_port`
- Launches: `autoregressive/train/train_t2i.py`
- Wrapper defaults:
  - `--vq-ckpt ./pretrained_models/vq_ds16_t2i.pt`
  - `--data-path /path/to/laion_coco50M`
  - `--t5-feat-path /path/to/laion_coco50M_flan_t5_xl`
  - `--dataset t2i`
  - `--image-size 256`
- Common extra flags:
  - `--gpt-model`
  - `--gpt-ckpt`
  - `--cls-token-num`
  - `--mixed-precision {none,fp16,bf16}`
  - `--no-compile`
  - `--no-local-save`

### `scripts/train_t2i_stage2.sh`
- Same launcher surface as stage 1.
- Wrapper defaults:
  - `--vq-ckpt ./pretrained_models/vq_ds16_t2i.pt`
  - `--data-path /path/to/high_aesthetic_10M`
  - `--t5-feat-path /path/to/high_aesthetic_10M_flan_t5_xl`
  - `--short-t5-feat-path /path/to/high_aesthetic_10M_trunc_flan_t5_xl`
  - `--dataset t2i`
  - `--image-size 512`

## Sampling

### `scripts/sample_t2i_coco.sh`
- Launches: `autoregressive/sample/sample_t2i_ddp.py`
- Wrapper defaults:
  - `--prompt-csv evaluations/t2i/coco_captions.csv`
  - `--sample-dir samples_coco`
  - `--vq-ckpt ./pretrained_models/vq_ds16_t2i.pt`
- Useful flags passed through to the Python script:
  - `--gpt-model`
  - `--gpt-ckpt`
  - `--image-size`
  - `--cfg-scale`
  - `--top-k`
  - `--top-p`
  - `--temperature`
  - `--no-left-padding`

### `scripts/sample_t2i_parti.sh`
- Same as COCO sampling, but defaults to `evaluations/t2i/PartiPrompts.tsv` and `samples_parti`.

## Evaluation

### `scripts/evaluate_t2i.sh`
- Launches: `evaluations/t2i/evaluation.py`
- Required args:
  - `--fake_dir`
  - `--ref_dir`
- Common args:
  - `--ref_data coco2014`
  - `--ref_type val2014`
  - `--eval_res 256`
  - `--batch_size`
  - `--how_many`
  - `--clip_model4eval`

## Underlying Python entry points

### `autoregressive/train/train_t2i.py`
- Core flags to know:
  - `--data-path`, `--t5-feat-path`, `--cloud-save-path`
  - `--short-t5-feat-path`
  - `--gpt-model {GPT-B,GPT-L,GPT-XL,GPT-XXL,GPT-XXXL,GPT-1B,GPT-3B,GPT-7B}`
  - `--vq-model {VQ-16,VQ-8}`
  - `--image-size {256,384,512}`
  - `--downsample-size {8,16}`
  - `--gpt-type t2i`

### `autoregressive/sample/sample_t2i_ddp.py`
- Core flags to know:
  - `--prompt-csv`
  - `--sample-dir`
  - `--t5-path`
  - `--t5-model-type`
  - `--no-left-padding`
  - `--gpt-model`
  - `--gpt-ckpt`
  - `--vq-ckpt`
  - `--image-size`
  - `--cfg-scale`
- Prompt-file note:
  - The sampler reads a `Prompt` column from the TSV / CSV source.

### `evaluations/t2i/evaluation.py`
- The evaluator expects a generated sample tree with an `images/` subfolder.
- It writes scores next to the sample batch.
