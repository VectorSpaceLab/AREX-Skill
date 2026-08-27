# Encoder Reference

`extract_features_fp.py` supports exactly these `--model_name` choices: `resnet50_trunc`, `uni_v1`, and `conch_v1`. The model builder also contains code for other encoders, but they are not accepted by the feature-extraction CLI covered by this sub-skill.

## Encoder Matrix

| `--model_name` | Checkpoint/package requirements | Normalization | Feature dimension | Notes |
| --- | --- | --- | --- | --- |
| `resnet50_trunc` | No user checkpoint variable required | ImageNet mean/std | `1024` | Default CLAM encoder; generally lower GPU memory than UNI/CONCH. |
| `uni_v1` | `UNI_CKPT_PATH` must point to the downloaded UNI `pytorch_model.bin` | ImageNet mean/std | `1024` | Uses a ViT-L model through `timm`; expect longer runtimes and smaller safe batch sizes. |
| `conch_v1` | CONCH package must be installed and `CONCH_CKPT_PATH` must point to the downloaded checkpoint | OpenAI CLIP mean/std | `512` | Uses CONCH image encoding; downstream CLAM commands must use `--embed_dim 512`. |

## Checkpoint Environment Variables

Set checkpoint variables in the shell before running CLAM feature extraction:

```bash
export UNI_CKPT_PATH="<uni-checkpoint>/pytorch_model.bin"
export CONCH_CKPT_PATH="<conch-checkpoint>/pytorch_model.bin"
```

Only set the variable needed for the selected encoder. The feature command loads checkpoints at runtime; the bundled command builder only checks whether the relevant variable is present and never reads checkpoint files.

## Target Patch Size

`--target_patch_size` is passed to CLAM image transforms. The current fast workflow defaults to `224`, resizing image patches before encoder inference. If preserving another patch size is intentional, set `--target_patch_size` explicitly and keep the same setting when comparing feature sets. For UNI and CONCH, `224` is the documented default used by the CLAM feature CLI.

## Downstream `embed_dim` Alignment

Match every training, evaluation, and heatmap model configuration to the feature dimension:

- ResNet50 truncation features: `--embed_dim 1024`.
- UNI features: `--embed_dim 1024`.
- CONCH features: `--embed_dim 512`.

A training or evaluation shape mismatch soon after loading a feature bag usually means the `.pt` features were extracted with a different encoder than the model's `embed_dim` setting.

## Encoder Selection Guidance

- Choose `resnet50_trunc` for the simplest baseline or when no external checkpoint access is available.
- Choose `uni_v1` when the user has UNI access, wants UNI representations, and can handle larger GPU memory usage.
- Choose `conch_v1` when the user has CONCH installed and needs CONCH representations; immediately propagate `embed_dim=512` to downstream commands.
