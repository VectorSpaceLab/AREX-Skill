# Losses, miners, distances, reducers, regularizers, and customization

This reference is the compact map for the component stack used throughout PyTorch Metric Learning.

## Mental model

```
inputs -> miner -> loss -> reducer -> scalar loss
```

Distances and regularizers plug into both losses and miners. Wrappers such as `CrossBatchMemory` and `SelfSupervisedLoss` adapt the same underlying component math to different workflows.

## Component families

| Family | Representative classes | When to use |
| --- | --- | --- |
| Distances | `LpDistance`, `CosineSimilarity`, `DotProductSimilarity`, `SNRDistance`, `BatchedDistance` | Choose the similarity or distance geometry used by a loss, miner, or regularizer. |
| Reducers | `MeanReducer`, `AvgNonZeroReducer`, `ThresholdReducer`, `DivisorReducer`, `PerAnchorReducer`, `MultipleReducers` | Convert many per-pair / per-triplet / per-element losses into one scalar. |
| Regularizers | `LpRegularizer`, `CenterInvariantRegularizer`, `RegularFaceRegularizer`, `SparseCentersRegularizer`, `ZeroMeanRegularizer` | Penalize embeddings or weights directly, usually as part of a loss. |
| Miners | `TripletMarginMiner`, `MultiSimilarityMiner`, `BatchHardMiner`, `BatchEasyHardMiner`, `DistanceWeightedMiner`, `PairMarginMiner`, `AngularMiner`, `HDCMiner`, `UniformHistogramMiner` | Select hard or structured tuples before loss computation. |
| Losses | `TripletMarginLoss`, `ContrastiveLoss`, `MultiSimilarityLoss`, `NTXentLoss`, `ArcFaceLoss`, `CosFaceLoss`, `NormalizedSoftmaxLoss`, `ProxyAnchorLoss`, `ProxyNCALoss`, `CrossBatchMemory`, `SelfSupervisedLoss`, `MultipleLosses`, `SmoothAPLoss`, `VICRegLoss` | Optimize embeddings directly or via classification-style margins/proxies. |

## Choosing a loss family

- **Pair / triplet metric losses**: `TripletMarginLoss`, `ContrastiveLoss`, `MultiSimilarityLoss`, `NTXentLoss`, `MarginLoss`, `TupletMarginLoss`, `CircleLoss`, `SignalToNoiseRatioContrastiveLoss`.
- **Classification-style margin losses**: `ArcFaceLoss`, `CosFaceLoss`, `NormalizedSoftmaxLoss`, `SphereFaceLoss`, `SubCenterArcFaceLoss`, `LargeMarginSoftmaxLoss`, `P2SGradLoss`, `InstanceLoss`, `SoftTripleLoss`, `ProxyAnchorLoss`, `ProxyNCALoss`.
- **Self-supervised wrappers and memory**: `SelfSupervisedLoss`, `CrossBatchMemory`, `VICRegLoss`.
- **Composite and wrapper utilities**: `MultipleLosses`, `MultipleReducers`, `BaseLossWrapper`.

## Compatibility notes

### Distances

- Many losses and miners accept a custom `distance` object.
- `CosineSimilarity` and `DotProductSimilarity` are inverted similarities, not ordinary distances.
- Some classes are stricter:
  - `AngularLoss` expects `LpDistance` with normalized embeddings.
  - `ArcFaceLoss`, `CosFaceLoss`, `NormalizedSoftmaxLoss`, and several proxy/classification losses are designed around cosine or dot-product style weights.
  - `DistanceWeightedMiner` is designed for L2-normalized, low-dimensional embeddings.

### Reducers

- The reducer decides how each sub-loss is collapsed.
- `ThresholdReducer` filters losses by range before averaging.
- `DivisorReducer` expects the loss dictionary to supply a `divisor` field.
- `MultipleReducers` maps each named sub-loss to its own reducer.
- `PerAnchorReducer` converts pairwise losses into per-anchor losses before the inner reducer runs.

### Tuple inputs

`indices_tuple` can be:

- `None`
- a pair tuple: `(anchors, positives, anchors, negatives)`
- a triplet tuple: `(anchors, positives, negatives)`

Use the helper functions in `pytorch_metric_learning.utils.loss_and_miner_utils`:

- `convert_to_pairs(...)`
- `convert_to_triplets(...)`
- `convert_to_weights(...)`
- `remove_self_comparisons(...)`
- `get_all_pairs_indices(...)`
- `get_all_triplets_indices(...)`

### Losses that can consume mined tuples without labels

The docs and tests confirm that these losses can be called with `indices_tuple` instead of labels when the tuple already exists:

- `CircleLoss`
- `ContrastiveLoss`
- `IntraPairVarianceLoss`
- `GeneralizedLiftedStructureLoss`
- `LiftedStructureLoss`
- `MarginLoss`
- `MultiSimilarityLoss`
- `NTXentLoss`
- `SignalToNoiseRatioContrastiveLoss`
- `SupConLoss`
- `TripletMarginLoss`
- `TupletMarginLoss`

## Custom loss pattern

1. Subclass `BaseMetricLossFunction`.
2. Implement `compute_loss(self, embeddings, labels, indices_tuple, ref_emb, ref_labels)`.
3. Return a dictionary whose keys name the sub-losses and whose values include:
   - `losses`
   - `indices`
   - `reduction_type`
4. Override `get_default_reducer()` or `get_default_distance()` when the default behavior is not appropriate.
5. Use `_sub_loss_names()` when the loss exposes multiple named sub-losses.

Example skeleton:

```python
from pytorch_metric_learning.losses import BaseMetricLossFunction

class MyLoss(BaseMetricLossFunction):
    def compute_loss(self, embeddings, labels, indices_tuple, ref_emb, ref_labels):
        return {
            "loss": {
                "losses": ..., 
                "indices": ..., 
                "reduction_type": "already_reduced",
            }
        }
```

## Custom miner pattern

1. Subclass `BaseMiner`.
2. Implement `mine(self, embeddings, labels, ref_emb, ref_labels)`.
3. Return a valid pair or triplet tuple.
4. Let the base class validate the output shape.

For pair or triplet conversion, the custom miner usually starts by computing a distance matrix and then indexing into it with helpers from `loss_and_miner_utils`.

## Weight initialization and proxy-style losses

- `TorchInitWrapper` turns a torch init function into a callable class that can be passed as `weight_init_func`.
- Several classification-style losses expose their class weights as parameters, so the wrapped loss may need its own optimizer.

## Practical selection checklist

- Need hard mining? Choose a miner first, then a loss that accepts mined tuples.
- Need self-supervision? Prefer `SelfSupervisedLoss` or a loss with explicit view-pair support.
- Need a running memory queue? Use `CrossBatchMemory` around a compatible loss.
- Need multiple objective terms? Use `MultipleLosses` or a loss with multiple named sub-losses.
- Need a different geometry? Swap the distance before changing the loss family.

## Cross-check against the tests

Useful native references for this layer include:

- `tests/losses/test_triplet_margin_loss.py`
- `tests/losses/test_self_supervised_loss.py`
- `tests/losses/test_cross_batch_memory.py`
- `tests/losses/test_multiple_losses.py`
- `tests/losses/test_losses_without_labels.py`
- `tests/miners/test_triplet_margin_miner.py`
- `tests/reducers/test_threshold_reducer.py`
- `tests/distances/test_batched_distance.py`
