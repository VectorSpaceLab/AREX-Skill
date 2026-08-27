# Workflows

## Image classification
```bash
python skills/disco/paddlecv/scripts/run_predict.py \
  --config paddlecv/configs/single_op/PP-HGNet.yml \
  --input paddlecv/demo/ILSVRC2012_val_00020010.jpeg
```

## Object detection
```bash
python skills/disco/paddlecv/scripts/run_predict.py \
  --config paddlecv/configs/single_op/PP-YOLOE+.yml \
  --input paddlecv/demo/000000014439.jpg \
  -o MODEL.0.DetectionOp.PostProcess.0.ParserDetResults.threshold=0.6
```

## Segmentation
```bash
python skills/disco/paddlecv/scripts/run_predict.py \
  --config paddlecv/configs/single_op/PP-HumanSegV2.yml \
  --input paddlecv/demo/pp_humansegv2_demo.jpg
```

## Feature extraction / keypoint
- Use the matching `paddlecv/configs/unittest/test_feature_extraction.yml` or `paddlecv/configs/unittest/test_keypoint.yml` when you need a smaller behavior-checking config.
- These routes are useful when the user is debugging postprocess output names or batched image inputs.

## Model selection workflow
1. Start with `PaddleCV.list_all_supported_models([...])` or `list_model([...])`.
2. Choose the smallest preset that matches the requested family.
3. Switch to a custom config only if the user needs a different threshold, batch size, or output layout.
