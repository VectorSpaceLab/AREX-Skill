# Acoustic-model troubleshooting

Use this reference for failures around ASRT Keras/PyTorch acoustic model construction, CTC training/evaluation, prediction, weights, and devices.

## TensorFlow CPU/GPU mismatch

Symptoms:

- TensorFlow imports fail with CUDA or shared-library errors.
- A GPU is visible on the host but TensorFlow does not list GPU devices.
- Training runs unexpectedly on CPU or runs out of memory immediately.

What the ASRT evidence says:

- README training expectations include NVIDIA GPU with roughly 11 GB+ graphics memory, Python 3.9+, and TensorFlow 2.5-2.11+.
- `requirements.txt` pins `tensorflow-gpu==2.8.4`.
- The Dockerfile installs `tensorflow-cpu==2.5.3` for CPU-only service inference.
- A separate installed fact verified TensorFlow CPU 2.11 can instantiate `SpeechModel251BN`; that is not a CUDA training proof.

Actions:

1. Run `scripts/inspect_keras_model.py --model 251bn` to check import and graph construction.
2. Inspect `tf.config.list_physical_devices()` output from the script.
3. If training is intended, align Python, TensorFlow, CUDA, and cuDNN versions in the target environment; do not use CPU construction as proof that GPU training is ready.
4. If only prediction is intended, CPU TensorFlow can be acceptable if latency is tolerable and weights load successfully.

## Missing trained weights

Symptoms:

- `FileNotFoundError`, Keras HDF5 load errors, or random/unusable predictions.

Actions:

- For `ModelSpeech.load_model(...)`, pass the full `.model.h5` file path, not just a prefix.
- For base inference only, load `.model.base.h5` directly into `sm.get_eval_model().load_weights(...)`.
- Match the model variant and dimensions used to create the weights. Default `SpeechModel251BN` model name is `SpeechModel251bn`.
- Do not claim recognition quality without trained weights.

## Wrong saved weight filename

Symptoms:

- Loading `save_models/SpeechModel251bn` fails.
- Loading `.model.base.h5` through `ms.load_model(...)` fails or gives layer mismatch.

Actions:

- Remember that `save_model(prefix)` writes both `prefix + '.model.h5'` and `prefix + '.model.base.h5'`.
- `load_model(filename)` expects an actual Keras weight filename. Use `.model.h5` for resume/evaluation through the training graph.
- Use `.model.base.h5` only when directly loading the base model for inference.

## Missing datasets or bad datalists

Symptoms:

- `DataLoader('train')` or `DataLoader('dev')` fails before training/evaluation.
- Generator stops with `[error] generator error. please check data format.`

Actions:

- Route dataset schema and `asrt_config.json` questions to `data-and-features`.
- Confirm dataset split names are `train`, `dev`, or `test`.
- Confirm pinyin dictionary and label tokens match; labels are mapped by ASRT's pinyin dictionary.
- Do not start acoustic training until data paths, list files, and label files are coherent.

## Overlong audio

Symptoms:

- Evaluation prints that wave data length is too long and skips a sample.
- Single-file prediction raises a NumPy broadcasting error or CTC length issue.

Cause:

- Default acoustic input length is 1600 frames, described by the README as about 16 seconds.
- Evaluation checks `data_input.shape[0] > speech_model.input_shape[0]`; single-file prediction does not pre-check before `forward`.

Actions:

- Split long audio into utterances shorter than the model input limit.
- Pre-run `Spectrogram().run(...)` and check frame count before prediction if graceful failure is required.

## `No valid path found` or infinite CTC loss

Symptoms:

- TensorFlow/Keras CTC reports no valid alignment path.
- Training loss becomes `inf`.

Relevant source note:

- The data generator computes input lengths from the feature length and pool size, with a comment saying the modulo/pool-size adjustment is required to avoid `inf` and `No valid path found`, but must not exceed the maximum output time length.

Actions:

- Verify label length does not exceed the acoustic/CTC capacity and `max_label_length=64`.
- Verify extracted feature length is not zero and not longer than `input_shape[0]`.
- Verify pinyin labels are valid dictionary tokens.
- Reduce batch complexity or remove malformed samples before blaming model architecture.

## `fit_generator` deprecation

Symptoms:

- New TensorFlow/Keras warns that `fit_generator` is deprecated or fails if the alias is removed.

Actions:

- In a local adaptation, replace `trained_model.fit_generator(yielddatas, num_iterate, callbacks=call_back)` with an equivalent `trained_model.fit(yielddatas, steps_per_epoch=num_iterate, callbacks=call_back)` after checking the installed TensorFlow API.
- Keep the source behavior in mind when comparing logs from older ASRT instructions.

## Memory requirements

Symptoms:

- Out-of-memory during Keras model construction, training, or prediction.

Actions:

- Use `scripts/inspect_keras_model.py` first to separate graph-construction failures from data/training memory pressure.
- Lower `batch_size` below the source default of `16` for constrained environments.
- Use shorter utterances or filter overlong files.
- Treat README's 16 GB+ RAM and 11 GB+ NVIDIA GPU training guidance as expectations for normal training, not as a guaranteed minimum for every model/data combination.

## PyTorch bfloat16/device pitfalls

Symptoms:

- PyTorch operations fail on CPU due to `bfloat16` support.
- CUDA is available but training is very slow or fails in convolution/batch norm.
- Saved PyTorch path is not where expected.

Actions:

- Read `references/pytorch-backend.md` before using the PyTorch route.
- Run a tiny target-hardware smoke before long training.
- Check that `save_models_torch` exists and that the `save_weight` filename argument does not already include unintended `.pth` or nested paths.
- Do not claim Keras/PyTorch parity, CUDA readiness, or CPU-as-GPU verification without explicit target-environment evidence.
