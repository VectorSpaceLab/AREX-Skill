# Data and Device Handling

## DataManager shapes

- A batch is typically a tuple whose first element is a tuple of model inputs and whose optional second element is labels.
- `DataManager.from_dataloader(...)` accepts standard Torch dataloaders and TensorFlow datasets and normalizes them into the repository's batch format.
- If a batch contains one tensor and one label tensor, the helper wraps the tensor in a tuple so the model input format is consistent.
- If the batch contains multiple input tensors, the last element is treated as the label by default unless the batch is already split into `(inputs, labels)`.

## Device parsing

- `cpu` returns a CPU device.
- `cuda`, `gpu`, `cuda:1`, and `gpu:1` request a GPU device.
- `tpu` and `tpu:1` request a TPU device.
- `neuron` and `neuron:1` request an AWS Inferentia/Neuron device.
- If the requested accelerator is not available, `check_device` falls back to CPU and logs a warning.

## Device helpers

- `Device.from_str(...)` mirrors the `check_device` parsing logic for `cpu`, `gpu`, `cuda`, `tpu`, and `neuron` strings.
- `Device.to_torch_format()` returns strings such as `cpu`, `cuda:0`, or `xla:0`.
- `Device.to_tf_format()` returns `CPU` or `GPU:<idx>`.
- `gpu_is_available()` shells out to `nvidia-smi`.
- `tpu_is_available()` checks `torch_xla`.
- `neuron_is_available()` checks `neuron-ls`.

## Use this when

You need to explain why a model fell back to CPU, why a batch was reshaped, or how to prepare a tiny input example for backend probing.
