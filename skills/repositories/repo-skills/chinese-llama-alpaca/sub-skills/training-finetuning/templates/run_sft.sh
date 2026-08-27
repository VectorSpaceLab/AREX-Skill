#!/usr/bin/env bash
# Template for Chinese-LLaMA-Alpaca supervised instruction fine-tuning with PEFT/LoRA.
# Set required environment variables before running. Validate data first with
# scripts/validate_training_data.py --mode sft.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

: "${MODEL_NAME_OR_PATH:?Set MODEL_NAME_OR_PATH to a HF-format base/merged model path or model id}"
: "${TOKENIZER_NAME_OR_PATH:?Set TOKENIZER_NAME_OR_PATH to a Chinese Alpaca tokenizer path or model id}"
: "${DATASET_DIR:?Set DATASET_DIR to a directory containing .json instruction files}"
: "${OUTPUT_DIR:?Set OUTPUT_DIR to a fresh or intentionally reused SFT output directory}"

NPROC_PER_NODE="${NPROC_PER_NODE:-1}"
PER_DEVICE_TRAIN_BATCH_SIZE="${PER_DEVICE_TRAIN_BATCH_SIZE:-1}"
PER_DEVICE_EVAL_BATCH_SIZE="${PER_DEVICE_EVAL_BATCH_SIZE:-1}"
GRADIENT_ACCUMULATION_STEPS="${GRADIENT_ACCUMULATION_STEPS:-8}"
MAX_SEQ_LENGTH="${MAX_SEQ_LENGTH:-512}"
LEARNING_RATE="${LEARNING_RATE:-1e-4}"
LORA_RANK="${LORA_RANK:-8}"
LORA_ALPHA="${LORA_ALPHA:-32}"
LORA_TRAINABLE="${LORA_TRAINABLE:-q_proj,v_proj,k_proj,o_proj,gate_proj,down_proj,up_proj}"
MODULES_TO_SAVE="${MODULES_TO_SAVE:-embed_tokens,lm_head}"
LORA_DROPOUT="${LORA_DROPOUT:-0.05}"
DEEPSPEED_CONFIG_FILE="${DEEPSPEED_CONFIG_FILE:-${SCRIPT_DIR}/ds_zero2_no_offload.json}"
OVERWRITE_OUTPUT_DIR="${OVERWRITE_OUTPUT_DIR:-false}"
DO_EVAL="${DO_EVAL:-false}"

EXTRA_ARGS=()
if [[ -n "${PEFT_PATH:-}" ]]; then EXTRA_ARGS+=(--peft_path "${PEFT_PATH}"); fi
if [[ -n "${RESUME_FROM_CHECKPOINT:-}" ]]; then EXTRA_ARGS+=(--resume_from_checkpoint "${RESUME_FROM_CHECKPOINT}"); fi
if [[ -n "${MAX_STEPS:-}" ]]; then EXTRA_ARGS+=(--max_steps "${MAX_STEPS}"); fi
if [[ "${OVERWRITE_OUTPUT_DIR}" == "true" ]]; then EXTRA_ARGS+=(--overwrite_output_dir); fi
if [[ "${FORCE_RESIZE_EMBEDDINGS:-false}" == "true" ]]; then EXTRA_ARGS+=(--force_resize_embeddings True); fi
if [[ "${DO_EVAL}" == "true" ]]; then
  : "${VALIDATION_FILE:?Set VALIDATION_FILE when DO_EVAL=true}"
  EXTRA_ARGS+=(--do_eval --evaluation_strategy steps --eval_steps "${EVAL_STEPS:-100}" --validation_file "${VALIDATION_FILE}")
fi

torchrun --nnodes 1 --nproc_per_node "${NPROC_PER_NODE}" "${SKILL_DIR}/scripts/run_clm_sft_with_peft.py" \
  --deepspeed "${DEEPSPEED_CONFIG_FILE}" \
  --model_name_or_path "${MODEL_NAME_OR_PATH}" \
  --tokenizer_name_or_path "${TOKENIZER_NAME_OR_PATH}" \
  --dataset_dir "${DATASET_DIR}" \
  --validation_split_percentage 0.001 \
  --per_device_train_batch_size "${PER_DEVICE_TRAIN_BATCH_SIZE}" \
  --per_device_eval_batch_size "${PER_DEVICE_EVAL_BATCH_SIZE}" \
  --do_train \
  --seed "${SEED:-42}" \
  --fp16 \
  --num_train_epochs "${NUM_TRAIN_EPOCHS:-1}" \
  --lr_scheduler_type cosine \
  --learning_rate "${LEARNING_RATE}" \
  --warmup_ratio 0.03 \
  --weight_decay 0 \
  --logging_strategy steps \
  --logging_steps "${LOGGING_STEPS:-10}" \
  --save_strategy steps \
  --save_total_limit "${SAVE_TOTAL_LIMIT:-3}" \
  --save_steps "${SAVE_STEPS:-200}" \
  --gradient_accumulation_steps "${GRADIENT_ACCUMULATION_STEPS}" \
  --preprocessing_num_workers "${PREPROCESSING_NUM_WORKERS:-8}" \
  --max_seq_length "${MAX_SEQ_LENGTH}" \
  --output_dir "${OUTPUT_DIR}" \
  --ddp_timeout 30000 \
  --logging_first_step True \
  --lora_rank "${LORA_RANK}" \
  --lora_alpha "${LORA_ALPHA}" \
  --trainable "${LORA_TRAINABLE}" \
  --modules_to_save "${MODULES_TO_SAVE}" \
  --lora_dropout "${LORA_DROPOUT}" \
  --torch_dtype float16 \
  --gradient_checkpointing \
  --ddp_find_unused_parameters False \
  "${EXTRA_ARGS[@]}"
