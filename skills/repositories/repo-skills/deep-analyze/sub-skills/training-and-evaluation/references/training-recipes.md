# DeepAnalyze training recipes

This reference distills DeepAnalyze's official development path into reproducible planning steps. It is intentionally a dry-run guide: the official recipes assume large checkpoints, DataScience-Instruct-500K, multi-GPU CUDA, long contexts, DeepSpeed/FSDP, FlashAttention, Liger, Ray, and vLLM. Do not run them until all placeholders are replaced and the environment is proven.

Use `../scripts/render_training_command.py` to print a stage-specific command plan and optional local file checks.

## 1. Inputs and stage order

| Stage | Purpose | Required model input | Required data input | Main output |
| --- | --- | --- | --- | --- |
| Special-token preprocessing | Add DeepAnalyze tags when starting from `DeepSeek-R1-0528-Qwen3-8B`. | Base `DeepSeek-R1-0528-Qwen3-8B` checkpoint. | None. | Tag-extended base checkpoint used by SFT. |
| Single-ability SFT | Teach individual reasoning/table/code/science/instruction-following abilities. | Tag-extended base checkpoint, or an existing DeepAnalyze-compatible checkpoint. | `DataScience-Instruct-500K/reasoning/*` JSON files. | Single-ability checkpoint. |
| Multi-ability cold-start SFT | Teach agentic multi-step data-analysis and research abilities before RL. | Single-ability checkpoint. | `DataScience-Instruct-500K/interation/*` JSON files. The directory name is spelled `interation` in the official recipe. | Cold-start multi-ability checkpoint. |
| Multi-ability RL | Optimize multi-turn DeepAnalyze behavior using SkyRL and `DeepAnalyzeEnv`. | Cold-start checkpoint. | `DataScience-Instruct-500K/RL/*.parquet` plus unzipped `DataScience-Instruct-500K/RL/data/`. | Final RL checkpoint/export directory. |

If the user wants to evaluate rather than train, switch to `benchmark-playgrounds.md`.

## 2. Environment preparation

Recommended separation:

- **SFT environment**: PyTorch/CUDA stack plus the repository's DeepAnalyze-forked `ms-swift` installed editable from the relative training package directory. The package exposes the `swift` console command; `swift sft` uses `torch.distributed.run` automatically when `NPROC_PER_NODE` or `NNODES` is set.
- **RL environment**: SkyRL installed editable from the relative SkyRL directory. Its project metadata requires Python `==3.12.*`. The official launch enters `skyrl-train` and runs a Hydra entrypoint under `examples.deepanalyze.main_deepanalyze`.
- **Serving/evaluation environment**: vLLM and benchmark dependencies. Keep separate unless versions are proven compatible.

Minimal install shape after selecting CUDA/PyTorch versions:

```bash
# SFT package, from the repository root
python -m pip install -e deepanalyze/ms-swift

# RL package, from the repository root, in a Python 3.12 environment
python -m pip install -e deepanalyze/SkyRL
```

Do not mix these editable installs into a production inference environment until the user accepts dependency conflicts.

## 3. Special-token preprocessing

When starting from `DeepSeek-R1-0528-Qwen3-8B`, create a new checkpoint with DeepAnalyze tags before SFT. Do not mutate the original checkpoint in place.

Template:

```bash
python deepanalyze/add_vocab.py \
  --model_path "$MODEL_PATH" \
  --save_path "$SAVE_PATH" \
  --add_tags
```

Validation before SFT:

- `MODEL_PATH` points to the base checkpoint.
- `SAVE_PATH` is a new writable output directory.
- The resulting tokenizer/model can be loaded by the selected SFT stack.
- If starting from `DeepAnalyze-8B`, do not add tokens again unless the user explicitly knows the tokenizer is missing them.

## 4. Single-ability SFT

Working directory: `deepanalyze/ms-swift`.

Default process assumptions:

- `CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7`
- `NPROC_PER_NODE=8`
- `MASTER_PORT=12345`

Required variables:

- `BASE_MODEL`: tag-extended base checkpoint or compatible DeepAnalyze checkpoint.
- `MODEL_SINGLE_ABILITY_PATH`: output checkpoint directory.
- `DATA_DIR`: root of DataScience-Instruct-500K.

Official reasoning data group:

```text
reasoning/SKGInstruct_199989.json
reasoning/TableQA_distillation_39301.json
reasoning/TableQA_refinement_39301.json
reasoning/TableGPT_29448.json
reasoning/file_database_3833.json
reasoning/file_csv_3007.json
reasoning/file_xlsx_3663.json
reasoning/file_any_2520.json
reasoning/math_20000.json
reasoning/code_20000.json
reasoning/science_20000.json
reasoning/instruction_following_20000.json
reasoning/other_19998.json
```

Key SFT settings:

- `train_type=full`
- `torch_dtype=bfloat16`
- `num_train_epochs=3`
- `per_device_train_batch_size=8`
- `gradient_accumulation_steps=4`
- `packing=true`
- `max_length=8192`
- `learning_rate=5e-5`
- `deepspeed=zero3`
- `use_liger_kernel=true`
- `attn_impl=flash_attn`
- `model_type=deepseek_r1_distill`

Render the plan:

```bash
python skills/disco/deep-analyze/sub-skills/training-and-evaluation/scripts/render_training_command.py \
  single \
  --base-model "$BASE_MODEL" \
  --output-model "$MODEL_SINGLE_ABILITY_PATH" \
  --data-dir "$DATA_DIR" \
  --gpus 0,1,2,3,4,5,6,7 \
  --check-files
```

## 5. Multi-ability cold-start SFT

