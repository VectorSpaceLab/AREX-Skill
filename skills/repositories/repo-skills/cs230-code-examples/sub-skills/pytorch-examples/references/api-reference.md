# PyTorch API Reference

## Purpose

Read this when you need the verified module and helper signatures for the
PyTorch example code.

## Verified shared utilities

From `pytorch/vision/utils.py` and `pytorch/nlp/utils.py`:

- `Params(json_path)` — load hyperparameters from a JSON file.
- `Params.save(json_path)` — write the current parameter set back to JSON.
- `Params.update(json_path)` — merge values from another JSON file.
- `RunningAverage()` — maintain a running average of scalar values.
- `RunningAverage.update(val)` — add one value.
- `RunningAverage()` as a callable — return the current average.
- `set_logger(log_path)` — configure console and file logging.
- `save_dict_to_json(d, json_path)` — write metrics or config dicts.
- `save_checkpoint(state, is_best, checkpoint)` — save `last.pth.tar` and,
  when `is_best` is true, `best.pth.tar`.
- `load_checkpoint(checkpoint, model, optimizer=None)` — restore model and
  optionally optimizer state.

## Vision module signatures

Verified from the live import inspection of `pytorch/vision`:

- `model.net.Net(params)` — convolutional classifier for SIGNS.
- `model.net.loss_fn(outputs, labels)` — negative log-likelihood over the
  batch.
- `model.net.metrics` — dictionary containing `accuracy`.
- `model.data_loader.fetch_dataloader(types, data_dir, params)` — build
  `torch.utils.data.DataLoader` objects for the requested splits.
- `build_dataset.resize_and_save(filename, output_dir, size=SIZE)` — resize one
  image and save it into the processed output directory.

### Vision behavior notes

- `fetch_dataloader` uses `train_transformer` for the training split and
  `eval_transformer` for validation/test.
- The training split shuffles; validation and test do not.
- `train.py` and `evaluate.py` move batches to CUDA automatically when
  `params.cuda` is true.
- `Net` expects three-channel 64x64 images after preprocessing.

## NLP module signatures

Verified from the live import inspection of `pytorch/nlp`:

- `model.net.Net(params)` — recurrent NER model.
- `model.net.loss_fn(outputs, labels)` — cross-entropy loss with padding masked
  out.
- `model.net.accuracy(outputs, labels)` — token accuracy with padding masked
  out.
- `model.net.metrics` — dictionary containing `accuracy`.
- `model.data_loader.DataLoader(data_dir, params)` — load vocabularies and
  dataset metadata.
- `DataLoader.load_data(types, data_dir)` — load the requested dataset splits.
- `DataLoader.data_iterator(data, params, shuffle=False)` — yield padded
  `torch.LongTensor` batches.
- `build_vocab.update_vocab(txt_path, vocab)` — count tokens in one text file.
- `build_kaggle_dataset.load_dataset(path_csv)` — parse the Kaggle CSV into
  sentence/tag pairs.
- `build_kaggle_dataset.save_dataset(dataset, save_dir)` — write text splits.

### NLP behavior notes

- `DataLoader` expects `dataset_params.json`, `words.txt`, and `tags.txt`.
- Padding labels are marked with `-1` and excluded from the loss and accuracy.
- `build_vocab.py` writes the dataset summary JSON used by the training and
  evaluation scripts.
- `build_kaggle_dataset.py` assumes the simple Kaggle file name
  `ner_dataset.csv`.

## Verified configuration fields

From the starter experiment files and live code:

### Vision

- `learning_rate`
- `batch_size`
- `num_epochs`
- `dropout_rate`
- `num_channels`
- `save_summary_steps`
- `num_workers`

### NLP

- `learning_rate`
- `batch_size`
- `num_epochs`
- `lstm_hidden_dim`
- `embedding_dim`
- `save_summary_steps`

## When to read this file

- You are about to use or explain a PyTorch helper or model class.
- You need to know which utility writes checkpoints or metrics.
- You want to distinguish the vision and NLP data iterators before debugging a
  training failure.
