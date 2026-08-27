# Inference Troubleshooting

## Purpose

Use this reference for checkpoint loading, offline prediction, and HTTP service
issues.

## Checkpoint load fails

**Symptoms**

- TensorFlow restore errors.
- Missing `model.ckpl` files.
- Shape mismatch errors during inference graph restore.

**Likely causes**

- The checkpoint was not created by the same model size.
- The vocab file changed after training.
- The checkpoint directory is empty or points at logs rather than checkpoint
  files.

**Recovery**

- Use the same `num_units`, `layers`, and vocabulary order that were used for
  training.
- Run the training smoke and then the serving smoke to confirm the complete
  path.
- Recreate the checkpoint if the vocabulary changed.

## Offline inference returns the fixed length message

**Symptoms**

- Output is `您的输入太长了`.

**Likely causes**

- The input string is empty or exceeds the configured service length limit.

**Recovery**

- Use a non-empty input below the limit.
- For controlled deployments, pass a different `--max-input-length` value to
  the bundled scripts.

## Service starts but candidates look poor

**Likely causes**

- The checkpoint is a tiny smoke checkpoint or under-trained model.
- The input is outside the model's training distribution.
- The vocab is too small or silently drops characters.

**Recovery**

- Use a real trained checkpoint for quality evaluation.
- Treat smoke output as a mechanics check only.
- Verify the vocab covers the input characters.

## Censor-word behavior is surprising

**Likely causes**

- The censor-word file contains broad substrings that penalize many outputs.
- No censor-word file was supplied, so censor penalties are skipped.

**Recovery**

- Inspect the censor-word list and test with `scripts/infer_couplet.py`.
- Run the HTTP smoke without a censor file first, then add the file once the
  service mechanics pass.

## Server tests hang

**Likely cause**

- The legacy source server was imported directly and started its WSGI loop.

**Recovery**

- Use `scripts/serve_smoke.py` for route tests. It builds an app and uses a
  Flask test client without starting a network listener.
- Use `scripts/serve_couplet.py --dry-run` before starting the listener.

## Dependency import fails

For TensorFlow/protobuf, gevent, Flask, or legacy CUDA warnings, read the root
`../../references/troubleshooting.md` file first. Those are environment issues,
not inference-route issues.
