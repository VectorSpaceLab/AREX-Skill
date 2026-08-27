# Inference API reference

## High-level synchronous API

Installed signature shape:

```python
MegatronLLM(
    *,
    model,
    tokenizer,
    inference_config=None,
    use_coordinator=True,
    coordinator_host=None,
    coordinator_port=None,
)
```

Use this for direct synchronous generation in scripts where the caller controls model/tokenizer construction and wants a context manager around the engine lifecycle.

Conceptual pattern:

```python
with MegatronLLM(model=model, tokenizer=tokenizer, inference_config=cfg, use_coordinator=False) as llm:
    results = llm.generate(prompts, sampling_params=sampling)
```

## High-level asynchronous API

Installed signature shape:

```python
MegatronAsyncLLM(
    *,
    model,
    tokenizer,
    inference_config=None,
    use_coordinator=True,
    coordinator_host=None,
    coordinator_port=None,
)
```

Use this when the caller needs async generation, coordinator mode, or serving lifecycle integration.

## `ServeConfig`

Installed signature shape:

```python
ServeConfig(
    host='0.0.0.0',
    port=5000,
    parsers=list_factory,
    verbose=False,
    frontend_replicas=4,
)
```

Use `host='127.0.0.1'` for local-only development and `0.0.0.0` only when external access is intended and network/security policy allows it.

## Sampling parameters

Use `SamplingParams` to capture generation controls such as maximum generated tokens, temperature, top-k/top-p, and stop words. Keep one sampling-parameter object per homogeneous generate call. If each prompt needs a different generation length from a file, the high-level API path may not be the right wrapper.

## Lifecycle rules

- Construct tokenizer and model before entering the LLM context.
- Use coordinator mode when worker ranks should receive requests through the coordinator pipeline; HTTP serving requires the coordinator path.
- Primary rank submits user prompts in coordinator mode; worker ranks participate in engine execution and shutdown.
- Destroy Torch distributed only after the LLM/server context exits.
