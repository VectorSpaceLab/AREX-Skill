# Troubleshooting

## Purpose

Use this reference for install, import, data, checkpoint, and legacy backend
failures that commonly show up in the couplet workflows.

## 1. TensorFlow import fails with protobuf descriptor errors

**Symptom**

- Importing `tensorflow` or any module that imports TensorFlow fails with a
  traceback that mentions protobuf descriptors being created directly.

**Likely cause**

- The protobuf package is too new for TensorFlow 1.15.

**Recovery**

1. Reinstall the verified dependency set from the bundled installer.
2. Keep `protobuf` pinned to `3.20.3` or lower.
3. Rerun `scripts/check_env.py`.

## 2. Beam-search graph build fails with a symbolic Tensor / NumPy error

**Symptom**

- Building the inference or eval graph fails with a message like `Cannot convert
  a symbolic Tensor ... to a numpy array`.

**Likely cause**

- NumPy is too new for TensorFlow 1.15's legacy beam-search decoder.

**Recovery**

1. Use the bundled dependency installer or install `numpy==1.18.5`.
2. Re-run the training or serving smoke.
3. Keep this pin separate from model-quality debugging; it is an environment
   compatibility issue.

## 3. TensorFlow prints missing CUDA 10 library warnings

**Symptom**

- Import logs mention missing `libcudart`, `libcublas`, `libcudnn`, or similar
  legacy CUDA 10 libraries.
- `tf.test.is_gpu_available()` reports false.

**Likely cause**

- The environment does not have the legacy GPU libraries that TensorFlow 1.15
  expects.

**Recovery**

- Continue on the CPU path if you only need the bundled training or inference
  workflows.
- If you truly need GPU acceleration, install a matching legacy CUDA 10.0 /
  cuDNN 7 stack and a compatible TensorFlow 1.15 GPU wheel in a separate
  environment.

## 4. Training or inference scripts cannot find data, vocab, or checkpoint files

**Symptom**

- `FileNotFoundError` or `OSError` for the input, target, vocabulary, checkpoint,
  model, or log directory.

**Likely cause**

- The legacy scripts relied on hard-coded directories that are not present in
  the current checkout.

**Recovery**

1. Use the bundled wrapper scripts and pass explicit paths.
2. Run the training smoke first so the inference workflow has a checkpoint to
   load.
3. Make sure the output directory exists before training.

## 5. The reader silently drops tokens

**Symptom**

- Sequences become shorter than expected or decode to empty text.

**Likely cause**

- A token does not exist in the vocabulary file, so `encode_text` drops it.

**Recovery**

- Add the missing token to the vocabulary.
- Keep `<s>` and `</s>` as the first two vocabulary entries.
- Rebuild the checkpoint if the vocabulary order changes.

## 6. Training appears to ignore part of the dataset

**Symptom**

- `SeqReader.data_size` is smaller than the number of examples on disk.
- The training loop only steps through a subset of the lines.

**Likely cause**

- The reader computes data size with integer division by batch size and drops
  any remainder.

**Recovery**

- Use a batch size that divides the number of aligned examples when you want a
  complete pass.
- Otherwise accept that the tail examples are ignored and adjust the dataset
  size accordingly.

## 7. The service returns `您的输入太长了`

**Symptom**

- The HTTP API or helper returns the fixed Chinese message instead of a couplet.

**Likely cause**

- The input is empty or longer than the service limit.

**Recovery**

- Use a non-empty input within the service length limit.
- If you need a different limit, adjust the bundled inference wrapper rather
  than editing the legacy source file directly.

## 8. A checkpoint restore fails during inference

**Symptom**

- `restore_model` or `reload_infer_model` raises an error about missing or
  incompatible variables.

**Likely cause**

- The checkpoint directory does not contain a compatible model, or the vocab or
  hidden-size configuration changed.

**Recovery**

- Recreate the checkpoint with the same vocabulary order and model size.
- Run the training smoke with the same settings before the inference smoke.

## 9. The legacy Flask module starts a server on import

**Symptom**

- Importing the service module blocks the session or starts a listener.

**Likely cause**

- The source file is a legacy script with top-level server startup logic.

**Recovery**

- Use the bundled inference wrapper and the `scripts/check_env.py` parser check
  instead of importing the legacy server module directly.
- When testing routes, use the bundled service helper that exposes a Flask app
  without starting the listener until you explicitly request it.

## 10. Sample outputs look noisy or repetitive

**Symptom**

- Beam-search results are technically valid but not good-looking.

**Likely cause**

- The model has not been trained enough, the checkpoint is tiny, or the input is
  outside the data distribution.

**Recovery**

- Train longer on a larger aligned dataset.
- Keep the tiny smoke fixtures only for verification, not for quality claims.

## When to stop and ask for more context

Stop and ask if:

- the dataset or checkpoint is missing and the user has not supplied a path,
- the user wants the legacy GPU path but the matching CUDA 10 stack is not
  available,
- a path or checkpoint mismatch suggests the user is trying to reuse a model
  trained with a different vocabulary.

Use the bundled check and smoke scripts before changing the source modules.
