# API Overview

## Purpose

Read this page when you want the package-wide map of verified TensorLayer modules and the live signatures that were checked during skill construction.

## Verified package facts

- Distribution: `tensorlayer`
- Import name: `tensorlayer`
- Verified package version: `2.2.4`
- Verified TensorFlow runtime during inspection: `2.21.0`
- Root import currently loads app/vision modules, so `matplotlib` is part of the practical runtime set for `import tensorlayer`.

## Package map

| Module | What it covers | Main sub-skill |
| --- | --- | --- |
| `tensorlayer.layers` | Layers, connectors, and layer containers | `core-modeling` |
| `tensorlayer.models` | `Model` plus pretrained constructors | `core-modeling` / `vision-and-apps` |
| `tensorlayer.files` | Datasets, persistence, downloads, file helpers | `data-and-utilities` |
| `tensorlayer.prepro` | Affine transforms and preprocessing | `data-and-utilities` |
| `tensorlayer.iterate` | Minibatches and sequence iteration | `data-and-utilities` |
| `tensorlayer.visualize` | Image drawing and visualization helpers | `data-and-utilities` / `vision-and-apps` |
| `tensorlayer.utils` | Fit/test/predict/evaluation helpers | `training-and-cli` |
| `tensorlayer.cli` | `tl` command and the `train` subcommand | `training-and-cli` |
| `tensorlayer.distributed` | Horovod-based distributed trainer | `training-and-cli` |
| `tensorlayer.nlp` | Tokenization, word ids, sampling, BLEU, vocabulary helpers | `text-and-sequence` |
| `tensorlayer.rein` | Reward and action-selection helpers | `reinforcement-learning` |
| `tensorlayer.app` | YOLOv4 and pose wrappers | `vision-and-apps` |
| `tensorlayer.activation` / `cost` / `initializers` / `optimizers` | Core math and building blocks | `core-modeling` |

## Live signatures that were verified

These were inspected from the installed package and are safe to rely on:

- `vgg16(pretrained=False, end_with='outputs', mode='dynamic', name=None)`
- `MobileNetV1(pretrained=False, end_with='out', name=None)`
- `ResNet50(pretrained=False, end_with='fc1000', n_classes=1000, name=None)`
- `SqueezeNetV1(pretrained=False, end_with='out', name=None)`
- `Seq2seq(decoder_seq_length, cell_enc, cell_dec, n_units=256, n_layer=3, embedding_layer=None, name=None)`
- `Seq2seqLuongAttention(hidden_size, embedding_layer, cell, method, name=None)`
- `Model.save(self, filepath, save_weights=True, customized_data=None)`
- `Model.load(filepath, load_weights=True)`
- `Model.save_weights(self, filepath, format=None)`
- `Model.load_weights(self, filepath, format=None, in_order=True, skip=False)`
- `tl.utils.fit(network, train_op, cost, X_train, y_train, acc=None, batch_size=100, n_epoch=100, print_freq=5, X_val=None, y_val=None, eval_train=True, tensorboard_dir=None, tensorboard_epoch_freq=5, tensorboard_weight_histograms=True, tensorboard_graph_vis=True)`
- `tl.utils.test(network, acc, X_test, y_test, batch_size, cost=None)`
- `tl.utils.predict(network, X, batch_size=None)`
- `load_mnist_dataset(shape=(-1, 784), path='data')`
- `load_cifar10_dataset(shape=(-1, 32, 32, 3), path='data', plotable=False)`
- `save_weights_to_hdf5(filepath, network)`
- `affine_transform_cv2(x, transform_matrix, flags=None, border_mode='constant')`
- `affine_rotation_matrix(angle=(-20, 20))`
- `generate_skip_gram_batch(data, batch_size, num_skips, skip_window, data_index=0)`
- `discount_episode_rewards(rewards=None, gamma=0.99, mode=0)`
- `Trainer(training_dataset, build_training_func, optimizer, optimizer_args, batch_size=32, prefetch_size=None, checkpoint_dir=None, scaling_learning_rate=True, log_step_size=1, validation_dataset=None, build_validation_func=None, max_iteration=inf)`
- `build_arg_parser(parser)`

## Where to go next

- For layer and model workflow details, read `sub-skills/core-modeling/references/api-reference.md`.
- For data, preprocessing, and TFRecord helpers, read `sub-skills/data-and-utilities/references/api-reference.md`.
- For training loops and CLI usage, read `sub-skills/training-and-cli/references/cli-reference.md`.
- For pretrained image models and app wrappers, read `sub-skills/vision-and-apps/references/model-overview.md`.
- For NLP and seq2seq details, read `sub-skills/text-and-sequence/references/nlp-reference.md`.
- For reinforcement-learning helpers, read `sub-skills/reinforcement-learning/references/rl-reference.md`.
