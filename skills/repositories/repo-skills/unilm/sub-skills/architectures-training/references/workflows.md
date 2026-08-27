# Architecture, Decoding, PFPO, and ReSA Workflows

This reference distills command planning patterns for architecture-heavy UniLM umbrella projects. Use the bundled `../scripts/check_training_plan.py` helper to validate a plan and print a safe template; the templates below are not intended to be launched blindly.

## Routing Matrix

| Request | Use this workflow | Key evidence signals | Route away when |
| --- | --- | --- | --- |
| YOCO 1M context, needle, harness eval, or GPT pretraining | YOCO long-context/fairseq planning | `--arch yoco_3b_new`, `--criterion needle_haystack` or `multi_needle`, `--tokens-per-sample`, `--load-ckpt`, `--yoco-model` | It is ordinary UniLM seq2seq fine-tuning; use `language-seq2seq`. |
| Diff-Transformer attention explanation or module integration | Diff-Transformer module notes | `MultiheadDiffAttn`, differential attention, `lambda_init`, FlashAttention V2 design | It asks for downstream generation or multimodal usage; use sibling skills. |
| DeepNet, LongNet, LongViT, RetNet, X-MoE, BitNet architecture selection | Architecture family notes | README-only architecture projects, often with old stack assumptions | It is only retrieval fine-tuning; use `embeddings-retrieval`. |
| GAD/IAD decoding acceleration | Decoding acceleration planning | `--strategy gad`, `--block-size`, `--beta`, `--tau`, AR verifier checkpoint | It asks to train general fairseq models unrelated to GAD/IAD. |
| PFPO math/coding preference optimization | PFPO offline planning | `trainer_base_ds_mul_fs_tp.py`, Hydra `-cp/-cn`, DeepSpeed configs, pseudo feedback | It requires OpenAI/service calls without credentials; keep offline or ask. |
| ReSA long-context math evaluation | ReSA evaluation planning | `--resa_rec_freq`, `--resa_sparse_ratio`, local math eval script | It is general paper recovery or non-UniLM inference. |

## YOCO Long-Context Evaluation

YOCO uses a fairseq-style checkout with `torchrun` wrappers. Source examples show single-process launches for harness evaluation and needle/haystack evaluation, both relying on checkpoint/model directories and optional Apex/Flash-Attention installs.

### Needle or Multi-Needle Plan

Inputs to validate:

- YOCO model directory containing model files.
- Checkpoint file, normally a `checkpoint.pth` under the YOCO model directory.
- Requested context length via `--tokens-per-sample` and `--interval`.
- GPU count matching `--nproc_per_node`; native examples use `1`, but larger runs require explicit memory planning.
- Criterion: `needle_haystack` for one needle, or `multi_needle --needle-num N` for multiple needles.

Safe template:

```bash
torchrun --master-port PORT --nproc_per_node N validate.py \
  --task pseudo \
  --criterion multi_needle --needle-num NEEDLES \
  --batch-size 1 --max-epoch 1 --no-save \
  --tiktoken-model cl100k_base --bf16 \
  --arch yoco_3b_new \
  --load-ckpt CHECKPOINT_PTH \
  --yoco-model YOCO_MODEL_DIR \
  --tokens-per-sample TOKENS \
  --interval TOKENS
```

For a sanity check without launching, run:

```bash
python scripts/check_training_plan.py yoco-needle \
  --checkpoint CHECKPOINT_PTH \
  --model-dir YOCO_MODEL_DIR \
  --tokens-per-sample 1048576 \
  --interval 1048576 \
  --nproc-per-node 1 \
  --needle-num 4
```

### Harness Task Evaluation Plan

Inputs to validate:

- Harness data directory with task data.
- Checkpoint and YOCO model directory.
- Eval task name, e.g. `lambada`, `piqa`, or another supported harness task.
- `--tokens-per-sample` appropriate to the task; source examples use `4096`.

Safe template:

```bash
torchrun --master-port PORT --nproc_per_node N validate.py \
  --data-dir HARNESS_DATA_DIR \
  --criterion harness_eval \
  --task harness_eval \
  --batch-size 4 \
  --eval-data TASK \
  --log-format simple --log-interval 10 \
  --bf16 --tokenizer-pad-to-multiple 8 \
  --arch yoco_3b_new --tiktoken-model cl100k_base \
  --load-ckpt CHECKPOINT_PTH \
  --yoco-model YOCO_MODEL_DIR \
  --tokens-per-sample 4096
```

### YOCO Training Plan

YOCO pretraining expects an infinibatch-style data directory. The README shows a root with `shard/` JSONL files and `json/` index files. Each JSONL line should be one JSON object with at least a text field similar to:

