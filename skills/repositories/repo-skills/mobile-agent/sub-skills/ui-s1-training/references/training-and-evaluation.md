# UI-S1 Training and Evaluation

## Training command shape

The public training example starts Ray and runs:

```text
python3 -m verl.trainer.main_dapo \
  --config-path=<UI-S1 examples/qwen_gui_static_grpo/config> \
  --config-name=traj_grpo \
  algorithm.adv_estimator=uis1 \
  data.train_files=<train-jsonl> \
  data.val_files=<val-jsonl> \
  actor_rollout_ref.model.path=<Qwen2.5-VL checkpoint> \
  actor_rollout_ref.rollout.name=vllm \
  trainer.project_name=gui_traj_grpo \
  trainer.n_gpus_per_node=8 \
  trainer.nnodes=<world-size>
```

Use `scripts/build_ui_s1_train_command.py` to print a template. The builder intentionally does not call `ray start`, launch vLLM, or train.

## Important Hydra override groups

- `data.*`: train/val JSONL files, batch size, max prompt/response length, truncation.
- `actor_rollout_ref.model.*`: checkpoint path, padding, gradient checkpointing.
- `actor_rollout_ref.actor.*`: learning rate, minibatches, micro-batches, KL loss, FSDP offload/checkpoint contents.
- `actor_rollout_ref.rollout.*`: rollout engine (`vllm`), tensor parallel size, memory utilization, max model length, image limits, samples per prompt.
- `algorithm.*`: UI-S1 estimator, gamma, patch threshold, DAPO/filter group controls.
- `trainer.*`: logger, project/experiment name, GPUs/nodes, save/test frequency, epochs.

## Evaluation command shape

Evaluation scripts read a JSONL file, call a model server helper, parse tagged actions, compare against `check_options`, and write one JSONL result file under the output directory. Use `scripts/build_ui_s1_eval_command.py`.

Evaluation still requires the model serving layer and API utilities expected by the chosen evaluator. The command builder only verifies flags.
