# Built-in Models, Datasets, and Run Scripts

This reference summarizes the PocketFlow source workflow names a future operator will see in an active checkout. Names are provided for orientation; they are not links to repository files. The bundled skeleton generator in this sub-skill is separate from these official source scripts.

## Built-in and example combinations

| Combination | Run script pattern | Dataset helper | ModelHelper highlights | Data assumptions |
| --- | --- | --- | --- | --- |
| LeNet-like model on CIFAR-10 | `nets/lenet_at_cifar10_run.py` | `Cifar10Dataset` | Simple classification helper; useful as a compact built-in pattern; supports `channels_last` and `channels_first` with explicit transpose. | CIFAR-10 binary batches: `data_batch_*.bin` for train and `test_batch.bin` for eval; 32x32 RGB; 10 classes. |
| ResNet on CIFAR-10 | `nets/resnet_at_cifar10_run.py` | `Cifar10Dataset` | `resnet_size` default 20; `model_name` becomes `resnet_<size>`; softmax loss plus top-1 accuracy. | Same CIFAR-10 binary layout as LeNet. |
| ResNet on ILSVRC-12 | `nets/resnet_at_ilsvrc12_run.py` | `Ilsvrc12Dataset` | `resnet_size` default 18; deeper versions use bottleneck blocks; reports top-1/top-5 metrics. | TFRecord shards named `train-*-of-*` and `validation-*-of-*`; 224x224 RGB; `nb_classes` is 1001. |
| MobileNet on ILSVRC-12 | `nets/mobilenet_at_ilsvrc12_run.py` | `Ilsvrc12Dataset` | `mobilenet_version` 1 or 2; `mobilenet_depth_mult`; asserts `channels_last` only. | Same ILSVRC-12 TFRecord layout as ResNet/ImageNet. |
| SSD/VGG on Pascal VOC | `nets/vgg_at_pascalvoc_run.py` | `PascalVocDataset` | Detection output dict; anchor setup; `warm_start()` from a backbone checkpoint; `dump_n_eval()` writes VOC-style detection results. | Pascal VOC TFRecords matching `*train*` and `*val*`; image size 300; 21 classes including background. |
| Faster R-CNN on Pascal VOC | `nets/faster_rcnn_at_pascalvoc_run.py` | `PascalVocDataset` | Label-aware forward pass with `forward_w_labels=True`; external Faster R-CNN configs select ResNet or MobileNetV2 backbones; detection dump/eval hook. | Same Pascal VOC TFRecord family; uses packed object annotations and detection-specific config constants. |
| Fashion-MNIST custom example | `convnet_at_fmnist_run.py` example script | `FMnistDataset` | Example of adding a dataset helper, model helper, and run script for a custom classification task; distill its pattern rather than copying it blindly. | Fashion-MNIST gzip files; 28x28 grayscale; 10 classes. |

## Dataset formats by helper

### `Cifar10Dataset`

- Reader: `tf.data.FixedLengthRecordDataset`.
- Record: one label byte followed by `32 * 32 * 3` image bytes.
- Parser reshapes to CHW, transposes to NHWC, normalizes by fixed RGB means/stds, and one-hot encodes labels.
- Training augmentation: pad/crop and random horizontal flip.
- Key flags: `nb_classes=10`, `nb_smpls_train=50000`, `nb_smpls_eval=10000`, `batch_size=128`, `batch_size_eval=100`.

### `Ilsvrc12Dataset`

- Reader: `tf.data.TFRecordDataset`.
- Parses `image/encoded`, `image/class/label`, and optional bounding boxes from `tf.Example` records.
- Uses ImageNet preprocessing to produce 224x224 RGB images and one-hot labels.
- Key flags: `nb_classes=1001`, `nb_smpls_train=1281167`, `nb_smpls_eval=50000`, `batch_size=64`, `batch_size_eval=100`.

### `PascalVocDataset`

- Reader: `tf.data.TFRecordDataset`.
- Parses JPEG bytes, filename, raw shape, boxes, labels, difficult/truncated flags.
- Returns an image-info dictionary plus a padded object tensor rather than a plain classification image/label pair.
- Filters difficult objects for training, packs boxes and labels, and uses detection-specific preprocessing.
- Key flags: `image_size=300`, `image_size_eval=300`, `nb_bboxs_max=100`, `nb_classes=21`, `batch_size=32`, `batch_size_eval=1`.

### Fashion-MNIST-style custom dataset

- Reads gzip image/label files into NumPy arrays in the dataset constructor.
- Overrides `build()` to create `tf.data.Dataset.from_tensor_slices` rather than using file listing.
- Uses the same train/eval split and iterator return conventions as `AbstractDataset`.

## Path-key conventions

PocketFlow's launcher helpers derive the dataset key from the run-script filename, not from `ModelHelper.dataset_name`.

- Expected filename shape: `*_at_<dataset_key>_run.py`.
- The source parser accepts alphanumeric `<dataset_key>` values.
- It then looks for keys such as `data_dir_local_<dataset_key>`, `data_dir_hdfs_<dataset_key>`, `data_dir_docker_<dataset_key>`, and `data_dir_seven_<dataset_key>` in `path.conf`.
- Built-in examples use keys such as `cifar10`, `ilsvrc12`, and custom examples may add a key such as `fmnist`.
- `ModelHelper.dataset_name` can intentionally differ for checkpoint naming, for example `cifar_10` versus the path key `cifar10`.

For path generation, command preview, and launcher mode details, use [execution-config](../../execution-config/SKILL.md).

## Pretrained and warm-start naming

- Learner model download uses `model_http_url` plus the helper-derived archive name `models_<model_name>_at_<dataset_name>.tar.gz`.
- Classification helpers typically rely on `model_name` and `dataset_name` for pretrained checkpoint discovery.
- Detection helpers may also need a backbone checkpoint directory, such as `backbone_ckpt_dir`, and may remap scope names during `warm_start()`.
- When cloning a built-in helper for a custom task, update names deliberately; changing names after checkpoints exist can break eval/download lookup.

## Choosing a base to adapt

- Use LeNet/CIFAR-10 or the Fashion-MNIST-style example for a small custom image classifier.
- Use ResNet/CIFAR-10 when the task is CIFAR-like but the model should exercise residual blocks and standard compression learners.
- Use ResNet or MobileNet/ImageNet when the custom dataset is large-image classification and preprocessing resembles ImageNet. Remember MobileNet is `channels_last` only.
- Use SSD/VGG or Faster R-CNN/Pascal VOC only when the custom task needs detection-style inputs, packed annotations, warm-start, and dump/eval hooks.
- Once the model/data contract is set, route learner choice and algorithm flags to [compression-learners](../../compression-learners/SKILL.md).
