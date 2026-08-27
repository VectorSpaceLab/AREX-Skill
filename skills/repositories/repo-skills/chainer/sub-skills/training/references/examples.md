# Example Families

The repo's examples are best understood as evidence families rather than isolated scripts.
Use this page to identify the reusable pattern represented by each family without depending on the original checkout at runtime.

## Vision and classification

- `examples/mnist`: the smallest end-to-end training and inference family.
  It includes single-GPU training, a custom training loop, data-parallel multi-GPU training, and model-parallel training.
- `examples/cifar`: a small convolutional image-classification workflow, with both standard and custom-loop variants.
- `examples/imagenet`: a larger ImageNet workflow that uses list files and a mean file.
- `examples/modelzoo` and `examples/caffe_export`: import or export pretrained vision models.

## Language and sequence models

- `examples/ptb`: recurrent language modeling.
- `examples/seq2seq`: sequence-to-sequence translation.
- `examples/text_classification`: text classification with reusable dataset and net helpers.
- `examples/word2vec`: word embedding training and search.
- `examples/image_captioning`: sequence modeling over image captions.
- `examples/wavenet`: audio generation and autoregressive modeling.

## Generative and probabilistic models

- `examples/vae`: variational autoencoder training.
- `examples/dcgan`: generative adversarial training.
- `examples/pix2pix`: paired image-to-image translation.
- `examples/glance`: tabular feature workflow and a small dense model.

## Reinforcement learning

- `examples/reinforcement_learning`: DQN, Double DQN, and DDPG recipes.

## Serialization and persistence

- `examples/serialization`: NPZ and HDF5 save/load examples.

## Static graph optimization

- `examples/static_graph_optimizations/*`: decorated MNIST, CIFAR, and PTB variants that exercise the experimental static graph path.

## What to treat as smoke-friendly

Smoke-friendly families are the ones that can be reduced to a tiny synthetic dataset or a short local run without downloads:

- MNIST-style toy training
- Serialization save/load
- Tiny export checks

## What to treat as reference-only

Treat the following as reference-only for the generated skill because they depend on external data, pretrained weights, heavy downloads, or large multi-process jobs:

- ImageNet training and model-zoo evaluation
- Large distributed training scripts
- Pretrained export recipes that assume external checkpoints
- Anything that requires MPI, NCCL, or multiple GPUs in a production-size cluster

The bundled smoke scripts cover the reusable core of these examples without depending on the original files.
