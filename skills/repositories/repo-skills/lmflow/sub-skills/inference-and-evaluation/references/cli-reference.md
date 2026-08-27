# Inference and Evaluation CLI Reference

## `InferencerArguments`

Important fields:

- `device`
- `inference_batch_size`
- `temperature`
- `repetition_penalty`
- `max_new_tokens`
- `do_sample`
- `use_beam_search`
- `num_output_sequences`
- `top_p`
- `top_k`
- `apply_chat_template`
- `inference_engine`
- `inference_tensor_parallel_size`
- `inference_data_parallel_size`
- `inference_gpu_memory_utilization`
- `inference_max_model_len`
- `save_inference_results`
- `inference_results_path`
- `return_logprob`
- `enable_deterministic_inference`
- `attention_backend`

## `EvaluatorArguments`

Important fields:

- `metric`
- `answer_type`
- `prompt_structure`
- `deepspeed`
- `output_dir`
- `use_wandb`
- `save_results`
- `results_path`
- `save_inference_results`
- `inference_results_path`
- `max_new_tokens`
- `minibatch_size`

## `BenchmarkingArguments`

Important fields:

- `dataset_name`
- `lm_evaluation_metric`
- `answer_type`
- `prompt_structure`
- `metric`

## Practical Notes

- `save_results` and `results_path` are deprecated aliases; prefer the `save_inference_results` and `inference_results_path` pair.
- `return_logprob` is meaningful for SGLang-style deterministic routes.
- `inference_engine` should match the installed backend extra.
- `dataset_path=None` is used by interactive shell examples, but the batch evaluation route expects a real dataset path.