```json
{"text": "<document text>"}
```

Each data-source index JSON should list JSONL shard file paths. Keep shard files around 10K lines or fewer to avoid huge single-file reads.

Safe template:

```bash
torchrun --master-port PORT --nproc-per-node N train.py DATA_ROOT \
  --save-interval-updates 5000 --no-epoch-checkpoints \
  --arch yoco_base --criterion cross_entropy --task gpt \
  --tokens-per-sample 2048 --tokenizer-pad-to-multiple 8 --pad-to-max-len \
  --optimizer adam --adam-betas "(0.9, 0.95)" --adam-eps 1e-06 \
  --clip-norm 2.0 --lr 0.00015 --lr-scheduler polynomial_decay \
  --warmup-updates 50 --weight-decay 0.05 \
  --batch-size 1 --model-parallel-size 1 --update-freq 1 \
  --batch-read-ahead 1000 --total-num-update 300000 \
  --log-format simple --log-interval 10 --disable-validation \
  --tiktoken-model cl100k_base --bf16
```

Do not run training just to answer a planning request; use `references/distributed-training.md` to discuss node/GPU and memory changes.

## Diff-Transformer Module Usage

Diff-Transformer V1 source defines `MultiheadDiffAttn` as a drop-in multi-head attention-style module with differential attention: it projects query/key/value, splits two query/key streams, computes two attention maps, and subtracts one from the other using a learned layer-dependent lambda. The example constructs a small module with:

```python
module = MultiheadDiffAttn(embed_dim=128, depth=0, num_heads=4)
output = module(x, rel_pos=None)
```

Key planning points:

- Inputs are sequence tensors shaped like transformer hidden states; the example uses a small batch/sequence/embed setup for source inspection.
- `rel_pos` can be passed through for rotary/relative position handling depending on the imported implementation.
- V1 contains custom flash-diff variants and mentions customized kernels; use the plain module for inspection and avoid kernel assumptions unless the runtime has the matching flash/xformers components.
- Diff-Transformer V2 changes the parameterization so FlashAttention can be used directly without a custom differential-attention kernel, while preserving grouped-query layout constraints.

Use the helper for a module-plan sanity check:

```bash
python scripts/check_training_plan.py diff-transformer \
  --embed-dim 128 --num-heads 4 --depth 0 --sequence-length 16
```

## DeepNet, LongNet, LongViT, RetNet, X-MoE, and BitNet Notes

These architecture directories are primarily README/source-inspection evidence in this skill; do not assume they are installed together. Use them to route and reason about command plans:

- DeepNet focuses on stable very-deep Transformer scaling and DeepNorm-style initialization.
- LongNet targets dilated attention for very long sequence modeling.
- LongViT applies long-context attention ideas to vision transformers.
- RetNet introduces retention-based sequence modeling; its README notes DeepNet initialization is already integrated, so do not add `--subln` or `--deepnorm` arguments to RetNet commands unless a specific config requires them.
- X-MoE covers sparse mixture-of-experts experiments and usually implies distributed expert parallelism and load-balancing checks.
- BitNet covers low-bit/1-bit Transformer experiments and requires careful kernel/hardware assumptions rather than generic PyTorch expectations.

For command advice, identify the family first, then check `references/distributed-training.md` before proposing distributed or kernel-specific flags.

## GAD and IAD Decoding Acceleration

The decoding subtree includes vendored/forked fairseq code and is intentionally not bundled into this skill. Treat it as evidence for command planning only.

GAD source examples use:

- `data_dir`: directory with fairseq dictionaries and binarized data.
- `--path`: NAT drafter checkpoint.
- `--AR-path`: autoregressive verifier checkpoint.
- `--input-path` and `--output-path` for text IO.
- `--block-size`, `--beta`, `--tau`, `--beam`, and `--strategy gad` to control generalized aggressive decoding.

Safe template:

```bash
python inference.py DATA_DIR --path NAT_DRAFTER_CKPT \
  --user-dir block_plugins --task translation_lev_modified --remove-bpe \
  --max-sentences 20 --source-lang SRC --target-lang TGT \
  --iter-decode-max-iter 0 --iter-decode-eos-penalty 0 --iter-decode-with-beam 1 \
  --gen-subset test --AR-path AR_VERIFIER_CKPT \
  --input-path INPUT_TXT --output-path OUTPUT_TXT \
  --block-size BLOCK --beta BETA --tau TAU --batch BATCH --beam BEAM --strategy gad
```

Validate without launching:

