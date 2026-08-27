# Evaluation workflows

## Standalone LFW validation

The standalone evaluator loads a model, computes embeddings for all image pairs, and reports verification metrics.

Command shape:

```bash
python -m validate_on_lfw LFW_ALIGNED_DIR MODEL \
  --lfw_pairs pairs.txt \
  --lfw_batch_size 100 \
  --lfw_nrof_folds 10 \
  --distance_metric 0 \
  --use_fixed_image_standardization
```

Key implementation facts:

- Pairs are read with `lfw.read_pairs()` and resolved with `lfw.get_paths()`.
- Images are enqueued through `facenet.create_input_pipeline()`.
- `facenet.load_model()` receives an input map so the loaded graph uses evaluator image/label queues.
- The script asserts the number of images is an integer multiple of `--lfw_batch_size`.
- With `--use_flipped_images`, the evaluator concatenates embeddings from original and horizontally flipped images.

## Training-time LFW evaluation

Both `train_softmax.py` and `train_tripletloss.py` can evaluate on LFW during training when `--lfw_dir` is provided. They call `lfw.evaluate()` after computing embeddings. Keep the pair file and batch-size constraints consistent with standalone validation.

## Reading outputs

Standalone validation prints:

- `Accuracy: mean+-std`
- `Validation rate: val+-std @ FAR=...`
- `Area Under Curve (AUC)`
- `Equal Error Rate (EER)`

Training scripts write summaries and append compact LFW results to `lfw_result.txt` in the log directory. The Matlab plotting utility in the source tree reads training log HDF5/stat files, but it is not a portable bundled workflow.

## Bounded verification

Use pair validation and parser/help checks by default. Run full LFW only when the user supplies aligned images and a model, because public LFW/model acquisition can be networked and benchmark-scale.
