# Inference and Evaluation Troubleshooting

## Missing Deepspeed Config

**Symptom**: the evaluation or chatbot example fails when a `deepspeed` config path is missing.

**Likely cause**: the evaluator route expects a valid config or an environment that supplies it.

**Recovery**: pass the config path explicitly or choose a base-generation path that does not need DeepSpeed.

## Optional Engine Missing

**Symptom**: `No module named vllm` or `No module named sglang`.

**Likely cause**: the selected engine extra is not installed.

**Recovery**: install exactly one engine extra in its own environment.

## Engine Conflicts

**Symptom**: vLLM and SGLang both appear in the same environment.

**Likely cause**: incompatible CUDA/PyTorch stacks were mixed.

**Recovery**: split them into separate prefixes and keep the routes separate.

## `return_logprob` Not Working

**Symptom**: the flag is ignored or warns on a non-SGLang path.

**Likely cause**: `return_logprob` is only supported for SGLang in the inspected install.

**Recovery**: switch to SGLang or drop the flag.

## Result File Issues

**Symptom**: no `inference_results.pkl` appears.

**Likely cause**: `save_inference_results` was not enabled or the output path points to a file rather than a directory.

**Recovery**: set the directory path explicitly and enable saving.

## Reward-Model Path Confusion

**Symptom**: text-regression / reward-model inference does not match the intended model family.

**Likely cause**: the model `arch_type` does not match the reward-model path.

**Recovery**: use `arch_type=text_regression` and confirm the route is `rm_inferencer`.
