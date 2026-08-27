# Facenet model files and checkpoints

## Accepted model path forms

Most Facenet workflows accept either:

- a checkpoint directory containing a `.meta` file plus checkpoint state/files; or
- a frozen GraphDef `.pb` file.

`facenet.load_model()` distinguishes these cases by checking whether the supplied path is a file.

## Checkpoint selection

`facenet.get_model_filenames(model_dir)` behaves as follows:

1. Look for exactly one `.meta` file.
2. Use checkpoint state if `tf.train.get_checkpoint_state(model_dir)` points at a checkpoint.
3. Otherwise scan for `model-*.ckpt-*` files and choose the highest step number.

If there are zero `.meta` files or more than one `.meta` file, the function raises `ValueError`.

## Tensor names

Most core workflows assume these graph tensors exist:

- `input:0`
- `embeddings:0`
- `phase_train:0`
- `label_batch` in training/export paths

If a model was exported or frozen with different names, downstream scripts may fail even though the checkpoint loads.

## Freeze graph output

`freeze_graph.py` restores the model, rewrites some ref/assign ops for freezing compatibility, and exports constants for `embeddings` and `label_batch`. The script prints the number of ops in the final graph.

## Inspection helper

Use `scripts/inspect_model_dir.py MODEL_DIR` to summarize `.meta`, checkpoint-state, and candidate checkpoint files before choosing a load or freeze workflow.
