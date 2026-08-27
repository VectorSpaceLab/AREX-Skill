# Model Overview

## Purpose

Read this when you need to choose a model family for a dataset or understand
why some algorithms expect a model head named `fc`.

## Dataset families and common models

### MNIST and Fashion-MNIST

- `Mclr_Logistic(1*28*28)`
- `LeNet()`
- `DNN(1*28*28, 100)`

### CIFAR-10, CIFAR-100, and Tiny-ImageNet

- `Mclr_Logistic(3*32*32)`
- `FedAvgCNN()`
- `DNN(3*32*32, 100)`
- `ResNet18`, `ResNet34`, `AlexNet`, `MobileNet`, `GoogleNet`

### AG News and Sogou News

- `LSTM()` / `LSTMNet`
- `fastText()`
- `TextCNN()`
- `TransformerModel()`

### Amazon Review

- `AmazonMLP()`

### Omniglot

- `FedAvgCNN()`

### HAR and PAMAP2

- `HARCNN()`

## Important model hooks

The experiment runner expects many algorithms to access or replace the model's
`fc` layer. That is why the built-in registry often wraps the backbone in
`BaseHeadSplit` or replaces `fc` with `nn.Identity()` before constructing the
algorithm.

Algorithms that rely on this pattern include the common head-sharing or
personalization methods such as:

- FedAvg
- FedPer
- FedRep
- FedPHP
- FedROD
- FedProto
- MOON
- FedBABU
- FedGen
- FedPAC
- FedKD
- FedCP
- GPFL
- FedGH
- FedDBE
- PFL-DA
- FedLC
- FedAS

## Practical selection notes

- Use the image families for label-skew CV experiments.
- Use the text families only when `torchtext` is installed and the vocabulary
  size / max length flags match the dataset.
- Use `HARCNN()` when the dataset is HAR or PAMAP2; it is shaped for the
  sensor windows produced by the HAR helpers.
- If you are adding a new model, check whether the chosen algorithm expects a
  single classifier head, a backbone/head split, or a pure end-to-end module.
