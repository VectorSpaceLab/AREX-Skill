# Alignment Data and Config

## Preference Dataset Shapes

### `paired_text_to_text`

```json
{
  "type": "paired_text_to_text",
  "instances": [
    {
      "prompt": "Question",
      "chosen": "Preferred answer",
      "rejected": "Rejected answer",
      "margin": 0.5
    }
  ]
}
```

### `paired_conversation`

A full pair of chosen and rejected conversations with `messages` arrays.

### `text_to_scored_textlist`

A prompt plus a list of scored candidate responses.

## Iterative DPO Config

The inspected repository ships an iterative DPO YAML example with these important groups:

- model: `model_name_or_path`, `reference_model_name_or_path`, `reward_model_name_or_path`, `trust_remote_code`
- data: `dataset_path_list`, `conversation_template`, `preprocessing_num_workers`
- pipeline: `output_dir`, `run_name`, `random_seed`, `enable_distributed_inference`, `distributed_inference_num_instances`, `do_response_generation`, `do_scoring`, `do_dpo_align`
- inference: `apply_chat_template`, `num_output_sequences`, `temperature`, `top_p`, `max_new_tokens`, `enable_decode_inference_result`
- vLLM: `use_vllm`, `vllm_gpu_memory_utilization`, `vllm_tensor_parallel_size`, `vllm_inference_batch_size`
- reward scoring: `reward_model_inference_block_size`, `reward_model_inference_batch_size`
- DPO training: `accelerate_config_file`, `bf16`, `num_train_epochs`, `max_steps`, `learning_rate`, `gradient_accumulation_steps`, `loss_type`, `optim`

## Merge-LoRA Notes

The merge step needs the base model path, the LoRA adapter path, and the destination path. The safe default is CPU merging.
