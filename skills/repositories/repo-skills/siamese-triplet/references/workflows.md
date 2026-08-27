# Workflows

This repository supports four related workflows. The notebooks show the long-form version; the bundled scripts in this generated skill provide short smoke checks.

## 1. Baseline classification

Use this when you want a plain embedding backbone plus a classification head.

Typical notebook shape:

1. Load `torchvision.datasets.MNIST` or `FashionMNIST` with grayscale transforms.
2. Wrap the data in standard `DataLoader` instances with batch size 256.
3. Build `EmbeddingNet` and wrap it with `ClassificationNet(embedding_net, n_classes)`.
4. Train with `torch.nn.NLLLoss`, `Adam(lr=1e-2)`, and `StepLR(step_size=8, gamma=0.1)` for 20 epochs.
5. Extract embeddings from the penultimate layer and plot them in 2D.

## 2. Siamese training

Use this when you want pairwise metric learning with contrastive loss.

Typical notebook shape:

1. Wrap the dataset with `SiameseMNIST`.
2. Create pair loaders with batch size 128.
3. Build `SiameseNet(EmbeddingNet())`.
4. Train with `ContrastiveLoss(margin=1.0)` and `Adam(lr=1e-3)` for 20 epochs.
5. Evaluate the learned embeddings by extracting the embeddings from the backbone and plotting them.

## 3. Triplet training

Use this when you want anchor/positive/negative learning with triplet loss.

Typical notebook shape:

1. Wrap the dataset with `TripletMNIST`.
2. Create triplet loaders with batch size 128.
3. Build `TripletNet(EmbeddingNet())`.
4. Train with `TripletLoss(margin=1.0)` and `Adam(lr=1e-3)` for 20 epochs.
5. Plot the resulting 2D embeddings for train and test sets.

## 4. Online mining

Use this when you want mini-batch mining instead of random pair or triplet sampling.

Typical notebook shape:

1. Build `BalancedBatchSampler(train_labels, n_classes=10, n_samples=25)` and the matching test sampler.
2. Feed the raw dataset into the sampler-backed loaders.
3. For online contrastive training, use `EmbeddingNet` directly with `OnlineContrastiveLoss(margin=1.0, pair_selector=HardNegativePairSelector())`.
4. For online triplet training, use `EmbeddingNet` directly with `OnlineTripletLoss(margin=1.0, triplet_selector=RandomNegativeTripletSelector(1.0))` or another selector.
5. Add `AverageNonzeroTripletsMetric()` for the online triplet case.

## Notebook defaults worth preserving

- `EmbeddingNet` outputs 2D embeddings.
- `margin = 1.0` is the notebook default for both contrastive and triplet losses.
- `n_epochs = 20` in the long-form notebooks.
- `StepLR(optimizer, 8, gamma=0.1, last_epoch=-1)` is used in the notebook recipes.
- `torch.cuda.is_available()` only changes the device placement and loader kwargs; the workflows still run on CPU.

## Bundled smoke strategy

The generated skill does not download MNIST or FashionMNIST during verification. Instead, the smoke scripts use tiny synthetic fixtures that mimic the notebook shapes and loader contracts:

- dataset wrappers and sampler smoke
- network and loss smoke
- one-epoch `fit` smoke on a synthetic classification batch
- optional CUDA tensor allocation when the host and installed wheels support it
