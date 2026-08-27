# Reward Training And Evaluation Workflows

This reference distills the IXC-2.5-Reward `training/` and `evaluation/` directories into non-executing plans. It records command shapes, arguments, data layouts, and result signals without running torchrun, downloading benchmarks, or loading the reward model.

## Training environment facts

The reward training README names this baseline stack:

- `torch==2.0.1`
- `transformers==4.33.2`
- `peft==0.8.2`
- `deepspeed==0.12.3`

General requirements are Python 3.8+, PyTorch 1.12+ (2.x recommended), CUDA 11.4+ for GPU users, and flash-attention2 for high-resolution InternLM-XComposer2.5 usage. Full training and LoRA training both require a CUDA-capable model environment; the helper in this skill only renders commands.

## Source launcher shape

The source shell scripts export distributed defaults from `MLP_*` environment variables, then run `torchrun` over `finetune.py`:

```bash
torchrun --nnodes $NNODES --nproc_per_node $GPUS_PER_NODE \
  --node_rank $NODE_RANK --master_addr $MASTER_ADDR --master_port $MASTER_PORT finetune.py \
  --model_name_or_path $MODEL \
  --data_path $DATA \
  --given_num True \
  --bf16 True \
  --fix_vit True \
  --fix_sampler True \
  --use_lora <True-or-False> \
  --hd_num 9 \
  --output_dir <output> \
  --num_train_epochs 1 \
  --batch_size 1 \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 2 \
  --learning_rate 1e-5 \
  --max_length 8192 \
  --deepspeed ds_config_zero2.json \
  --gradient_checkpointing True
```

The source `ds_config_zero2.json` uses DeepSpeed ZeRO stage 2, automatic fp16/bf16 settings, automatic train-batch sizing, and no optimizer offload.

Use the renderer to adapt this safely:

```bash
python scripts/render_reward_training_command.py --mode full --model-path /models/ixc_reward --data-path data.txt --output-dir output/ixc_reward
python scripts/render_reward_training_command.py --mode lora --model-path /models/ixc_reward --data-path data.txt --output-dir output/ixc_reward_lora --gpus-per-node 4
```

The renderer prints shell only; it never executes the command or checks model dependencies.

## Bundled self-contained reward training bundle

For approved execution, use `entrypoints/ixc25-reward-training/`. The bundle packages the source-derived reward `finetune.py`, custom `trainer.py`, data loader, preprocessing helper, DeepSpeed config, source example fixture, and launch wrappers:

```bash
# From the reward-model sub-skill root, validate the bundled source-format fixture.
python scripts/validate_reward_data.py entrypoints/ixc25-reward-training/data.txt --given-num --manifest-base manifest

# Real LoRA training after explicit model/data/GPU approval.
cd entrypoints/ixc25-reward-training
MODEL=/models/internlm-xcomposer2d5-7b-reward DATA=/data/reward_data.txt GPUS_PER_NODE=8 OUTPUT_DIR=/runs/ixc_reward_lora ./launch_lora.sh

# Real full reward training after explicit approval.
MODEL=/models/internlm-xcomposer2d5-7b-reward DATA=/data/reward_data.txt GPUS_PER_NODE=8 OUTPUT_DIR=/runs/ixc_reward_full ./launch_full.sh
```

The wrappers resolve `finetune.py` and `ds_config_zero2.json` from the bundle itself. Prefer absolute `DATA` paths for real runs; the bundled `data.txt` is only a small format fixture.

After LoRA training, merge the reward adapter with the bundled reward merge entrypoint:

```bash
cd entrypoints/ixc25-reward-training
python merge_reward_lora.py \
  --adapter-model-name /runs/ixc_reward_lora \
  --base-model-name /models/internlm-xcomposer2d5-7b-reward \
  --output-name /runs/ixc_reward_merged
```

This entrypoint is adapted from the reward README's PEFT loading snippet and writes a standalone merged model directory.

## Full versus LoRA reward training

| Mode | Source script | Key flags | Default output | Notes |
| --- | --- | --- | --- | --- |
| Full parameter | `script_train.sh` | `--use_lora False`, `--fix_vit True`, `--fix_sampler True`, `--bf16 True` | `output/ixc_reward` | Updates all unfrozen parameters selected by the script; still uses source launcher freezes for ViT and sampler. |
| LoRA | `script_train_lora.sh` | `--use_lora True`, `--lora_r 512`, `--fix_vit True`, `--fix_sampler True`, `--bf16 True` | `output/ixc_reward_lora` | Saves an adapter. Prefer an absolute local base model path because adapter configs may record the base path. |

`finetune.py` defines LoRA target modules:

- `attention.wqkv`
- `attention.wo`
- `feed_forward.w1`
- `feed_forward.w2`
- `feed_forward.w3`

