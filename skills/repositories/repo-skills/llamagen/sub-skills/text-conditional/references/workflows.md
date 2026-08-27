# Text-conditioned workflows

## 1. Stage-1 training
Use this when you are training the first text-conditioned LlamaGen stage.

- Wrapper: `scripts/train_t2i_stage1.sh`
- Underlying module: `autoregressive/train/train_t2i.py`
- Required runtime data:
  - VQ checkpoint for the text-conditional tokenizer.
  - Text-image dataset root.
  - Precomputed FLAN-T5 feature cache.
- Common output:
  - `results/` training folders and cloud-save checkpoints.

## 2. Stage-2 training
Use this when you are training the higher-resolution text-conditioned stage.

- Wrapper: `scripts/train_t2i_stage2.sh`
- Underlying module: `autoregressive/train/train_t2i.py`
- Required runtime data:
  - VQ checkpoint for the text-conditional tokenizer.
  - Full and truncated T5 caches when the training recipe expects both.
  - Stage-2 data root.
- Common output:
  - Higher-resolution checkpoints and logs in the standard training folder structure.

## 3. Prompt sampling
Use this when you want to generate images from a fixed prompt set.

- COCO prompts: `scripts/sample_t2i_coco.sh`
- Parti prompts: `scripts/sample_t2i_parti.sh`
- Underlying module: `autoregressive/sample/sample_t2i_ddp.py`
- Important behavior:
  - The script writes an `images/` folder under the sample directory.
  - It also writes `result.jsonl` and `captions.txt` for later inspection or evaluation.

## 4. Evaluation
Use this when you need CLIP / FID-style evaluation on generated text-conditioned batches.

- Wrapper: `scripts/evaluate_t2i.sh`
- Underlying module: `evaluations/t2i/evaluation.py`
- Required inputs:
  - `--fake_dir` pointing at a generated sample tree.
  - `--ref_dir` pointing at the dataset reference root.
  - `--ref_data` and `--ref_type` matching the reference layout.
- Typical output:
  - score text file beside the sample batch.

## 5. T5 cache preparation dependencies
The text-conditioned path expects precomputed T5 features from `data-preparation`.

- The stage-1 and stage-2 training scripts read feature caches, not raw captions.
- If a training or sampling command mentions missing T5 paths, route back to `data-preparation` instead of trying to regenerate them here.
- The `--no-left-padding` option changes the caption tensor layout in sampling; use it only when the prompt embedding layout is intentional.

## Recommended flow
1. Run `data-preparation` to produce the needed T5 cache trees.
2. Train stage 1.
3. Train stage 2.
4. Sample a prompt batch.
5. Evaluate the batch.

## Caution
The repo’s t2i path is sensitive to prompt-file columns, T5 cache location, and left-padding behavior. Check the CLI reference before launching long runs.
