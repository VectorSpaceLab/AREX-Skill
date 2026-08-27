# Inference Troubleshooting

## `Conflicting argument ... in config and kwargs`

`init_inference` merges `config` and `kwargs`, but duplicate keys must have identical values. Fix by choosing one source of truth:

```python
config = {"replace_with_kernel_inject": True, "dtype": "fp16"}
engine = deepspeed.init_inference(model, config=config)
```

or move overrides entirely into kwargs:

```python
engine = deepspeed.init_inference(model, config={"dtype": "fp16"}, replace_with_kernel_inject=True)
```

Do not pass conflicting values such as `config={"replace_with_kernel_inject": True}` with `replace_with_kernel_inject=False`.

## Unsupported Kernel Injection

Symptoms include no default policy found, unsupported model, import errors for a policy class, or a model that still uses original modules. Check whether the block class is covered by `replace_policies`. If not:

- Use manual `injection_policy` with the repeated block class and projection suffixes.
- Use AutoTP by setting `tensor_parallel.tp_size > 1` and leaving both kernel injection and manual policy off.
- Add or modify DeepSpeed policy code only if the task is to develop DeepSpeed itself.

Kernel injection and manual injection are mutually exclusive. `InferenceEngine` asserts when `injection_policy` is provided together with `replace_with_kernel_inject=True`.

## Manual Policy Layer Name Errors

`InferenceEngine` validates each policy suffix against `model.named_modules()` and raises `ValueError("Injection policy layer ... not valid")` when no module name ends with the suffix. Print layer names around the target block and choose suffixes that match the installed model version.

A common hard case is a Hugging Face architecture whose module names changed between releases. Avoid copying old suffixes blindly; inspect `named_modules()` from the actual model object.

## AutoTP Fallbacks and TP Plan Drift

AutoTP can fail when it cannot infer a policy or when the model is better served by an existing kernel policy. If a Hugging Face `tp_plan` is involved, DeepSpeed conversion supports only `colwise` and `rowwise`; unsupported partition styles return `None` so callers can fall back to preset-based AutoTP.

For model families with grouped-query attention, fused QKV, or nonstandard MLP projections, confirm that the AutoTP preset or `tp_plan` covers the exact parameter names before assuming tensor slicing is correct.

## CUDA Graph with Tensor Parallelism

`InferenceEngine` asserts `Cuda graph is not supported for model parallelism` when `tensor_parallel.tp_size > 1` and `enable_cuda_graph=True`. Disable CUDA graph for TP inference, or reduce TP to one rank if CUDA graph capture is the priority.

Also confirm PyTorch version and CUDA availability; CUDA graph support requires accelerator support and PyTorch meeting DeepSpeed's runtime checks.

## Missing `transformers`, Triton, or Checkpoints

- Built-in Hugging Face policies import `transformers` model classes lazily. If `transformers` is absent or the model class moved, policy detection can fail.
- `use_triton=True` requires Triton import support as detected by DeepSpeed; otherwise config validation raises an error.
- Checkpoint JSON files must reference reachable checkpoint files at runtime. Do not encode local development paths in reusable skill content.

## Quantization Name Drift

Older tutorials may pass `quantization_setting`, but current installed `DeepSpeedInferenceConfig` fields include `quant`, not `quantization_setting`. Treat `quantization_setting` examples as historical intent and translate carefully:

- Use `dtype=torch.int8` for int8 inference.
- Configure `quant.weight`, `quant.activation`, or `quant.qkv` as needed.
- Inspect installed fields with the bundled script before giving exact nested config advice.

## v1 vs v2/FastGen Routing

If the user asks for `init_inference`, `InferenceEngine`, `DeepSpeedInferenceConfig`, or module injection, stay in v1 inference guidance. If they ask for current high-throughput text generation serving or FastGen, explain that docs route that path through DeepSpeed-FastGen/MII and that `deepspeed.inference.v2` internals are not a direct drop-in replacement for `init_inference`.

## Hybrid Engine Confusion

`DeepSpeedHybridEngine` is a training runtime engine created through `deepspeed.initialize` with hybrid engine config. It uses inference containers for generation during training, but it is not returned by `deepspeed.init_inference`. Do not advise enabling `hybrid_engine` to solve standalone inference initialization issues.
