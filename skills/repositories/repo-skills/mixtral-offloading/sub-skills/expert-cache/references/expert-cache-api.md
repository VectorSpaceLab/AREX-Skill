# Expert cache API reference

## Data records

`ExpertInfo(uid, eviction_group, offloaded, index)` records where an expert is
stored and which eviction group it belongs to. In the built Mixtral model, the
UID shape is `(layer_idx, expert_idx)`.

`EvictionGroupInfo` keeps two ordered dictionaries:

- `main_infos`: experts currently in CUDA/main slots, least-recently-used first.
- `offloaded_infos`: experts currently in pinned/offload storage, also ordered.

It also records `hits` and `misses`. `mark_used(info)` increments hits when the
expert is in `main_infos` and misses when it is in `offloaded_infos`.

## ExpertCache constructor

`ExpertCache(make_module, main_size, offload_size, buffer_size)` creates:

- `main_size` main modules by calling `make_module()`.
- `offload_size` pinned `torch.UntypedStorage` objects sized to match the first
  module's storage.
- `buffer_size` device expert buffers and offload storage buffers for swaps.

Every object returned by `make_module()` must be a `MixtralExpertWrapper` with a
`torch.UntypedStorage` at `module.storage`. The cache checks that wrapper type,
storage length, and storage device remain identical for all modules.

## Adding experts

`add_expert(uid, module, eviction_group=0, offload=None)` delegates to
`add_expert_storage(uid, module.storage, ...)`.

`add_expert_storage` rules:

- `uid` must not already be registered.
- `storage` must be an `UntypedStorage` with the same byte length as cache
  modules.
- If `offload is False` or `None`, it first tries to fill a free main slot.
- If `offload is True` or `None`, it tries to fill a free offload slot.
- If no allowed slot is free, it raises `ValueError('Cache is full')`.

During model build, each layer's first `offload_per_layer` experts are added
with `offload=True`; the others are kept in main slots.

## Loading experts

`load_experts(*uids, unordered=False)` is an iterator that yields
`(uid, MixtralExpertWrapper)` pairs for a set of requested experts.

Important invariants:

- Requested UIDs must be unique.
- Cache loading is non-reentrant; `self.active` must be false when entering.
- All requested experts must belong to the same eviction group.
- If `unordered=True`, non-offloaded experts are yielded first to reduce wait
  time.
- The iterator is only safe inside the `for` loop; the cache clears `active` in
  `finally`.

When an offloaded expert is needed, `_swap(info_to_load, info_to_evict)` moves
one offloaded storage into a device expert buffer while preserving the evicted
main expert into offload storage. The eviction candidate is the least recently
used main expert in the same eviction group.

## Capacity planning

For a model with `L` layers, `E` experts per layer, and `P=offload_per_layer`:

- `main_size = L * (E - P)`
- `offload_size = L * P`
- `buffer_size = 4` in the demo

A plan with `E - P <= 0` leaves no main expert to evict in a layer and is risky
for swap-based loading.
