# Helpers Workflows

## Purpose

Read this for end-to-end helper recipes: device selection, optimizer choice,
training-loop wiring, and the remote dataset pattern.

## 1) Build a small supervised trainer

Use `SimpleTrainValidConfigs` when you want a reusable skeleton for ordinary
supervised learning.

1. Define a config subclass with `model`, `optimizer`, `loss_func`, `device`,
   `train_loader`, and `valid_loader`.
2. Use `DeviceConfigs` to select CPU or CUDA with a clear fallback.
3. Use `OptimizerConfigs` when you want swapable `SGD`, `Adam`, or `Noam`
   behavior without changing the training loop.
4. Add state modules such as `Accuracy` or `Collector`.
5. Call `experiment.configs(conf, ...)` and then `conf.run()` inside an
   experiment.

The helper sample pattern is especially useful when the loop is the same but the
model or optimizer changes often.

## 2) Use `TrainingLoopConfigs` directly

Choose `TrainingLoopConfigs` when you need loop timing, checkpoint cadence, or
signal-aware iteration management without the full train/valid abstraction.

- Set `loop_count` and `loop_step` to control the iteration schedule.
- Enable `is_save_models` if you want automatic checkpointing.
- Adjust `log_new_line_interval` and `log_write_interval` for cleaner output.
- Use the loop object from `conf.training_loop` in your own custom training
  code.

## 3) Pick the right metric helpers

- Use `Accuracy` for ordinary multiclass classification.
- Use `BinaryAccuracy` when your model output is binary and already thresholded.
- Use `Collector` when you want to collect arbitrary outputs for later analysis.
- Use `RecallPrecision` when precision/recall is the primary output.

The helpers manage state for you, so you only need to call the metric object in
training or validation code and let `on_epoch_start`/`on_epoch_end` do the
bookkeeping.

## 4) Use packaged dataset configs

`MNISTConfigs` and `CIFAR10Configs` are ready-made examples of how to build a
configurable dataset pipeline.

- They expose dataset, transform, and loader config items.
- They are a good pattern when you want a reusable data block for multiple
  experiments.
- They do download the dataset when the underlying torchvision dataset needs it,
  so treat them as networked examples rather than the default smoke path.

## 5) Share a dataset over HTTP

The remote dataset helper is useful when you want the training process to read a
local or LAN-hosted dataset through a simple HTTP API.

1. Build a torch dataset in the host process.
2. Create a `DatasetServer` and call `add_dataset(name, dataset)`.
3. Start the server on a local port.
4. In the consumer process, instantiate `RemoteDataset(name, host, port)` and
   feed it to a `DataLoader`.

This pattern is especially helpful for local multi-process demos and for keeping
small examples self-contained.

## 6) Remote dataset smoke path

Use `scripts/remote_dataset_smoke.py` when you need a tiny loopback validation
without downloading MNIST or standing up a real remote server.
