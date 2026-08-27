#!/usr/bin/env bash
set -euo pipefail
set -x

: "${VERL_DIR:?Set VERL_DIR to the VERL checkout}"
: "${VENV_PATH:?Set VENV_PATH to the Python env used for VERL}"
: "${MODEL_PATH:?Set MODEL_PATH to the structure-recovery checkpoint}"
: "${TRAIN_DATA:?Set TRAIN_DATA to the training Parquet file}"
: "${VAL_DATA:?Set VAL_DATA to the validation Parquet file}"

REWARD_VARIANT="${REWARD_VARIANT:-exe_type}"
NUM_NODES="${NUM_NODES:-2}"
GPUS_PER_NODE="${GPUS_PER_NODE:-8}"
KL_COEF="${KL_COEF:-0.01}"
TOTAL_EPOCHS="${TOTAL_EPOCHS:-2}"
SAVE_FREQ="${SAVE_FREQ:-25}"
TEST_FREQ="${TEST_FREQ:-25}"
WANDB_PROJECT_VAL="${WANDB_PROJECT_VAL:-sk2decompile}"
WANDB_ENTITY_VAL="${WANDB_ENTITY_VAL:-}"
WANDB_API_KEY_VAL="${WANDB_API_KEY_VAL:-}"

source "${VENV_PATH}/bin/activate"
cd "${VERL_DIR}"

export UCX_IB_PCI_RELAXED_ORDERING=1
export NCCL_IB_PCI_RELAXED_ORDERING=1
export NCCL_IB_TIMEOUT=22
export NCCL_DEBUG=INFO
export TRANSFORMERS_OFFLINE=0
export TORCH_NCCL_AVOID_RECORD_STREAMS=1
export NCCL_NVLS_ENABLE=0
export NCCL_IB_DISABLE=0
export CUDA_DEVICE_MAX_CONNECTIONS=1

TASK_NAME="sk2decompile_struct-rl-${REWARD_VARIANT}"
LOG_DIR="${VERL_DIR}/logs"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/${TASK_NAME}.log"
ERR_FILE="${LOG_DIR}/${TASK_NAME}.err"

export WANDB_API_KEY="${WANDB_API_KEY_VAL}"
export WANDB_ENTITY="${WANDB_ENTITY_VAL}"
export WANDB_PROJECT="${WANDB_PROJECT_VAL}"
export WANDB_NAME="${TASK_NAME}"
export WANDB_MODE='online'

python3 -m verl.trainer.main_ppo --config-path=config \
    --config-name='ppo_trainer-lm4dc.yaml' \
    algorithm.adv_estimator=grpo \
    data.train_files="${TRAIN_DATA}" \
    data.val_files="${VAL_DATA}" \
    data.train_batch_size=128 \
    data.max_prompt_length=1024 \
    data.max_response_length=2048 \
    data.filter_overlong_prompts=True \
    data.truncation='error' \
    actor_rollout_ref.model.path="${MODEL_PATH}" \
    actor_rollout_ref.actor.optim.lr=1e-6 \
    actor_rollout_ref.model.use_remove_padding=True \
    actor_rollout_ref.actor.ppo_mini_batch_size=32 \
    actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=4 \
    actor_rollout_ref.actor.use_kl_loss=True \
    actor_rollout_ref.actor.kl_loss_coef="${KL_COEF}" \
    actor_rollout_ref.actor.kl_loss_type=low_var_kl \
    actor_rollout_ref.actor.entropy_coeff=0 \
    actor_rollout_ref.model.enable_gradient_checkpointing=False \
    actor_rollout_ref.actor.fsdp_config.param_offload=False \
    actor_rollout_ref.actor.fsdp_config.optimizer_offload=False \
    actor_rollout_ref.rollout.log_prob_micro_batch_size_per_gpu=1 \
    actor_rollout_ref.rollout.tensor_model_parallel_size=1 \
    actor_rollout_ref.rollout.name=vllm \
    actor_rollout_ref.rollout.gpu_memory_utilization=0.80 \
    actor_rollout_ref.rollout.n=16 \
    actor_rollout_ref.ref.log_prob_micro_batch_size_per_gpu=4 \
    actor_rollout_ref.ref.fsdp_config.param_offload=True \
    algorithm.use_kl_in_reward=False \
    trainer.critic_warmup=0 \
    trainer.logger=['console','wandb'] \
    trainer.project_name='sk2decompile_rl' \
    trainer.experiment_name="${TASK_NAME}" \
    trainer.default_local_dir="${VERL_DIR}/checkpoints/${TASK_NAME}" \
    trainer.n_gpus_per_node="${GPUS_PER_NODE}" \
    trainer.nnodes="${NUM_NODES}" \
    trainer.save_freq="${SAVE_FREQ}" \
    trainer.test_freq="${TEST_FREQ}" \
    trainer.total_epochs="${TOTAL_EPOCHS}" "$@" \
    > >(tee -a "${LOG_FILE}") \
    2> >(tee -a "${ERR_FILE}" >&2)

echo "STDOUT saved to: ${LOG_FILE}"
echo "STDERR saved to: ${ERR_FILE}"