```bash
python scripts/check_training_plan.py gad-decoding \
  --data-dir DATA_DIR --checkpoint NAT_DRAFTER_CKPT --ar-checkpoint AR_VERIFIER_CKPT \
  --input-file INPUT_TXT --output-file OUTPUT_TXT --source-lang en --target-lang de \
  --block-size 4 --beta 1 --tau 0 --batch-size 20 --beam 1
```

IAD uses another vendored fairseq tree and interactive/inference scripts. Apply the same safety rule: inspect command shape, do not copy or run the forked fairseq stack unless the user has an isolated environment and confirms compatibility.

## PFPO Offline Math and Coding Workflows

PFPO combines Hydra configs, DeepSpeed, vLLM inference, preference pair construction, and optional OpenAI/service pseudo-feedback callers. Its requirements pin modern but heavy dependencies such as `torch==2.3.1`, `vllm==0.5.2`, `hydra-core==1.3.2`, `transformers==4.42.4`, `deepspeed==0.13.2`, `fairscale==0.4.13`, and `wandb==0.17.0`.

### Offline Steps

Use offline steps when credentials or services are unavailable:

1. Validate JSON/JSONL prediction files and generated test cases.
2. Run local MBPP-style test-case verification logic in an isolated sandbox if requested and safe.
3. Construct preference pairs from already-generated outputs using `scripts/math_scale/construct_prefer_pair.py`-style inputs.
4. Plan DPO/pDPO training with `trainer_base_ds_mul_fs_tp.py` only after checking DeepSpeed config, GPU count, batch size, and checkpoint paths.

Safe examples to adapt:

```bash
python scripts/math_scale/construct_prefer_pair.py \
  --input_file INPUT_GLOB \
  --output_file PREFERENCE_PAIRS_JSON
```

```bash
torchrun --nnodes NNODES --nproc_per_node GPUS_PER_NODE \
  --node_rank NODE_RANK --master_addr MASTER_ADDR --master_port MASTER_PORT \
  trainer_base_ds_mul_fs_tp.py \
  -cp HYDRA_CONFIG_PATH -cn CONFIG_NAME \
  train_file=PREFERENCE_PAIRS_JSON sft_model_dir=SFT_CHECKPOINT_DIR output_dir=OUTPUT_DIR
```

Validate without launching:

```bash
python scripts/check_training_plan.py pfpo-offline-eval \
  --input-file PREDICTIONS_JSONL \
  --output-file RESULTS_JSON \
  --task math \
  --deepspeed-config train_hybrid_engine_zero2.yaml \
  --nproc-per-node 8
```

### Credentialed Callers

PFPO `openai_api_caller_v1.py` instantiates a Hydra model and logs "Running inference through OpenAI API". `service_api_caller_v1.py` similarly loads examples and post-processes service-style outputs. Both depend on configured services, credentials, and Hydra objects. Do not run them in a dry-run or offline setting.

If asked to run them without credentials, explain that the caller cannot be executed safely and offer one of these alternatives:

- Validate the input JSON/JSONL schema and sample count.
- Verify generated MBPP-style test cases offline with a sandboxed local script.
- Construct preference pairs from existing outputs.
- Produce a credential checklist for a future run.

## ReSA Math Evaluation

ReSA uses sparse decoding plus periodic dense rectification. Its local math script sets `TORCH_IND_SYM_NODE_NO_SYMPY=1`, changes into `llm/`, and launches:

```bash
torchrun --nproc_per_node=1 --nnodes=1 --master_port=29388 eval.py \
  --limit 512 --batch_size 4 \
  --checkpoint_dir CHECKPOINT_DIR --downstream_task math \
  --save_feature resa_0.1_32 \
  --output_folder OUTPUT_DIR \
  --resa_rec_freq 32 \
  --resa_sparse_ratio 0.1
```

Inputs to validate:

- Pretrained checkpoint directory with model/tokenizer artifacts.
- Output directory for JSONL result files.
- Math downstream task selected explicitly.
- ReSA controls: `--resa_rec_freq`, `--resa_sparse_ratio`, and optionally block/local/min block settings if exposed.
- GPU memory: long contexts and sparse kernels still require CUDA-compatible attention kernels.

Validate without launching:

```bash
python scripts/check_training_plan.py resa-math-eval \
  --checkpoint CHECKPOINT_DIR \
  --output-dir OUTPUT_DIR \
  --limit 512 --batch-size 4 \
  --resa-rec-freq 32 --resa-sparse-ratio 0.1 \
  --nproc-per-node 1
```

Result collection scripts expect a result output folder and a JSONL filename, for example a generated file named like `MODEL_resa_0.1_32_local.jsonl`. If filenames or JSONL records differ, diagnose with `references/troubleshooting.md` before suggesting reruns.
