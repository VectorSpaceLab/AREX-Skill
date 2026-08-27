# Expert cache troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `expert <uid> already registered` | Duplicate UID passed to `add_expert_storage`. | Ensure UIDs are unique, usually `(layer_idx, expert_idx)`. |
| `Cache is full` | No permitted main/offload slot remains for the requested `offload` setting. | Recompute `main_size` and `offload_size`; verify `offload_per_layer <= num_experts` and counts match all experts. |
| `No evictable experts` | A layer/group has no expert in `main_infos` to swap out. | Avoid `offload_per_layer == num_experts` for swap-based paths; keep at least one main expert per eviction group. |
| `already loading experts; buffers are busy` | `load_experts` was entered while a previous iterator is still active. | Do not nest `load_experts`; finish the for-loop before starting another load or design a separate prefetch path. |
| `experts must be in the same evicton group` | Requested UIDs span multiple layer eviction groups. | Call `load_experts` per layer/group. SparseMoeWrapper naturally does this with `(layer_id, expert_idx)`. |
| Storage type/size/device assertion | `make_module` or added expert storage differs from the cache's first wrapper. | Use the same quantized expert class, metadata shapes, and device for every cached expert. |
| Pinned-memory or CUDA copy failure | Host lacks pinned-memory/CUDA support or storage lives on the wrong device. | Verify CUDA first; inspect wrapper storage device and do not replace `UntypedStorage` with ordinary tensors. |
| Unexpected output order with `unordered=True` | Cache yields non-offloaded experts first to reduce wait time. | Consume returned `(uid, expert)` pairs by UID, not by assuming request order. |
| Routing shape/index error | `expert_mask`, `selected_experts`, and `routing_weights` no longer align after a routing change. | Recheck flattened token dimensions and the top-k index lists used for `current_state` and `index_add_`. |

## Debug order

1. Use `inspect_cache_plan.py` to validate capacity math.
2. Confirm every expert UID and eviction group is what the layer expects.
3. Check `main_infos` and `offloaded_infos` counts per group before swaps.
4. Verify wrapper storage type, length, and device.
5. Only then inspect Triton/HQQ expert computation.
