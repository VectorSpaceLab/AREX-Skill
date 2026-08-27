# Training Workflows

## Shared fit-loop contract

`fit` expects the model, loss, loader, and metric objects to agree on their input/output shape.

- Classification: loader returns `(images, labels)`, model returns scores, loss consumes scores and labels.
- Siamese: loader returns image pairs, model returns two embeddings, loss consumes the pair embeddings and a binary target.
- Triplet: loader returns triplets, model returns three embeddings, loss consumes the triplet embeddings.
- Online mining: loader returns mini-batches of images and labels, model usually returns embeddings, loss mines pairs or triplets from the batch.

## Distilled notebook defaults

### MNIST baseline classification

- `EmbeddingNet`
- `ClassificationNet(embedding_net, n_classes)`
- `NLLLoss`
- `Adam(lr=1e-2)`
- `StepLR(step_size=8, gamma=0.1)`
- `n_epochs = 20`

### Siamese MNIST

- `SiameseMNIST`
- `SiameseNet(EmbeddingNet())`
- `ContrastiveLoss(margin=1.0)`
- `Adam(lr=1e-3)`
- `n_epochs = 20`

### Triplet MNIST

- `TripletMNIST`
- `TripletNet(EmbeddingNet())`
- `TripletLoss(margin=1.0)`
- `Adam(lr=1e-3)`
- `n_epochs = 20`

### Online contrastive MNIST

- `BalancedBatchSampler(train_labels, n_classes=10, n_samples=25)`
- `EmbeddingNet()`
- `OnlineContrastiveLoss(margin=1.0, pair_selector=HardNegativePairSelector())`
- `Adam(lr=1e-3)`

### Online triplet MNIST

- `BalancedBatchSampler(train_labels, n_classes=10, n_samples=25)`
- `EmbeddingNet()`
- `OnlineTripletLoss(margin=1.0, triplet_selector=RandomNegativeTripletSelector(1.0))`
- `Adam(lr=1e-3, weight_decay=1e-4)`
- `AverageNonzeroTripletsMetric()`

## Notebook helper behavior to remember

- The notebooks extract 2D embeddings after training so they can plot train and test clusters.
- `extract_embeddings` walks a dataloader, switches the model to eval mode, and concatenates the results.
- `plot_embeddings` uses a fixed color palette for the 10 classes.
- FashionMNIST uses the same structure as MNIST with different class labels.

## Smoke strategy

The generated skill does not attempt the full notebook run. The bundled smoke uses tiny synthetic datasets and one-epoch fits to prove the contracts without downloading data.
