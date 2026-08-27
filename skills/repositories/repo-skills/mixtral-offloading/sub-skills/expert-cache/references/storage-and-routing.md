# Storage and sparse-routing reference

## MixtralExpertWrapper storage replacement

`MixtralExpertWrapper(expert_module, device)` wraps a quantized expert module and
replaces its parameter tensors with views into one contiguous
`torch.UntypedStorage` on the requested device.

The wrapper:

1. Builds a nested state structure for `w1`, `w2`, and `w3` containing `W_q`,
   `meta`, and `bias`.
2. Computes byte offsets for every tensor in the nested structure.
3. Allocates a single `UntypedStorage(storage_size, device=device)`.
4. Replaces tensor leaves with views into that storage.
5. Reassigns patched layers back to the expert module.
6. Registers state-dict hooks that save/load the contiguous `storage` tensor.

This design lets `ExpertCache` move an entire expert by copying one storage
object instead of many separate tensors.

## SparseMoeWrapper routing flow

`SparseMoeWrapper(config, layer_id, gate, expert_cache)` replaces Mixtral's
block-sparse MoE module after experts are registered in `ExpertCache`.

`forward(hidden_states)`:

1. Flattens `(batch, sequence, hidden)` to token rows.
2. Computes router logits with `gate(hidden_states)`.
3. Applies softmax, takes top-k experts, and renormalizes routing weights.
4. Builds a one-hot expert mask of selected experts.
5. Collects unique active expert IDs for this layer.
6. Calls `expert_cache.load_experts((layer_id, expert_idx), ..., unordered=True)`.
7. For each yielded expert, selects tokens routed to it, runs the expert, scales
   outputs by routing weights, and accumulates with `index_add_`.
8. Reshapes back to `(batch, sequence, hidden)` and returns
   `(final_hidden_states, router_logits)`.

Because active experts are requested by `(layer_id, expert_idx)`, the cache's
same-eviction-group assertion keeps swaps within the current layer.

## Extension guidance

- Keep UID shape consistent. If you change it, update all `add_expert` and
  `load_experts` call sites together.
- Do not call `load_experts` recursively or hold the iterator beyond its loop.
- Preserve same-size storage wrappers; mixed quantization layouts require a new
  cache strategy or separate cache instances.
- If adding speculative prefetching, avoid racing the `active` flag and buffer
  deques used by `_swap`.
- When changing routing, verify that `expert_mask`, `top_x`, `idx`, and
  `routing_weights` index the same flattened token order.
