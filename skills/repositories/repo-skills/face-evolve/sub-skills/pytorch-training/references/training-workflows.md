# PyTorch Training and Validation Workflows

This reference distills the PyTorch face.evoLVe training loop into safe operating steps. It is self-contained guidance for future agents; it is not a command to run full training automatically.

## When full training is appropriate

Run or repair full PyTorch training only when all of these are true:

1. The user has a face.evoLVe checkout they want to train from.
2. `DATA_ROOT/imgs/` contains ImageFolder-style identity folders (`identity_name/image.jpg`).
3. Any requested validation datasets are present as bcolz arrays plus matching `*_list.npy` files.
4. `MODEL_ROOT` and `LOG_ROOT` are writable.
5. The PyTorch source issues in [troubleshooting.md](troubleshooting.md) are fixed or explicitly bypassed.
6. For normal scale training, compatible CUDA devices are available and the config's `DEVICE`, `MULTI_GPU`, and `GPU_ID` values agree with that hardware.

Skip expensive full training when only component/API inspection is needed, when datasets/checkpoints are absent, when the task is just to choose a config, when the checkout still has the known `LOSS_DICT` syntax issue, or when the user has not approved long-running GPU work.

## End-to-end flow

### 1. Prepare data upstream

PyTorch training expects aligned identity images under `DATA_ROOT/imgs/` using `torchvision.datasets.ImageFolder` semantics:

```text
DATA_ROOT/
  imgs/
    person_a/
      0001.jpg
      ...
    person_b/
      0001.jpg
      ...
```

Use `face-alignment` for MTCNN alignment/cropping and `data-preparation` for identity-folder validation, class counts, low-shot pruning, and validation bcolz acquisition notes.

### 2. Edit the training configuration

Edit the active dictionary in `config.py`; see [configuration.md](configuration.md) for key-by-key rules. Common choices:

- `BACKBONE_NAME='IR_SE_50'`, `HEAD_NAME='ArcFace'`, `LOSS_NAME='Focal'` for the repo's model-zoo-style PyTorch face-recognition recipe.
- `INPUT_SIZE=[112, 112]` unless the data and validation preprocessing have been intentionally changed for `[224, 224]`.
- `BATCH_SIZE` large enough for stable BatchNorm during real training; use the largest value that fits the chosen GPU memory.
- `DROP_LAST=True` for real training so the final small batch does not destabilize BatchNorm statistics.
- `BACKBONE_RESUME_ROOT` and `HEAD_RESUME_ROOT` should point to actual checkpoint files when resuming. Use empty values for a clean scratch start if you do not want the script to probe placeholder paths.

### 3. Data loader and weighted sampling

The training loop builds:

- A transform chain: resize to `128 * input_size / 112`, random crop to `INPUT_SIZE`, random horizontal flip, tensor conversion, and normalization with `RGB_MEAN`/`RGB_STD` (defaults map pixels to approximately `[-1, 1]`).
- `torchvision.datasets.ImageFolder(DATA_ROOT/imgs, train_transform)`.
- Class-balancing weights with `make_weights_for_balanced_classes(dataset_train.imgs, len(dataset_train.classes))`.
- `torch.utils.data.sampler.WeightedRandomSampler(weights, len(weights))`.
- A `DataLoader` using `BATCH_SIZE`, `PIN_MEMORY`, `NUM_WORKERS`, and `DROP_LAST`.

For tiny synthetic training experiments, watch for two extra source assumptions: `DISP_FREQ = len(train_loader) // 100` can become zero, and `accuracy(..., topk=(1, 5))` fails when `NUM_CLASS < 5`. Repair those before attempting a tiny one-epoch training smoke.

### 4. Backbone, head, and loss construction

Stable training dictionaries are:

- Backbones: `ResNet_50`, `ResNet_101`, `ResNet_152`, `IR_50`, `IR_101`, `IR_152`, `IR_SE_50`, `IR_SE_101`, `IR_SE_152`.
- README-supported heads: `Softmax`, `ArcFace`, `CosFace`, `SphereFace`, `Am_softmax`. The checked training dictionary includes the margin heads but omits `Softmax`; add `Softmax` explicitly if `HEAD_NAME='Softmax'` is desired.
- Losses: `FocalLoss()` for `LOSS_NAME='Focal'`, or `torch.nn.CrossEntropyLoss()` for `LOSS_NAME='Softmax'`.

Margin heads transform embeddings plus labels into classification logits. The actual scalar objective is still `FocalLoss` or cross entropy applied to those logits and the same labels. Do not move margin-head classes into the loss dictionary.

### 5. Optimizer and schedule

The training loop uses SGD:

- Parameters are split so BatchNorm parameters receive no weight decay.
- For backbones whose name contains `IR`, use the IR/IR-SE parameter splitter; otherwise use the ResNet splitter.
- The optimizer has two groups: non-BatchNorm backbone/head parameters with `WEIGHT_DECAY`, and BatchNorm-only backbone parameters without explicit weight decay.
- Warm-up lasts `NUM_EPOCH // 25` epochs, with batch-wise linear LR increase.
- Each epoch listed in `STAGES` divides the learning rate by 10.

