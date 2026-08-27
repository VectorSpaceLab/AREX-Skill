# Helpers Troubleshooting

## Purpose

Read this when helper training loops, metrics, devices, or the remote dataset
service fail.

## Common issues

### `torch`, `torchvision`, or remote-dataset support imports are missing

**Symptoms**
- Import errors at the top of helper scripts.
- Dataset or transform constructors fail immediately.
- `RemoteDataset` fails on import because `matplotlib` or `urllib3` is missing.

**Likely cause**
- The PyTorch runtime, torchvision, or the remote-dataset helper imports were not installed.

**Recovery**
- Install the PyTorch runtime first, then reinstall the helper package.
- For `labml_helpers.datasets.remote`, also install `matplotlib`, `urllib3`, `fastapi`, and `uvicorn`.
- Re-run the helpers smoke script or the remote dataset smoke script.

### `DeviceConfigs` falls back to CPU

**Symptoms**
- The config resolves to CPU even on a GPU host.

**Likely cause**
- CUDA is unavailable, disabled, or the host lacks a compatible driver.

**Recovery**
- Confirm `torch.cuda.is_available()` in the health check.
- Check the driver and the PyTorch wheel variant.
- If CPU is acceptable, keep the fallback and do not treat it as an error.

### `Module.device` raises an error

**Symptoms**
- `RuntimeError: Unable to determine device of ...`

**Likely cause**
- The module has no parameters, so there is no device to infer.

**Recovery**
- Make sure the model contains at least one parameter or pass the device from a
  surrounding config.

### Optimizer configuration errors

**Symptoms**
- `OptimizerConfigs` does not resolve the expected optimizer.
- `NoamOpt` or `Adam` is not chosen as expected.

**Likely cause**
- The nested optimizer choice was not set through config overrides.

**Recovery**
- Override the nested choice explicitly, for example `optimizer.optimizer`.
- Re-run the smoke script and inspect the printed optimizer type.

### Dataset downloads are slow or fail

**Symptoms**
- MNIST or CIFAR examples stall or retry network downloads.

**Likely cause**
- The example relies on torchvision downloads or the host has no network.

**Recovery**
- Use the synthetic smoke script instead of the networked dataset examples.
- Provide cached data when the training example truly needs the full dataset.

### Remote dataset client times out

**Symptoms**
- `RemoteDataset` hangs, times out, or fails to fetch an item.

**Likely cause**
- The dataset server is not running, the host/port is wrong, or the port is in
  use.

**Recovery**
- Start the server first and make sure the host and port match.
- Use the loopback smoke script to verify the pattern locally.

### Training-loop progress looks wrong

**Symptoms**
- `BatchIndex` or progress calculations seem off.

**Likely cause**
- The data loader length, loop count, or `inner_iterations` setting does not
  match the intended epoch structure.

**Recovery**
- Re-check `loop_count`, `loop_step`, and `inner_iterations`.
- Compare the loop math against the workflow reference before debugging model
  code.

## Read next

- `helpers/scripts/helpers_smoke.py` for a safe synthetic trainer.
- `helpers/scripts/remote_dataset_smoke.py` for a loopback dataset-service test.
