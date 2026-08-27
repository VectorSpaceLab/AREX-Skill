# Embedding and Mining API Reference

## Network wrappers

| Symbol | Contract |
| --- | --- |
| `EmbeddingNet()` | Grayscale `1×28×28` input -> 2D embedding |
| `EmbeddingNetL2()` | Same as `EmbeddingNet`, then L2-normalize |
| `ClassificationNet(embedding_net, n_classes)` | Backbone -> `PReLU` -> linear head -> log-softmax |
| `SiameseNet(embedding_net)` | Runs the same backbone on two inputs and returns two embeddings |
| `TripletNet(embedding_net)` | Runs the same backbone on three inputs and returns three embeddings |

## Losses

| Symbol | Inputs | Return |
| --- | --- | --- |
| `ContrastiveLoss(margin)` | `output1, output2, target` | scalar tensor |
| `TripletLoss(margin)` | `anchor, positive, negative` | scalar tensor |
| `OnlineContrastiveLoss(margin, pair_selector)` | `embeddings, labels` | scalar tensor |
| `OnlineTripletLoss(margin, triplet_selector)` | `embeddings, labels` | `(scalar tensor, mined_triplet_count)` |

## Selectors

| Symbol | Purpose |
| --- | --- |
| `AllPositivePairSelector(balance=True)` | All positive pairs plus balanced negatives |
| `HardNegativePairSelector(cpu=True)` | Hardest negative pairs by distance |
| `AllTripletSelector()` | Exhaustive triplet enumeration |
| `HardestNegativeTripletSelector(margin, cpu=False)` | Hardest negative triplets |
| `RandomNegativeTripletSelector(margin, cpu=False)` | Random hard negatives |
| `SemihardNegativeTripletSelector(margin, cpu=False)` | Semi-hard negatives |

## Selector notes

- The selector helpers rely on the labels being compatible with `.cpu().data.numpy()`.
- The mining code is small-batch friendly and intended for notebook-scale experiments.
- `AverageNonzeroTripletsMetric` depends on the online triplet loss returning the triplet count.
