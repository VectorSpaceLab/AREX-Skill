# TinyViT API Reference

## Purpose

Read this when you need the verified TinyViT variants, config keys, and output assumptions.

## Verified variants

From `models/tiny_vit.py`:

- `tiny_vit_5m_224(pretrained=False, **kwargs)`
- `tiny_vit_11m_224(pretrained=False, **kwargs)`
- `tiny_vit_21m_224(pretrained=False, **kwargs)`
- `tiny_vit_21m_384(pretrained=False, **kwargs)`
- `tiny_vit_21m_512(pretrained=False, **kwargs)`

The builder path is `models/build.py:build_model(config)` and supports:

- `MODEL.TYPE == 'tiny_vit'`
- `MODEL.TYPE == 'clip_vit_large14_224'`

## Verified config keys

The main `config.py` surface includes:

- `DATA.DATA_PATH`, `DATA.DATASET`, `DATA.IMG_SIZE`, `DATA.FNAME_FORMAT`, `DATA.DEBUG`
- `MODEL.TYPE`, `MODEL.NAME`, `MODEL.PRETRAINED`, `MODEL.RESUME`, `MODEL.NUM_CLASSES`, `MODEL.DROP_PATH_RATE`, `MODEL.LABEL_SMOOTHING`
- `MODEL.TINY_VIT.DEPTHS`, `NUM_HEADS`, `WINDOW_SIZES`, `EMBED_DIMS`, `MBCONV_EXPAND_RATIO`, `LOCAL_CONV_SIZE`
- `DISTILL.ENABLED`, `DISTILL.TEACHER_LOGITS_PATH`, `DISTILL.SAVE_TEACHER_LOGITS`, `DISTILL.LOGITS_TOPK`
- `TRAIN.EPOCHS`, `TRAIN.WARMUP_EPOCHS`, `TRAIN.ACCUMULATION_STEPS`, `TRAIN.USE_CHECKPOINT`, `TRAIN.LAYER_LR_DECAY`
- `AUG.MIXUP`, `AUG.CUTMIX`, `AUG.MIXUP_MODE`

## Notes from inspection

- `tiny_vit_5m_224` built successfully in the inspection environment.
- The observed head shape was `1000 x 320` for the 5M 224 model.
- The repo's tests check model loading, head replacement during finetuning, and a forward pass.

## What to avoid

Do not hard-code private checkpoint paths or local environment details.
Use model names and config keys only.
