# Graph Augmentation Troubleshooting

## CUDA and Device Usage

- GraphAug runners choose CPU or CUDA automatically.
- S-Mixup uses `.cuda()` in several places and is effectively a CUDA-oriented workflow.

## TripleSet / Label Issues

- The reward generator expects anchor, positive, and negative samples with label metadata.
- If labels are missing or multi-label, create a custom dataset wrapper rather than forcing `TripleSet`.

## Dataset and Config Mismatch

- GraphAug example configs assume specific TU dataset names and feature dimensions.
- If the input graph has no node features, use the degree transform before training or the model dimensions will be wrong.
