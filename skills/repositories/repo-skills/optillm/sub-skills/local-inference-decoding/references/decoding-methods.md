# Decoding Methods

Read this when a local inference task requests advanced decoding or reasoning-token behavior.

## Local-only rule

The methods below require access to local model/tokenizer internals, logits, hidden states, or generation loops. They are not ordinary external-provider proxy features unless the provider itself exposes equivalent internals.

## `cot_decoding`

Chain-of-thought decoding attempts to elicit reasoning without explicit prompting. Request config can include:

```python
extra_body={
    "decoding": "cot_decoding",
    "k": 10,
    "aggregate_paths": True
}
```

Use when a local model can produce useful alternate reasoning paths. Bound `k` and token limits to control cost.

## `entropy_decoding`

Entropy decoding adapts sampling based on token uncertainty metrics. Request config can include:

```python
extra_body={
    "decoding": "entropy_decoding",
    "top_k": 27,
    "min_p": 0.03
}
```

Use when token uncertainty should influence exploration. Validate on a small prompt because sampling behavior is model-sensitive.

## `thinkdeeper`

ThinkDeeper scales reasoning effort for reasoning models and explicit thought-switch behavior. It uses local generation loops and can report reasoning tokens. Use bounded `max_tokens` for smoke tests.

## `thinkdeeper_mlx`

The MLX variant is for Apple Silicon/macOS with `mlx-lm`. Do not claim it is verified on Linux/CUDA hosts. Route to this only when the machine is `arm64` macOS and MLX dependencies import.

## `deepconf`

DeepConf is confidence-aware reasoning with warmup traces, threshold calibration, early termination, consensus checking, and weighted majority voting.

Example request config:

```python
extra_body={
    "decoding": "deepconf",
    "variant": "low",
    "warmup_samples": 16,
    "max_traces": 64,
    "consensus_threshold": 0.95,
    "include_stats": False
}
```

Variants:

- `low`: aggressive filtering, keeps top-confidence traces.
- `high`: conservative filtering, keeps more traces.

DeepConf can reduce token usage but still generates multiple traces; keep trace counts bounded.

## `autothink`

AutoThink combines query complexity classification, token budget allocation, steering vectors, and controlled `<think>` phases. Config can include classifier model, steering dataset, target layer, token budgets, and pattern strengths.

Use only when:

- The local model architecture supports the steering hooks.
- Classifier and steering vector datasets are available or cached.
- The user accepts model/cache downloads if needed.

## Choosing a method

| Need | Consider |
| --- | --- |
| Prompt-free reasoning paths | `cot_decoding` |
| Adaptive uncertainty-aware sampling | `entropy_decoding` |
| More/less explicit reasoning effort | `thinkdeeper` |
| Confidence filtering and early termination | `deepconf` |
| Complexity routing plus activation steering | `autothink` |
| Apple Silicon local generation | `thinkdeeper_mlx` / MLX local path |

## Validation pattern

1. Run `scripts/check_local_backend.py`.
2. Use a tiny prompt and small `max_tokens`.
3. Confirm model/tokenizer load from cache or approved network.
4. Inspect `usage.completion_tokens_details.reasoning_tokens` if reasoning tags are expected.
5. Increase trace/path counts only after the small run succeeds.
