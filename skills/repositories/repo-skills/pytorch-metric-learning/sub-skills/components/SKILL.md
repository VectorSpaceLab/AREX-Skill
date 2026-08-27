---
name: components
description: "Routes PyTorch Metric Learning questions about losses, miners,
  distances, reducers, regularizers, self-supervised wrappers, and custom
  component implementations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Components

Use this sub-skill when the user needs to choose, combine, or customize the metric-learning primitives that sit below training and evaluation.

## Typical triggers

- "Which loss should I use for triplets, pairs, proxies, or self-supervision?"
- "How do I pick a miner for this batch?"
- "How do I swap the distance, reducer, or regularizer?"
- "Why does this loss need labels, a miner output, or `indices_tuple`?"
- "How do I write a custom loss or miner?"
- "Why am I getting no valid triplets, a distance-compatibility error, or a shape error?"

## In scope

- Distances: `LpDistance`, `CosineSimilarity`, `DotProductSimilarity`, `SNRDistance`, and `BatchedDistance`.
- Reducers: `MeanReducer`, `AvgNonZeroReducer`, `ThresholdReducer`, `DivisorReducer`, `PerAnchorReducer`, `MultipleReducers`, `DoNothingReducer`, `SumReducer`, `ClassWeightedReducer`.
- Regularizers: `LpRegularizer`, `CenterInvariantRegularizer`, `RegularFaceRegularizer`, `SparseCentersRegularizer`, `ZeroMeanRegularizer`.
- Miners: `TripletMarginMiner`, `MultiSimilarityMiner`, `BatchHardMiner`, `BatchEasyHardMiner`, `DistanceWeightedMiner`, `PairMarginMiner`, `AngularMiner`, `HDCMiner`, `UniformHistogramMiner`, `EmbeddingsAlreadyPackagedAsTriplets`.
- Loss families and wrappers: `TripletMarginLoss`, `ContrastiveLoss`, `MultiSimilarityLoss`, `NTXentLoss`, `AngularLoss`, `ArcFaceLoss`, `CosFaceLoss`, `NormalizedSoftmaxLoss`, `ProxyAnchorLoss`, `ProxyNCALoss`, `SelfSupervisedLoss`, `CrossBatchMemory`, `MultipleLosses`, `SmoothAPLoss`, `VICRegLoss`, and related metric/classification losses.
- Custom component authoring with `BaseMetricLossFunction`, `BaseMiner`, `loss_and_miner_utils`, and `TorchInitWrapper`.

## Out of scope

- Trainer setup, hooks, logging, and checkpointing belong in `training`.
- Accuracy calculators, testers, and nearest-neighbor inference belong in `evaluation`.
- Dataset download and sampler configuration belong in `data`.

## How to use this sub-skill

1. Start with `references/losses-miners-and-customization.md` for the compact component catalog and compatibility rules.
2. Run `scripts/smoke_components.py` on toy tensors when you need a quick sanity check for a component stack or a custom extension.
3. Read `references/troubleshooting.md` when the failure mentions labels, `indices_tuple`, no valid tuples, or an incompatible distance/reducer/regularizer.
4. For custom loss/miner implementations, follow the distilled extension patterns and use the bundled `loss_and_miner_utils` helpers instead of re-deriving tuple conversion logic.

## Common routing decisions

- If the user asks which loss or miner to use, stay here.
- If the user asks why a component rejects labels, margins, or tuple shapes, stay here.
- If the user asks how to wire the chosen component into a trainer or tester, route to `training` or `evaluation` after the component choice is settled.

## Useful public facts

- Most metric losses and miners accept a `distance` object.
- Some losses can be called with `indices_tuple` instead of labels when the tuple has already been mined.
- Classification-style losses typically need `num_classes` and `embedding_size`, and some require an optimizer for their class weights.
- `CrossBatchMemory` wraps another loss and adds queue behavior; `SelfSupervisedLoss` adapts a pair or tuple loss to two views.
- `MultipleLosses` and `MultipleReducers` require matching keys or parallel lists.

## Read next

- `references/losses-miners-and-customization.md` for the component catalog and extension notes.
- `references/troubleshooting.md` for predictable component-level failures.
- `scripts/smoke_components.py` for a tiny direct smoke check.
