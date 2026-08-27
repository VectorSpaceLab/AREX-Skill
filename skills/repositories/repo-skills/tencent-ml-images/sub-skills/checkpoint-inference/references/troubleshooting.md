# Checkpoint Inference Troubleshooting

Use this when a checkpoint-backed classification or feature-extraction task
fails.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `FileNotFoundError` or restore failure on the checkpoint | The path points to a directory without TensorFlow checkpoint shards, or the prefix is wrong | Point the inspector at the checkpoint prefix and confirm that `.index`/`.data-*` files exist |
| `cv2` import missing | OpenCV is not installed in the inspection runtime | Install `opencv-python-headless` or a compatible OpenCV package in the target environment before using the bundled inspectors |
| `imread` returns `None` or an unreadable image | The image list contains missing or corrupt files | Fix the image list or replace the image before running inference |
| `top_k` greater than class count | The caller asked for more classes than the checkpoint/dictionary supports | Lower `--top-k` or use the correct `class_num` and dictionary/checkpoint pair |
| Dictionary names look wrong | The dictionary file is not the ImageNet 2012 mapping the source code expects | Use the project's `imagenet2012_dictionary.txt` or a compatible replacement with zero-based ids |
| Output file is empty | The image list is empty, unreadable, or the process exited before writing | Validate the list with the bundled inspector first; verify the output path is writable |
| Restore succeeds but predictions are nonsense | The checkpoint, class count, and dictionary do not belong together | Match the checkpoint family to the intended workflow: `1000`-class ImageNet classification or ML-Images-pretrained feature extraction |
| `SyntaxError: from __future__ imports must occur at the beginning of the file` in the original scripts | The source checkout still has the legacy import placement issue | Patch the checkout before direct execution or rely on the bundled inspectors plus a patched script run |

## Safe validation order

1. Validate the image list and dictionary with the bundled inspector.
2. Confirm the checkpoint prefix contains TensorFlow checkpoint shards.
3. Ensure OpenCV imports in the target runtime.
4. Run the printed command.
5. Only then inspect the resulting predictions or feature file.

## When not to proceed

Do not try to restore a checkpoint when the dataset, dictionary, or runtime is
not ready. The failure is usually in the inputs, not the model itself.
