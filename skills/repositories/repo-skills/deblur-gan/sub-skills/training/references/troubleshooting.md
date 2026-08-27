# Training troubleshooting

## Common failures

### CUDA / GPU missing

**Symptom**: the training path crashes when it tries to move the perceptual-loss feature extractor or gradient-penalty tensors to CUDA.

**Likely cause**: the run is using a CPU-only PyTorch build or the host does not expose a CUDA device.

**Fix**:
- Install a CUDA-enabled PyTorch build that matches the host driver.
- Verify `torch.cuda.is_available()` before launching training.
- Do not expect the content-GAN training path to be truthful on CPU only.

### VGG19 weights are downloading or unavailable

**Symptom**: the first training run stalls or errors while building the perceptual loss.

**Likely cause**: `torchvision.models.vgg19` wants pretrained weights and the machine is offline or blocked.

**Fix**:
- Allow the download once if the machine can reach the model host.
- If the machine must stay offline, pre-stage the weights in the environment cache before the run.
- Do not treat a download failure as a model bug until the network path has been checked.

### visdom is missing

**Symptom**: the training run fails as soon as `Visualizer` tries to import visdom.

**Likely cause**: live plotting is enabled but `visdom` is not installed.

**Fix**:
- Install `visdom` if you want browser plotting.
- Otherwise run the bundled wrapper with headless settings such as `--display_id 0`.

### Checkpoint directory does not exist

**Symptom**: `Visualizer` fails when opening the log file.

**Likely cause**: `checkpoints_dir/name` has not been created yet.

**Fix**:
- Create the checkpoint directory before constructing the visualizer.
- The bundled wrapper does this for you.

### Paper-vs-source `gan_type` mismatch

**Symptom**: the run behaves differently from the README or paper description.

**Likely cause**: the shipped `train.py` hardcodes `gan_type = "gan"`, even though the README discusses a WGAN-GP style setup.

**Fix**:
- Use the bundled wrapper and choose the loss family explicitly.
- If you need the paper-style route, pass the desired `--gan_type` rather than inheriting the source override.

### Wrong or uninitialized dataroot

**Symptom**: the training run starts but cannot find images.

**Likely cause**: the source training script points at a local path that does not exist on your machine.

**Fix**:
- Always pass the correct `--dataroot` to the wrapper.
- Do not copy the hardcoded source dataroot into your own command.

## What to do next

- Once the training path is stable, move to inference for restoration or validation.
- If you only need to confirm the wiring, use the wrapper's smoke mode and a tiny fixture.
