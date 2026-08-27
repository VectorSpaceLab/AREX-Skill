# Components troubleshooting

## Common symptoms and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `labels must be a 1D tensor of shape (batch_size,)` | The batch labels are 2D or the wrong length | Flatten or repackage the labels so they match the batch size. |
| `Number of embeddings must equal number of labels` | The model output and label batch lengths differ | Make the loader, collate function, and model output agree on batch size. |
| `labels are ref_labels are not supported for this loss function` | A loss that expects mined tuples only was given labels | Call the compatible loss with `indices_tuple` or choose a label-aware loss. |
| `ref_emb is not supported for this loss function` | A classification-style loss or other non-reference-aware loss received reference embeddings | Use the loss in its supported form, or switch to a tuple loss that supports references. |
| `indices_tuple is not supported for this loss function` | A loss that only uses labels was given mined tuples | Remove `indices_tuple` or pick a tuple-compatible loss. |
| `no valid triplets` / `no valid pairs` / zero loss | Batch composition or labels do not produce positive/negative structure | Increase batch diversity, use a sampler, or lower the miner margin. |
| Distance-compatibility assertion | The chosen distance does not match the loss/miner requirements | Read the component reference; some losses require `CosineSimilarity` or normalized `LpDistance`. |
| `CrossBatchMemory` complains about `efficient=True` | Efficient mode is not supported for that wrapper combination | Use `efficient=False` or a compatible loss/memory setup. |
| A classification-style loss never learns | The loss has trainable class weights but no optimizer steps them | Add the loss parameters to an optimizer. |

## Compatibility mistakes that are easy to make

- Using a similarity where a non-inverted distance is expected, or vice versa.
- Forgetting to normalize embeddings when the selected loss or miner assumes it.
- Passing a miner output built for one batch into a different batch.
- Mixing `MultipleLosses` / `MultipleReducers` keys that do not match the underlying objects.
- Using `TripletMarginMiner` or `MultiSimilarityMiner` on a batch that does not contain at least one positive and one negative per anchor.
- Choosing a margin that is too strict for the current batch geometry, which often produces empty tuples.

## Recovery steps

1. Reproduce the failure on a tiny toy batch so you can see whether the issue is labels, geometry, or tuple shape.
2. Print the sampled labels and the mined tuple lengths before the loss call.
3. Temporarily switch to a basic `TripletMarginLoss` or `ContrastiveLoss` with the default distance to isolate the component that is too strict.
4. Reduce the batch size if the batch produces too many tuples and the library hits large-tensor limits.
5. Use `loss_and_miner_utils.convert_to_pairs` or `convert_to_triplets` instead of hand-rolling tuple conversion.

## When to read the script

Run `scripts/smoke_components.py` when you want a short confirmation that the chosen component stack is still valid after a config change.
