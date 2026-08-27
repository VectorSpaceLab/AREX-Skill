# Training and data API reference

This is a distilled map of the training-related entry points and classes.

## Training CLI

Public entry point: `train.py`.

| Argument | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `--data_input_path` | string | yes | none | Flat directory containing paired `.png` and `.gui` files. |
| `--validation_split` | float | no | `0.2` | Fraction copied to validation using `int(split * sample_count)`. |
| `--epochs` | int | yes | none | Number of training epochs. |
| `--model_output_path` | string | yes | none | Created if missing; receives model JSON, weights, checkpoints, and CSV logs. |
| `--model_json_file` | string | no | none | Pretrained model architecture JSON. Requires matching weights to load. |
| `--model_weights_file` | string | no | none | Pretrained weights. Requires matching JSON to load. |
| `--augment_training_data` | int | no | `1` | `1` enables Keras image augmentation for training images. |

Main flow:

```text
parse flags
SketchCodeModel(model_output_path, model_json_file, model_weights_file)
ensure model_output_path exists
ModelUtils.prepare_data_for_training(data_input_path, validation_split, augment_training_data)
model.train(training_path, validation_path, epochs)
```

## Dataset

Construction:

```text
Dataset(data_input_folder, test_set_folder=None)
```

Key constants:

| Constant | Value |
| --- | --- |
| `VOCAB_FILE` | `../vocabulary.vocab` |
| `TRAINING_SET_NAME` | `training_set` |
| `VALIDATION_SET_NAME` | `validation_set` |
| `BATCH_SIZE` | `64` |

Important methods:

| Method | Purpose | Notes |
| --- | --- | --- |
| `split_datasets(validation_split)` | Build train/validation sample IDs and copy pairs into split folders. | Calls `populate_sample_ids`, `get_all_id_sets`, then `split_samples`. |
| `preprocess_data(training_path, validation_path, augment_training_data)` | Convert PNGs in split folders to `.npz` features. | Training uses requested augmentation; validation uses no augmentation. |
| `load_vocab()` | Load tokenizer and vocabulary size from `../vocabulary.vocab`. | Path is relative to process current working directory. |
| `create_generator(data_input_path, max_sequences)` | Load split data and return `(generator, steps_per_epoch)`. | Counts GUI tokens and divides by `BATCH_SIZE`. |
| `load_data(data_input_path)` | Load `.npz` feature arrays and `.gui` text from a split folder. | Wraps each GUI text in `<START>` and `<END>`, normalizes whitespace, separates commas. |
| `populate_sample_ids()` | Return sample stems that have both `.gui` and `.png`. | Missing pairs are omitted. |
| `create_data_folders()` | Create split folder paths. | Deletes existing sibling `training_set` and `validation_set` first. |

## ImagePreprocessor

Construction:

```text
ImagePreprocessor()
```

Key methods:

| Method | Purpose | Output |
| --- | --- | --- |
| `build_image_dataset(data_input_folder, augment_data=True)` | Convert all PNGs in a folder into `.npz` feature files. | Writes one `.npz` per PNG stem. |
| `get_img_features(png_path)` | Return resized/thresholded normalized features for one PNG. | Asserts shape `(256, 256, 3)`. |
| `resize_img(png_file_path)` | Internal OpenCV preprocessing path. | Grayscale, adaptive threshold, 200x200 resize, centered on 256x256 white canvas, normalized. |
| `augment_and_save_images(...)` | Apply Keras `ImageDataGenerator` and save features. | Rotation range 2, width/height shift 0.05, zoom 0.05. |
| `save_resized_img_arrays(...)` | Save non-augmented `.npz` features. | Uses key `features`. |

## ModelUtils

Static method:

```text
ModelUtils.prepare_data_for_training(data_input_folder, validation_split, augment_training_data)
```

Behavior:

1. Creates `Dataset(data_input_folder)`.
2. Splits samples into sibling `training_set` and `validation_set` folders.
3. Preprocesses images into `.npz` feature files.
4. Returns `(training_path, validation_path)`.

## SketchCodeModel

Construction:

```text
SketchCodeModel(model_output_path, model_json_file=None, model_weights_file=None)
```

Behavior:

- If both `model_json_file` and `model_weights_file` are provided, loads the model from disk and compiles it.
- Otherwise creates a new CNN + GRU model using the loaded vocabulary size.
- Prints the Keras model summary.

Key methods:

| Method | Purpose |
| --- | --- |
| `load_model(model_json_file, model_weights_file)` | Load JSON architecture and weights with Keras `model_from_json`. |
| `create_model()` | Build the CNN image encoder, GRU language encoder, decoder, optimizer, and loss. |
| `train(training_path, validation_path, epochs)` | Create generators, callbacks, call `fit_generator`, then save final JSON and weights. |
| `save_model()` | Write `model_json.json` and `weights.h5` to the model output directory. |
| `construct_callbacks(validation_path)` | Create `ModelCheckpoint` and `CSVLogger` callbacks. |

## Bundled validator

Runtime helper:

```sh
python sub-skills/training-data/scripts/validate_training_dataset.py --help
python sub-skills/training-data/scripts/validate_training_dataset.py DATASET_DIR
```

It uses only the Python standard library by default, plus optional Pillow image checks if Pillow is installed. It never imports TensorFlow, Keras, OpenCV, or NumPy.