The training README states `hd_num` defaults to 18 in the data/model code, but the shipped reward shell launchers pass `hd_num=9`. Lower `hd_num` and `max_length` first when resolving OOM.

## Important training arguments

| Argument | Meaning | Source behavior / planning note |
| --- | --- | --- |
| `model_name_or_path` | Base or reward checkpoint path/model id | README has a documented typo `internlm/iinternlm-xcomposer2d5-7b-reward`; use `internlm/internlm-xcomposer2d5-7b-reward` or a local checkpoint. |
| `data_path` | JSON list or `data.txt` manifest | Source scripts use `data.txt` with `--given_num True`. Validate first with `validate_reward_data.py`. |
| `given_num` | Interpret manifest second column as thousands | `1` means 1,000 examples per epoch. If false, the second column is a ratio. |
| `fix_vit` | Freeze ViT encoder | README describes mode defaults, but source scripts pass `True` for both full and LoRA. |
| `fix_sampler` | Freeze projection/sampler after ViT | Source scripts pass `True` for both full and LoRA. |
| `hd_num` | Dynamic image partition patch budget | Source launchers and reward eval scripts commonly use `9`; data/model defaults may be `18`. |
| `max_length` | Maximum conversation token length | Source launchers use `8192`; README notes `16384` default and up to `24000` on 80G A100 with flash-attn2. |
| `deepspeed` | DeepSpeed config path | Source uses `ds_config_zero2.json`; make path valid from the training working directory. |

## Evaluation benchmark layouts

All evaluation scripts load `internlm/internlm-xcomposer2d5-7b-reward`, set `torch.set_grad_enabled(False)`, attach the tokenizer to the model, set a seed, run CUDA fp16 inference, and incrementally write `results.json` in the benchmark directory. They require model weights, benchmark data, CUDA, and extra data libraries. This skill records layouts only.

| Benchmark | Directory | Required local data | Model call | Result signal |
| --- | --- | --- | --- | --- |
| RewardBench | `evaluation/reward_bench/` | `filtered-00000-of-00001.parquet` from `allenai/reward-bench` placed beside `inference.py` | `get_scores([chosen_chat, rejected_chat], [[]] * 2)` over text-only prompt/chosen/rejected rows | `results.json` list with `score_chosen` and `score_rejected`; accuracy by mapped subset (`Chat`, `Chat Hard`, `Safety`, `Reasoning`) and `all` printed. |
| RM-Bench | `evaluation/rm_bench/` | `total_dataset.json` from THU-KEG/RM-Bench placed beside `inference.py` | `get_scores` over six text-only chats: three chosen styles and three rejected styles, with `max_length=16384`, `hd_num=9` | `results.json` list with `score_chosen` and `score_rejected` arrays; computes 3x3 pairwise matrix and prints `hard_acc`, `normal_acc`, `easy_acc`, `avg_acc`. |
| VL-RewardBench | `evaluation/vl_rewardbench/` | `combined_data_tagged.jsonl` plus extracted `images/` tree containing `povid/`, `wildvision-battle/`, and related folders | Randomizes the two responses, builds two visual chats, and calls `rank([chat_1, chat_2], [image, image], max_length=16384, hd_num=9)` | `results.json` with per-row correctness arrays and randomization trace; prints General, Hallucination, Reasoning, Overall, and Macro accuracy. |

### RewardBench input expectations

The script expects a parquet file with fields such as `prompt`, `chosen`, `rejected`, and `subset`. It maps fine-grained subsets into four groups. Local scoring is pairwise: a row is correct when `score_chosen > score_rejected`.

### RM-Bench input expectations

The script expects each JSON row to include `prompt`, `chosen`, and `rejected`. `chosen` and `rejected` each contain three response variants in the order concise, detailed plain, and detailed markdown. Accuracy is computed across all nine chosen/rejected style comparisons.

### VL-RewardBench input expectations

The JSONL rows include `query`, `response` with two candidate responses, `human_ranking`, and `image_path`. Images are rooted under the local `images/` directory described by the README. Category membership is inferred from image-path substrings: `reasoning_tasks`, `vlfeedback`, `wildvision-battle`, `povid`, `rlhf-v`, and `rlaif-v`.

## Execution approval gate

Before any real training or evaluation run, confirm:

1. Local model/checkpoint path or approved model download.
2. CUDA devices, dtype, flash-attn/deepspeed/peft compatibility, and VRAM budget.
3. Validated preference data or benchmark data layout.
4. Output directory outside the runtime skill tree.
5. Whether the run is expected to take minutes, hours, or a distributed cluster job.

If any model/data/GPU dependency is missing, return a plan and mark the native workload as unverified rather than running a partial command.
