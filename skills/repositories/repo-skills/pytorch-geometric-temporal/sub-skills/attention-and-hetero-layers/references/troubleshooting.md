# Attention and Heterogeneous Layer Troubleshooting

## Purpose

Use this when attention, STGCN-style, MTGNN/GMAN/AAGCN/DNNTSP, or `HeteroGCLSTM` code fails. For exact signatures and layout contracts, read [api-reference.md](api-reference.md). For minimal recipes, read [workflows.md](workflows.md).

## Fast triage checklist

1. Print the tensor shape immediately before the model call.
2. Compare it with the layout table in [api-reference.md](api-reference.md), not with a different model family.
3. Confirm `edge_index` is `torch.long` with shape `[2, E]`; confirm `edge_weight` is length `E` when supplied.
4. For Chebyshev layers, keep normalization symmetric unless the called API accepts and receives `lambda_max`.
5. For heterogeneous layers, print `x_dict.keys()`, `edge_index_dict.keys()`, and `metadata` before constructing `HeteroGCLSTM`.
6. Reproduce the issue with `python scripts/attention_hetero_smoke.py`; if the smoke passes, the failure is probably shape/data-specific.

## Common failure matrix

| Symptom or error | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: not enough values to unpack`, `permute` dimension error, or convolution expects 4D input | Feeding `[T, N, F]` or `[B, N, T, F]` directly into a 4D model | Convert explicitly: `STConv`/`TemporalConv` use `[B, T, N, F]`; `ASTGCN`/`MSTGCN` use `[B, N, F, T]`; `MTGNN` uses `[B, F, N, T]`; `AAGCN` uses `[B, F, T, N]`. |
| `STConv` output time dimension is smaller than expected | Two temporal convolutions each shrink by `kernel_size - 1` | Expected time is `T - 2*(kernel_size - 1)`. Increase input window or lower `kernel_size`. |
| `Calculated padded input size per channel... Kernel size can't be greater than actual input size` | Time window too short for `TemporalConv`, `STConv`, or MTGNN temporal kernels | Check the temporal axis for the chosen layout and start with tiny known-good settings from [workflows.md](workflows.md). |
| Chebyshev layer asks for `lambda_max` | Non-symmetric normalization (`None` or `"rw"`) without largest Laplacian eigenvalue | Prefer `normalization="sym"` for `STConv`. For `ChebConvAttention`, pass `lambda_max` or use the `ASTGCN` wrapper that computes it. |
| `STConv(normalization=None)` fails even though ChebConv supports it | `STConv.forward` does not expose `lambda_max` | Use default `"sym"` or write a custom wrapper around lower-level PyG/Chebyshev operations. |
| `edge_index` dtype/device error | `edge_index` is float/int32 or on a different device than the model/tensors | Use `edge_index = edge_index.long().to(device)`. Move `edge_weight` and input tensors to the same device. |
| PyG message passing import/runtime error mentioning scatter/sparse/cluster operations | PyG optional compiled operations are missing or mismatched with the installed PyTorch build | Verify a tiny CPU smoke first. Reinstall a PyTorch/PyG-compatible dependency set before blaming model code. Avoid GPU wheels unless the selected backend is required. |
| GMAN output horizon is wrong | `TE.shape[1]` does not equal `num_his + num_pred` | Build `TE` with exactly history plus prediction rows; GMAN infers prediction horizon from `TE.shape[1] - num_his`. |
| GMAN gives odd temporal behavior with float `TE` | `TE` values are cast to integer one-hot indices internally | Supply integer day-of-week values `0..6` and time-of-day values `0..steps_per_day-1`. |
| MTGNN assertion: `Input sequence length not equal to preset sequence length.` | `X_in.size(3)` differs from constructor `seq_length` | Ensure `X_in` is `[B, in_dim, N, seq_length]` and constructor `seq_length` matches the final axis. |
| MTGNN adjacency or feature shape mismatch | `build_adj`, `A_tilde`, `idx`, and `FE` were combined inconsistently | If `build_adj=True`, let the model build adjacency or pass valid `idx`/`FE`. If `build_adj=False` and `gcn_true=True`, pass `A_tilde: [N, N]`. |
| AAGCN complains about layout or gives transposed results | Input left as `[B, T, N, F]` | Use `x = x_btnf.permute(0, 3, 1, 2).contiguous()` for `[B, F, T, N]`. |
| DNNTSP reshape failure | First dimension of `X` is not divisible by `items_total` | Arrange rows as `batch * items_total`; assert `X.size(0) % items_total == 0` before calling. |
| DNNTSP prints shapes during forward | Helper modules contain diagnostic `print` calls | Treat prints as noisy stdout. If using in a strict test harness, capture stdout or wrap the call. |
| `KeyError` for a node type in `HeteroGCLSTM` | `HeteroConv` did not produce an output for that destination node type | Add reverse edge types or incoming relations so every node type in `in_channels_dict` appears as a destination in `edge_index_dict`. |
| `HeteroGCLSTM` device mismatch with CUDA tensors | Omitted states are initialized on CPU by the layer | On GPU, pass explicit `h_dict` and `c_dict` zero tensors on the same device as each node type's features. |
| `HeteroGCLSTM` parameter shape mismatch | `in_channels_dict` does not match `x_dict` feature dimensions | Build `in_channels_dict = {node_type: x.shape[-1] for node_type, x in x_dict.items()}` after validating the feature tensors. |
| Heterogeneous metadata mismatch | `metadata` was constructed manually and does not match `edge_index_dict` | Prefer `metadata = hetero_data.metadata()` when starting from `HeteroData`; otherwise set `metadata = (list(x_dict.keys()), list(edge_index_dict.keys()))` and verify every edge type tuple. |

