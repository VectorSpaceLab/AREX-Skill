# API Reference

This repository is organized around six top-level modules. The tables below capture the public classes and functions that the generated skill routes should know about.

## `datasets.py`

| Symbol | Purpose | Notes |
| --- | --- | --- |
| `SiameseMNIST(mnist_dataset)` | Wraps a MNIST-like dataset and returns image pairs with a same/different target. | Training mode samples random positive or negative pairs; test mode emits fixed pairs. |
| `TripletMNIST(mnist_dataset)` | Wraps a MNIST-like dataset and returns `(anchor, positive, negative)` triplets. | Training mode samples random positives and negatives; test mode emits fixed triplets. |
| `BalancedBatchSampler(labels, n_classes, n_samples)` | Batch sampler that draws `n_classes × n_samples` examples per batch. | Used by the online mining notebook sections. |

## `networks.py`

| Symbol | Purpose | Notes |
| --- | --- | --- |
| `EmbeddingNet` | Small CNN that maps a grayscale `1×28×28` image to a 2D embedding. | This is the repository's default embedding backbone. |
| `EmbeddingNetL2` | `EmbeddingNet` plus L2 normalization. | Useful when normalized embeddings are desired. |
| `ClassificationNet(embedding_net, n_classes)` | Adds a classification head over an embedding network. | Produces log-softmax scores for NLL loss. |
| `SiameseNet(embedding_net)` | Runs one embedding network on two inputs. | Returns two embeddings. |
| `TripletNet(embedding_net)` | Runs one embedding network on three inputs. | Returns anchor, positive, and negative embeddings. |

## `losses.py`

| Symbol | Purpose | Notes |
| --- | --- | --- |
| `ContrastiveLoss(margin)` | Pairwise contrastive loss for same/different pairs. | Expects two embeddings and a binary target. |
| `TripletLoss(margin)` | Standard triplet margin loss. | Expects anchor, positive, and negative embeddings. |
| `OnlineContrastiveLoss(margin, pair_selector)` | Contrastive loss that mines pairs inside a batch. | Returns a scalar loss over mined pairs. |
| `OnlineTripletLoss(margin, triplet_selector)` | Triplet loss that mines triplets inside a batch. | Returns `(loss, num_triplets)` so metrics can track mined triplets. |

## `utils.py`

| Symbol | Purpose | Notes |
| --- | --- | --- |
| `pdist(vectors)` | Pairwise distance matrix helper. | Used by the mining selectors. |
| `PairSelector` | Abstract pair selector interface. | Implement `get_pairs`. |
| `AllPositivePairSelector(balance=True)` | Generates all positive pairs and optionally balances negatives. | Good baseline selector. |
| `HardNegativePairSelector(cpu=True)` | Selects hard negatives by distance. | CPU conversion is part of the repo implementation. |
| `TripletSelector` | Abstract triplet selector interface. | Implement `get_triplets`. |
| `AllTripletSelector()` | Generates all possible triplets. | Useful for exhaustive tiny smokes only. |
| `FunctionNegativeTripletSelector(margin, negative_selection_fn, cpu=True)` | Shared selector implementation for negative-mining strategies. | Underlies the selector factories below. |
| `HardestNegativeTripletSelector(margin, cpu=False)` | Factory for hardest-negative mining. | | 
| `RandomNegativeTripletSelector(margin, cpu=False)` | Factory for random hard-negative mining. | | 
| `SemihardNegativeTripletSelector(margin, cpu=False)` | Factory for semi-hard negative mining. | | 

## `trainer.py`

| Symbol | Purpose | Notes |
| --- | --- | --- |
| `fit(train_loader, val_loader, model, loss_fn, optimizer, scheduler, n_epochs, cuda, log_interval, metrics=[], start_epoch=0)` | Shared training loop used by the notebooks. | Works with classification, siamese, triplet, and online-mining loaders. |
| `train_epoch(...)` | Single-epoch training helper. | Internal helper used by `fit`. |
| `test_epoch(...)` | Validation helper. | Internal helper used by `fit`. |

## `metrics.py`

| Symbol | Purpose | Notes |
| --- | --- | --- |
| `Metric` | Abstract metric interface. | Implement `__call__`, `reset`, `value`, and `name`. |
| `AccumulatedAccuracyMetric` | Accuracy metric for classification. | Uses `outputs[0].data.max(1)`. |
| `AverageNonzeroTripletsMetric` | Tracks the average number of mined triplets. | Expects the loss to return `(loss, count)`. |

## Shape and data expectations

- `EmbeddingNet` and the notebook helpers expect grayscale image tensors shaped like `1×28×28` before the batch dimension.
- The pair and triplet dataset wrappers convert tensors to PIL images internally and then reapply the transform if one is attached.
- The notebooks assume 2D embeddings for plotting; if you change the embedding dimension, update the plotting helpers accordingly.
- The online mining code mines on labels from the current mini-batch. The batch must contain multiple examples per class for meaningful pairs or triplets.
