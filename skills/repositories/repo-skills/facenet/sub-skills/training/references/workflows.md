# Facenet training workflows

## Softmax training

`train_softmax.py` is the main classifier-style training script.

Command shape:

```bash
python -m train_softmax \
  --data_dir ALIGNED_DATASET \
  --model_def models.inception_resnet_v1 \
  --logs_base_dir LOGS_DIR \
  --models_base_dir MODELS_DIR \
  --batch_size 90 \
  --image_size 160 \
  --max_nrof_epochs 500
```

Important options:

- `--pretrained_model`: restore a starting checkpoint before training.
- `--center_loss_factor` and `--center_loss_alfa`: enable center loss.
- `--prelogits_norm_loss_factor`: regularize the prelogits norm.
- `--validation_set_split_ratio`: split the dataset into training/validation images.
- `--lfw_dir` and `--lfw_pairs`: run LFW evaluation after each validation epoch.
- `--use_fixed_image_standardization`: use the fixed normalization needed by newer pretrained models.

`train_softmax.py` samples images through a queue-based pipeline, so batch size, preprocess threads, and image size must be compatible with the available memory.

## Triplet-loss training

`train_tripletloss.py` learns embeddings with anchor/positive/negative triplets.

Command shape:

```bash
python -m train_tripletloss \
  --data_dir ALIGNED_DATASET \
  --model_def models.inception_resnet_v1 \
  --logs_base_dir LOGS_DIR \
  --models_base_dir MODELS_DIR \
  --people_per_batch 45 \
  --images_per_person 40 \
  --batch_size 90 \
  --epoch_size 1000 \
  --max_nrof_epochs 500
```

Important workflow facts:

- The script samples `people_per_batch * images_per_person` examples, computes embeddings, then mines triplets where the negative violates the margin.
- Training uses `alpha` as the positive/negative distance margin.
- `batch_size` should be divisible by 3 because the training graph reshapes embeddings into anchor/positive/negative triplets.
- The script can also evaluate on LFW when `--lfw_dir` is provided.

## Model definitions

The `model_def` argument names a module in `src/models/` that exports `inference(...)`:

- `models.inception_resnet_v1`
- `models.inception_resnet_v2`
- `models.squeezenet`
- `models.dummy` for tests only

All three real models expose `bottleneck_layer_size`, `weight_decay`, `phase_train`, and `reuse` arguments. The dummy model is only a simplified bottleneck layer used in tests.

## Outputs

Training writes run-specific directories under the selected log/model roots, with subdirectories named by timestamp. The scripts also write revision metadata and may save `lfw_result.txt` or `stat.h5`.

## Safe usage pattern

1. Validate dataset layout and alignment first.
2. Select a model definition and image size.
3. Build the command with the helper script.
4. Start with a very small epoch size or synthetic fixture only when debugging control flow.
5. Use the source tests as guidance for command structure, not as a replacement for full training datasets.
