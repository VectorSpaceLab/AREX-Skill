---
name: expert-cache
description: "Debug and extend mixtral-offloading's MoE expert cache, storage
  wrapper, and sparse routing internals."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Expert Cache

Use this sub-skill when the task is about expert offloading internals rather
than simply running the demo: `ExpertCache`, `MixtralExpertWrapper`,
`SparseMoeWrapper`, expert UIDs, LRU eviction groups, pinned offload storage,
or cache-capacity errors.

## Read this when

- The user sees `Cache is full`, `No evictable experts`, `already loading
  experts`, duplicate expert UID assertions, or eviction-group assertions.
- The task is to change offloading policy, add prefetching, debug storage
  movement, or inspect sparse MoE routing.
- The user wants to understand how `offload_per_layer` becomes `main_size` and
  `offload_size` inside `ExpertCache`.

## Route map

1. Read [references/expert-cache-api.md](references/expert-cache-api.md) for
   `ExpertInfo`, `EvictionGroupInfo`, `ExpertCache`, and method invariants.
2. Read [references/storage-and-routing.md](references/storage-and-routing.md)
   for `MixtralExpertWrapper` storage replacement and `SparseMoeWrapper.forward`
   routing flow.
3. Use [scripts/inspect_cache_plan.py](scripts/inspect_cache_plan.py) to compute
   cache capacities and example expert UIDs without loading model weights.
4. Read [references/troubleshooting.md](references/troubleshooting.md) for
   capacity, reentrancy, storage, pinned-memory, and routing-shape failures.

## What this sub-skill owns

- Expert-cache capacity and eviction invariants.
- Expert UID layout and eviction-group behavior.
- Storage wrapping and state-dict storage hooks.
- Sparse MoE top-k routing through cached experts.

## What to route elsewhere

- Use [../inference-workflow/SKILL.md](../inference-workflow/SKILL.md) for full
  model construction, generation, and offload config selection.
- Use [../quantization-kernels/SKILL.md](../quantization-kernels/SKILL.md) for
  HQQ quantized MLP layers, packing, and Triton kernel failures.

## Safe verification

Most cache internals require real `MixtralExpertWrapper` objects backed by
CUDA `UntypedStorage`. For safe planning, use the bundled script and source/API
reasoning. Do not construct the full cache with dummy objects unless their
storage type, size, and device match the expected wrapper invariants.
