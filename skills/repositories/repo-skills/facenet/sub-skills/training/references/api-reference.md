# Training API reference

## Loss functions

```python
facenet.triplet_loss(anchor, positive, negative, alpha)
```

Computes mean `max(pos_dist - neg_dist + alpha, 0)` over embedding rows.

```python
facenet.center_loss(features, label, alfa, nrof_classes)
```

Maintains a non-trainable `centers` variable and returns `(loss, centers_update)` for center-loss regularization.

## Training helper

```python
facenet.train(total_loss, global_step, optimizer, learning_rate, moving_average_decay, update_gradient_vars, log_histograms=True)
```

Optimizer choices in the source are `ADAGRAD`, `ADADELTA`, `ADAM`, `RMSPROP`, and `MOM`. The helper adds loss summaries, gradients, optional histograms, moving averages, and returns a `train` no-op with dependencies.

## Dataset helpers

```python
facenet.get_dataset(path, has_class_directories=True)
facenet.get_image_paths_and_labels(dataset)
facenet.split_dataset(dataset, split_ratio, min_nrof_images_per_class, mode)
```

`split_dataset` supports `SPLIT_CLASSES` and `SPLIT_IMAGES`.

## Schedule helper

```python
facenet.get_learning_rate_from_file(filename, epoch)
```

Reads `epoch:learning_rate` lines and ignores comments after `#`. In `train_softmax.py`, a selected non-positive learning rate stops training.

## Triplet mining helpers

```python
train_tripletloss.sample_people(dataset, people_per_batch, images_per_person)
train_tripletloss.select_triplets(embeddings, nrof_images_per_class, image_paths, people_per_batch, alpha)
```

These functions implement sampling and semi-hard/random negative selection for triplet training.