Advanced source backbones such as MobileFaceNet, GhostNet, ResidualAttentionNet, or EfficientNet-like code are not wired into the stable training dictionary. If a user chooses one, update the backbone dictionary, verify output shape, and re-check the parameter-splitting logic.

### 6. Resume behavior

Resume is attempted only if both `BACKBONE_RESUME_ROOT` and `HEAD_RESUME_ROOT` are truthy. The loop checks that both are files before loading:

- Backbone state is loaded before any `DataParallel` wrapping.
- Head state is loaded directly into the head module.
- Checkpoint names produced by training are time-stamped and include backbone/head name, epoch, and global batch count.

When a checkpoint mismatch occurs, compare backbone/head class, embedding size, class count, and whether the checkpoint was saved from a `DataParallel`-wrapped backbone. Feature-extraction-only tasks should route to `feature-extraction-verification`.

### 7. Multi-GPU behavior

When `MULTI_GPU=True`:

- The backbone is wrapped with `torch.nn.DataParallel(BACKBONE, device_ids=GPU_ID)` and moved to `DEVICE`.
- Margin heads implement their own model-parallel behavior when `device_id` is a list: class weights are chunked along the class dimension, work is spread across `GPU_ID`, and concatenated logits land on `GPU_ID[0]`.
- The head is not wrapped in `DataParallel` in the stable flow.
- Checkpoint saving uses `BACKBONE.module.state_dict()` for the backbone and `HEAD.state_dict()` for the head.

For CPU or single-device inspection, construct heads with `device_id=None` and do not set `MULTI_GPU=True`.

### 8. Validation during training

`get_val_data(DATA_ROOT)` expects all of these validation arrays under `DATA_ROOT`:

| Dataset key | Expected bcolz root | Expected issame file |
| --- | --- | --- |
| LFW | `lfw/` | `lfw_list.npy` |
| CFP frontal-frontal | `cfp_ff/` | `cfp_ff_list.npy` |
| CFP frontal-profile | `cfp_fp/` | `cfp_fp_list.npy` |
| AgeDB-30 | `agedb_30/` | `agedb_30_list.npy` |
| CALFW | `calfw/` | `calfw_list.npy` |
| CPLFW | `cplfw/` | `cplfw_list.npy` |
| VGGFace2-FP | `vgg2_fp/` | `vgg2_fp_list.npy` |

Validation uses `perform_val(...)`, switches the backbone to eval mode, center-crops to 112, optionally adds horizontal-flip test-time augmentation, L2-normalizes embeddings, and computes ROC/accuracy/best-threshold metrics. If the user supplies only a subset of validation datasets, repair the validation block to load and evaluate only that subset rather than letting the first missing bcolz root abort training.

### 9. Checkpoints and TensorBoard logs

Per epoch, training writes:

```text
Backbone_<BACKBONE_NAME>_Epoch_<epoch>_Batch_<batch>_Time_<timestamp>_checkpoint.pth
Head_<HEAD_NAME>_Epoch_<epoch>_Batch_<batch>_Time_<timestamp>_checkpoint.pth
```

TensorBoard scalars/images include training loss/accuracy and validation accuracy, threshold, and ROC curves for each validation dataset. Ensure `LOG_ROOT` exists and `tensorboardX` is installed before relying on logging.

## Safe bundled checks

Use the bundled component inspector before full training:

```bash
python skills/disco/face-evolve/sub-skills/pytorch-training/scripts/inspect_pytorch_components.py \
  --repo-root <face-evolve-repo> \
  --backbone IR_50 \
  --input-size 112 \
  --batch-size 2 \
  --inspect-heads
```

Expected safe signal on a healthy CPU-capable environment: the chosen backbone produces a tensor shaped `[batch_size, 512]`; stable heads report signatures and, when run with synthetic labels, produce logits shaped `[batch_size, num_classes]`.

Do not interpret this as evidence that full training is ready. It proves only import/signature/shape behavior for synthetic tensors.

## Full-training launch checklist

Before launching a real training run, verify:

- Data: `DATA_ROOT/imgs` has enough identities and images per identity for the requested batch size and `DROP_LAST` behavior.
- Validation: either all seven bcolz validation sets are present or the validation loop is repaired to a supplied subset.
- Source repairs: known `LOSS_DICT` syntax and `head.metrics` import issues are fixed if they affect the current run.
- Config: roots are writable; `DEVICE`, `MULTI_GPU`, and `GPU_ID` match actual hardware; checkpoint resume paths are deliberate.
- Runtime: PyTorch, torchvision, tensorboardX, bcolz, numpy, scipy, scikit-learn, PIL, matplotlib, and tqdm imports are compatible.
- Expense: the user accepts long-running training and GPU use.
