# Recurrent layer troubleshooting

Use this file when a recurrent temporal graph model imports correctly but fails at construction, forward pass, loss computation, or short training.

## Shape mismatch quick triage

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `mat1 and mat2 shapes cannot be multiplied` or `size mismatch` in `Linear` | The task head input dimension does not match the recurrent output dimension. | Check the layer table. For most cells the head input is `out_channels`; for `MPNNLSTM` it is `2 * hidden_size + in_channels + window - 1`; for `EvolveGCN*` it is `in_channels`. |
| Error around concatenating `X` and `H` | Hidden state shape does not match current node count, batch size, or `out_channels`. | Reset `H=None` when `N`, `B`, node order, or hidden size changes. For LSTM-style layers reset both `H=None` and `C=None`. |
| Output has `[B, N, O]` but target has `[B, T, N]` or `[B, N, T]` | Batched-period output layout does not match the target horizon layout. | Decide whether the head predicts per period (`Linear(hidden, periods)` -> `[B, N, periods]`) or per time step (`torch.cat(..., dim=1)` -> `[B, T, N, target_dim]`), then permute/squeeze only intentionally. |
| `A3TGCN` receives 4-D input or `A3TGCN2` receives 3-D input | Non-batched and batched A3 variants were mixed. | `A3TGCN`: `[N, F, periods]`; `A3TGCN2`: `[B, N, F, periods]`. |
| Loss broadcasts silently or warns about different target sizes | `y_hat` and `y` are not aligned even though broadcasting permits a result. | Assert shapes before loss: `assert y_hat.shape == y.shape` or reshape targets explicitly. |
| `MPNNLSTM` returns an unexpected number of rows | Input was not flattened according to `window` and `num_nodes`. | For `window>1`, build `[B, window, N, F]`, flatten to `[B * window * N, F]`, and expect `[B * N, 2 * hidden_size + F + window - 1]`. |

## `edge_weight` and graph-weight failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `NoneType` error or scatter/repeat failure in a diffusion/batched layer | A layer path expects explicit edge weights even if the graph is conceptually unweighted. | Pass `edge_weight = torch.ones(edge_index.size(1), dtype=torch.float32, device=X.device)`. This is especially important for `BatchedDCRNN`. |
| `edge_weight` length error | `edge_weight` is not shaped `[num_edges]` or no longer matches `edge_index`. | Recompute `edge_weight` after filtering/reordering edges. Check `edge_weight.numel() == edge_index.size(1)`. |
| `inf`, `nan`, or unstable diffusion outputs | Diffusion normalization encountered zero degree, zero weights, or disconnected directed structure. | Use a graph where every node has the required incoming/outgoing support for the diffusion direction, add self-loops if appropriate, or use positive weights. Start with the smoke script's bidirectional ring. |
| Device mismatch involving `edge_weight` | Features moved to GPU/CPU but weights stayed elsewhere. | Move `X`, `edge_index`, `edge_weight`, `H`, `C`, and embeddings to the same device before forward. |

## Chebyshev `K`, normalization, and `lambda_max`

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Error requesting `lambda_max` | `GConvGRU`, `GConvLSTM`, or `GCLSTM` was constructed with `normalization=None` or `normalization="rw"`. | Compute/pass `lambda_max` for every forward call, or use default `normalization="sym"` when appropriate. |
| Poor performance or slow/memory-heavy smoke with large `K` | Chebyshev filters expand work with `K`. | For initial smoke tests use `K=1` or `K=2`; increase only after shapes are validated. |
| Different graph each snapshot with cached assumptions | `lambda_max` or normalized support belongs to the graph topology. | Recompute `lambda_max` whenever `edge_index`/`edge_weight` changes. |

## Hidden-state management problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Validation/test result depends on the immediately previous training batch | Hidden state was preserved across independent splits. | Set `H=None` and `C=None` before validation/test, or clone/detach only the exact state you intentionally want to evaluate. |
| Memory grows over a long temporal sequence | Backpropagation graph is retained through all previous snapshots. | Use truncated BPTT: after each chunk, detach state with `H = H.detach()` and `C = C.detach()` before continuing. |
| `DyGrEncoder` raises `Invalid hidden state and cell matrices.` | Exactly one of `H` or `C` was provided. | Pass both returned states or pass neither. |
| `EvolveGCNH`/`EvolveGCNO` gives order-dependent results in a repeated smoke | Internal recurrent weight was not reset between independent runs. | Call `layer.reinitialize_weight()` before each independent sequence. |
| Hidden state shape fails on final small batch | The final `DataLoader` batch has a smaller leading dimension than the saved state. | Use `drop_last=True` for fixed-size recurrent batches or reset state when `x.size(0)` changes. |

## `batch_size`, `periods`, and batched recurrent variants

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `A3TGCN2` output is `[B, N, hidden]` but expected `[B, N, periods]` | `A3TGCN2` returns hidden features; the horizon head is missing. | Add `torch.nn.Linear(hidden, periods)` or the desired `target_dim` after `F.relu(h)`. |
| `periods` constructor value disagrees with data | The last axis of `X` is not the same as the `periods` argument. | Check `assert X.size(-1) == periods` before the forward call. |
| Confusion between `TGCN2(batch_size=...)` and current batch size | The constructor includes `batch_size` for compatibility, while hidden-state initialization infers `B` from `X`. | Still instantiate with the intended batch size for clarity, but reset/resize persistent state if the actual `B` changes. |
| `BatchedDCRNN` state cannot be preserved between calls | `BatchedDCRNN.forward` has no external `H` argument and resets hidden state internally. | Use the whole sequence in one call, or use non-batched `DCRNN` in an explicit snapshot loop if cross-call state is required. |

## Optional Lightning and long-example caveats

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: pytorch_lightning` | Lightning is optional and not part of the minimum recurrent-layer environment. | Use ordinary PyTorch loops or install Lightning deliberately for a Lightning workflow. Do not treat Lightning absence as a core recurrent-layer failure. |
| A recurrent example starts downloads, plots, or long training | Public examples may use real loaders, network-backed traffic data, plotting stacks, or many epochs. | Use the bundled synthetic smoke script first. Adapt only the model skeleton, not the network/data/download side effects. |
| Lightning validation appears to use stale recurrent state | `training_step`/`validation_step` state handling was implicit. | Reset hidden state per batch unless the sequence order is controlled and state carryover is intentional. Log metrics with names matching callbacks. |

## Synthetic smoke script failures

Run the script with `--help` first. If `--layer all` fails, isolate the layer:

```bash
python scripts/recurrent_forecasting_smoke.py --help
python scripts/recurrent_forecasting_smoke.py --layer dcrnn --train-steps 1
python scripts/recurrent_forecasting_smoke.py --layer a3tgcn2 --train-steps 1 --batch-size 2 --periods 3
```

Troubleshooting signals from the script:

- Shape assertion failure: compare the reported expected and actual shapes against [API reference](api-reference.md).
- Import failure: verify the package and PyTorch/PyG installation before debugging model code.
- `nan` loss: reduce learning rate, keep edge weights positive, or isolate with `--train-steps 1`.
- Batch/period assertion failure: check `--batch-size`, `--periods`, and `--num-nodes` arguments.

The smoke script validates importability, forward shapes, explicit heads, loss computation, and optimizer steps. It is not a benchmark and does not validate dataset-loader behavior.