## Tensor order confusion: quick conversions

Starting from `raw_tnf: [T, N, F]`:

```python
x_stconv = raw_tnf.unsqueeze(0)                              # [1, T, N, F]
x_astgcn = raw_tnf.permute(1, 2, 0).unsqueeze(0).contiguous() # [1, N, F, T]
x_mtgnn = raw_tnf.permute(2, 1, 0).unsqueeze(0).contiguous()  # [1, F, N, T]
x_aagcn = raw_tnf.permute(2, 0, 1).unsqueeze(0).contiguous()  # [1, F, T, N]
x_gman = raw_tnf[:, :, 0].unsqueeze(0).contiguous()           # [1, T, N]
```

Before training, assert the expected output shape from [api-reference.md](api-reference.md). Do this even when the forward pass does not crash; many wrong layouts remain numerically valid but learn the wrong axis relationships.

## Normalization and `lambda_max`

- `STConv` wraps PyG `ChebConv` but its `forward` only accepts `X`, `edge_index`, and `edge_weight`. It cannot pass `lambda_max`; therefore `normalization="sym"` is the safe default.
- `ChebConvAttention` directly accepts `lambda_max`. If you choose `normalization=None` or `normalization="rw"`, compute and pass the largest Laplacian eigenvalue.
- `ASTGCN` and `MSTGCN` wrappers compute `lambda_max` internally in their blocks when they need it, but this adds overhead.
- For batched graphs and non-symmetric normalization, `lambda_max` shape should match PyG's Chebyshev expectations for the graph/batch scenario.

## Heterogeneous metadata and state recovery

Use this pattern when `HeteroGCLSTM` fails on custom data:

```python
print(x_dict.keys())
print(edge_index_dict.keys())
metadata = (list(x_dict.keys()), list(edge_index_dict.keys()))
print(metadata)

in_channels_dict = {node_type: x.shape[-1] for node_type, x in x_dict.items()}
h_dict = {
    node_type: x.new_zeros((x.shape[0], out_channels))
    for node_type, x in x_dict.items()
}
c_dict = {
    node_type: x.new_zeros((x.shape[0], out_channels))
    for node_type, x in x_dict.items()
}
```

Then verify that every node type has at least one incoming relation in `edge_index_dict`. If only one direction exists, add the reverse relation before calling the layer.

## Expensive or optional model cases

The following classes are public and legitimate, but full benchmark-size tests are not good default smoke checks:

- `ASTGCN` and `MSTGCN`: attention/Chebyshev blocks over traffic-scale node counts can be memory-heavy.
- `GMAN`: multi-head spatio-temporal attention scales with history/prediction length and node count.
- `MTGNN`: receptive field, layer count, and adaptive graph construction can be expensive.
- `DNNTSP`: GCN plus self-attention over temporal sets may print diagnostics and should be wrapped if stdout matters.

Use tiny synthetic dimensions first. Treat dataset downloads, long training, and full traffic notebook replication as optional workflows owned by the appropriate data/model integration plan, not as required checks for this sub-skill.

## When to stop and reroute

- If the failure is a dataset download/cache/raw-file issue, stop here and route to `dataset-loaders`.
- If the failure is temporal iterator construction, splitting, or snapshot slicing, route to `temporal-signals`.
- If the failure is an index-batching tuple, `allGPU`, Dask-DDP, or distributed loader issue, route to `index-batching`.
- If the user actually selected recurrent-only layers such as `DCRNN`, `TGCN`, or `AGCRN`, route to `recurrent-layers`.
