# Model export and checkpoint troubleshooting

## No `.meta` file

`facenet.get_model_filenames()` requires exactly one `.meta` file in the model directory. If there are none, the directory is incomplete. If there are multiple, pick the correct training run or clean the directory.

## Checkpoint state missing or stale

If `tf.train.get_checkpoint_state()` cannot resolve the checkpoint, `get_model_filenames()` falls back to the highest-step `model-*.ckpt-*` file. Make sure the checkpoint files and the `checkpoint` state file stay together.

## Frozen graph tensor missing

If downstream scripts cannot find `input:0`, `embeddings:0`, or `phase_train:0`, the model was frozen with different names or a different output signature. Re-freeze with the Facenet export script or adapt the consumer to the actual tensor names.

## `freeze_graph.py` fails on restore

Common causes:

- the model directory does not contain the expected checkpoint pair;
- the `.meta` graph is from a different branch or architecture;
- the environment is missing TensorFlow 1.x APIs.

## `.pb` vs checkpoint confusion

A `.pb` file is already a frozen graph and should be passed directly to `facenet.load_model()`. A checkpoint directory must contain graph and weight files. Do not point checkpoint-only workflows at a `.pb` file unless the consumer explicitly supports it.
