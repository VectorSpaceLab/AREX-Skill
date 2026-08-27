# Speedster Workflows

## Purpose

Read this for common end-to-end recipes.

## Typical path

1. Build or load the original model.
2. Prepare `input_data` in the framework format the docs describe.
3. Choose `optimization_time`, `metric_drop_ths`, and any compiler exclusions.
4. Run `optimize_model(...)`.
5. Persist the optimized learner with `save_model(...)` if you want to reuse it.
6. Load it later with `load_model(...)`.

## Framework notes

- PyTorch and TensorFlow use batched tensor tuples or dataloaders.
- ONNX expects NumPy inputs.
- Hugging Face flows can use dictionaries or strings, but string input usually needs a tokenizer passed in extra keyword arguments.
- Diffusers workflows are stricter about backend versions and tend to require CUDA-oriented environments.

## Common choices

- Use `optimization_time="constrained"` when you want a short, compiler-focused pass.
- Use `optimization_time="unconstrained"` when you can provide more data and want pruning or distillation to remain eligible.
- Use `ignore_compilers` to avoid hardware-specific backends you cannot satisfy.
- Use `device="cpu"` when you need a CPU-only fallback path.
- Use `store_latencies=True` when you want a per-compiler latency file for comparison.
- Use `dynamic_info` when the model accepts variable input or output shapes.

## When not to use this path

If the user is asking which optional backend package to install, or why a backend is missing, open the NebullVM backend sub-skill instead.
