# LMFlow Inference and Evaluation Workflows

## Hugging Face Inference

Use the base LMFlow inferencer when the user wants the simplest generation path.

Typical inputs:

- `model_name_or_path`
- `dataset_path`
- `conversation_template` when the input is conversational
- `max_new_tokens`
- `temperature`
- `prompt_structure`

## Evaluator

Use the evaluator when the task is about metrics rather than raw generation.

Typical inputs:

- `metric` such as `accuracy` or `nll`
- `answer_type`
- `prompt_structure`
- `deepspeed` config path when the workflow expects it

## vLLM

Use the vLLM route only when the `vllm` extra is installed in a dedicated environment.

Typical additions:

- `inference_engine=vllm`
- `inference_gpu_memory_utilization`
- `inference_tensor_parallel_size`
- `num_output_sequences`
- `inference_max_model_len`

## SGLang

Use the SGLang route only when the `sglang` extra is installed in a dedicated environment.

Typical additions:

- `inference_engine=sglang`
- `enable_deterministic_inference`
- `attention_backend`
- `return_logprob`

## Reward-Model Inference

The `rm_inferencer` route uses the text-regression model path and produces scoring output. It is useful for ranking tasks and reward-model pipelines.

## Benchmarking

The benchmarking example combines dataset selection, metric configuration, and evaluator routing. It is best treated as an evaluation workflow rather than a training workflow.

## Selection Guidance

- Use the base inferencer for plain text generation.
- Use the evaluator when the task names a metric or answer extraction.
- Use vLLM or SGLang only when the engine itself is part of the request.
- Use the reward-model route only when the model family is text regression / reward scoring.
