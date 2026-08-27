# TensorFlow API Reference

## Purpose

Read this when you need the verified module and helper signatures for the
TensorFlow example code.

## Verified shared utilities

From `tensorflow/vision/model/utils.py` and `tensorflow/nlp/model/utils.py`:

- `Params(json_path)` — load hyperparameters from a JSON file.
- `Params.save(json_path)` — write the current parameter set back to JSON.
- `Params.update(json_path)` — merge values from another JSON file.
- `set_logger(log_path)` — configure console and file logging.
- `save_dict_to_json(d, json_path)` — write metrics or config dicts.

## Vision module signatures

Verified from the live import inspection of `tensorflow/vision`:

- `model.input_fn.input_fn(is_training, filenames, labels, params)` — build a
  `tf.data` input pipeline for the SIGNS images.
- `model.model_fn.model_fn(mode, inputs, params, reuse=False)` — create the
  TensorFlow graph for training or evaluation.
- `model.training.train_and_evaluate(train_model_spec, eval_model_spec,
  model_dir, params, restore_from=None)` — train and evaluate over epochs.
- `model.evaluation.evaluate(model_spec, model_dir, params, restore_from)` —
  run test-set evaluation and write the metric JSON.
- `build_dataset.resize_and_save(filename, output_dir, size=SIZE)` — resize one
  image and save it to the processed output directory.

### Vision behavior notes

- `input_fn` uses `tf.data.Dataset.from_tensor_slices`, optional random flip,
  batching, and prefetching.
- `model_fn` expects an `images` tensor of shape
  `[None, params.image_size, params.image_size, 3]`.
- `train.py` uses `dev_signs` for evaluation, not `val_signs`.
- `evaluate.py` loads weights from the `restore_from` path or directory.

## NLP module signatures

Verified from the live import inspection of `tensorflow/nlp`:

- `model.input_fn.load_dataset_from_text(path_txt, vocab)` — create a text-line
  dataset from one tokenized text file.
- `model.input_fn.input_fn(mode, sentences, labels, params)` — zip the datasets,
  pad them, and create an iterator.
- `model.model_fn.model_fn(mode, inputs, params, reuse=False)` — create the
  graph for training or evaluation.
- `model.training.train_and_evaluate(train_model_spec, eval_model_spec,
  model_dir, params, restore_from=None)` — train and evaluate over epochs.
- `model.evaluation.evaluate(model_spec, model_dir, params, restore_from)` —
  run test-set evaluation and write the metric JSON.
- `build_vocab.update_vocab(txt_path, vocab)` — count tokens in one text file.
- `build_kaggle_dataset.load_dataset(path_csv)` — parse the Kaggle CSV into
  sentence/tag pairs.
- `build_kaggle_dataset.save_dataset(dataset, save_dir)` — write text splits.

### NLP behavior notes

- `load_dataset_from_text` returns token ids and sentence lengths.
- `input_fn` pads with the configured pad word and pad tag ids.
- `model_fn` uses `tf.nn.sparse_softmax_cross_entropy_with_logits` and masks
  padding tokens via `tf.sequence_mask`.
- `build_kaggle_dataset.py` splits into `train/`, `dev/`, and `test/`.
- `train.py` uses `restore_dir`, while `evaluate.py` uses `restore_from`.

## Verified configuration fields

From the starter experiment files and live code:

### Vision

- `learning_rate`
- `batch_size`
- `num_epochs`
- `num_channels`
- `use_batch_norm`
- `bn_momentum`
- `image_size`
- `use_random_flip`
- `num_labels`
- `num_parallel_calls`
- `save_summary_steps`

### NLP

- `model_version`
- `lstm_num_units`
- `embedding_size`
- `learning_rate`
- `batch_size`
- `num_epochs`
- `dropout_rate`
- `save_summary_steps`

## When to read this file

- You are about to use or explain a TensorFlow helper or model function.
- You need to know which utility writes checkpoints or metrics.
- You want to distinguish the vision and NLP data pipelines before debugging a
  training failure.