Working directory: `deepanalyze/ms-swift`.

Required variables:

- `MODEL_SINGLE_ABILITY_PATH`: output of single-ability SFT.
- `MODEL_MULTI_ABILITY_PATH`: output checkpoint directory for cold start.
- `DATA_DIR`: root of DataScience-Instruct-500K.

Official multi-ability data group uses the directory spelling `interation`:

```text
interation/data_pipeline_3601.json
interation/data_preparation_3311.json
interation/data_cleaning_1616.json
interation/data_analysis_3936.json
interation/data_insight_1062.json
interation/research_database_818.json
interation/research_xlsx_848.json
interation/research_other_3505.json
interation/research_data_preparation_488.json
interation/research_data_analysis_1339.json
interation/research_data_insight_1351.json
interation/research_report_generation_4327.json
```

Key differences from single-ability SFT:

- `model` is the single-ability checkpoint.
- `per_device_train_batch_size=1`.
- `gradient_accumulation_steps=32`.
- `learning_rate=5e-6`.
- `max_length=32768`.
- DeepSpeed Zero-3, Liger, and FlashAttention remain enabled.

Render the plan:

```bash
python skills/disco/deep-analyze/sub-skills/training-and-evaluation/scripts/render_training_command.py \
  multi-coldstart \
  --previous-stage-model "$MODEL_SINGLE_ABILITY_PATH" \
  --output-model "$MODEL_MULTI_ABILITY_PATH" \
  --data-dir "$DATA_DIR" \
  --gpus 0,1,2,3,4,5,6,7 \
  --check-files
```

## 6. Multi-ability RL with SkyRL

Working directory: `deepanalyze/SkyRL/skyrl-train`.

Required variables:

- `MODEL_COLDSTART_PATH`: cold-start checkpoint from multi-ability SFT.
- `FINAL_MODEL_PATH`: final RL output root. The recipe writes checkpoints under `ckpt` and exports under `export` inside this root.
- `DATA_DIR`: root of DataScience-Instruct-500K.
- `NUM_GPUS`: number of GPUs allocated to policy, reference, and vLLM inference engines.
- `INFERENCE_BACKEND`: official value is `vllm`.

Required RL data:

```text
RL/qa.parquet
RL/datatask.parquet
RL/reseach.parquet
RL/data/                # unzip DataScience-Instruct-500K/RL/data.zip here
```

The `reseach.parquet` filename is spelled this way in the official command. Do not silently rename it unless the user's dataset version differs and they confirm the change.

Main Hydra/SkyRL settings:

- `trainer.algorithm.advantage_estimator=grpo`
- `trainer.epochs=1`
- `trainer.policy.model.path=$MODEL_COLDSTART_PATH`
- `trainer.strategy=fsdp2`
- policy/reference CPU offload enabled
- colocated placement across the selected GPU count
- `trainer.train_batch_size=256`
- `trainer.micro_forward_batch_size_per_gpu=16`
- `trainer.micro_train_batch_size_per_gpu=1`
- `trainer.max_prompt_length=8000`
- `generator.max_input_length=32768`
- `generator.sampling_params.max_generate_length=32768`
- `trainer.policy.optimizer_config.lr=5e-7`
- `generator.backend=vllm`
- local inference engines, NCCL weight sync, async engine enabled
- `generator.n_samples_per_prompt=5`
- `generator.max_turns=30`
- stop token ids `[151676,151645]`
- `environment.env_class=deepanalyze`
- `environment.skyrl_gym.deepanalyze.workspace=$DATA_DIR/RL/data/`
- `trainer.resume_mode=latest`

`DeepAnalyzeEnv` behavior that matters for RL debugging:

- The entrypoint registers environment id `deepanalyze` and maps it to `examples.deepanalyze.deepanalyze_env:DeepAnalyzeEnv`.
- Each environment item must provide `reward_spec` and `data`; optional `workspace_id` selects a nested workspace under the configured RL data workspace.
- The environment expects DeepAnalyze-style tags: `<Analyze>`, `<Code>`, `<Execute>`, and `<Answer>`.
- Python code blocks are executed in a process-local workspace with a short timeout and non-interactive Matplotlib backend.
- QA rewards include exact TableQA answer matching and LLM-as-judge analysis; data-task/open-research rewards may combine code-pass, judgement functions, and turn-count reward.
- If LLM judgement is enabled by the config, make sure the Hydra environment config provides a reachable OpenAI-compatible base URL, API key or accepted placeholder, and judgement model name.

Render the plan:

```bash
python skills/disco/deep-analyze/sub-skills/training-and-evaluation/scripts/render_training_command.py \
  multi-rl \
  --coldstart-model "$MODEL_COLDSTART_PATH" \
  --final-model "$FINAL_MODEL_PATH" \
  --data-dir "$DATA_DIR" \
  --num-gpus 8 \
  --gpus 0,1,2,3,4,5,6,7 \
  --check-files
```

## 7. Pre-launch checklist

Before executing any rendered command:

1. All placeholder paths are replaced by real model, data, and output directories.
2. DataScience-Instruct-500K is present and `RL/data.zip` has been unzipped for RL.
3. Special-token preprocessing was done if starting from the DeepSeek base model.
4. The selected environment imports the package needed by the stage (`swift` for SFT, SkyRL/Ray/Hydra for RL).
5. `nvidia-smi` shows the GPUs requested by `CUDA_VISIBLE_DEVICES`.
6. Long-context memory is plausible for the selected GPU count and sequence lengths.
7. Output directories are empty or the resume/overwrite policy is explicit.
8. For RL, Ray has no stale cluster/session conflict and the judgement endpoint is reachable if judgement rewards are configured.
