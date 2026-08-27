# PyTorch Model API Reference

This reference summarizes the PyTorch component APIs needed for face.evoLVe training and inspection. It distinguishes README-supported training components from additional source components that need extra repair and verification before use in real training.

## Stable README-supported backbones

All stable backbones accept `input_size` as `[112, 112]` or `[224, 224]` and produce 512-dimensional embeddings. For tiny synthetic checks, put the model in eval mode before forwarding small batches so BatchNorm uses running statistics.

| Name | Constructor | Source behavior | Training status |
| --- | --- | --- | --- |
| `ResNet_50` | `ResNet_50(input_size, **kwargs)` | ResNet bottleneck layers `[3, 4, 6, 3]`, final `Linear(..., 512)` and `BatchNorm1d(512)`. | Stable dictionary entry. |
| `ResNet_101` | `ResNet_101(input_size, **kwargs)` | ResNet bottleneck layers `[3, 4, 23, 3]`, final 512 embedding. | Stable dictionary entry. |
| `ResNet_152` | `ResNet_152(input_size, **kwargs)` | ResNet bottleneck layers `[3, 8, 36, 3]`, final 512 embedding. | Stable dictionary entry. |
| `IR_50` | `IR_50(input_size)` | IR bottleneck backbone with block layout for 50 layers, final 512 embedding. | Stable dictionary entry; CPU eval forward was verified to produce `[2, 512]`. |
| `IR_101` | `IR_101(input_size)` | Constructor maps to `num_layers=100` in source naming, final 512 embedding. | Stable dictionary entry. |
| `IR_152` | `IR_152(input_size)` | IR bottleneck backbone with 152-layer block layout, final 512 embedding. | Stable dictionary entry. |
| `IR_SE_50` | `IR_SE_50(input_size)` | IR backbone with squeeze-and-excitation modules, final 512 embedding. | Stable dictionary entry; recommended for ArcFace/Focal recipe. |
| `IR_SE_101` | `IR_SE_101(input_size)` | IR-SE backbone using source `num_layers=100`, final 512 embedding. | Stable dictionary entry. |
| `IR_SE_152` | `IR_SE_152(input_size)` | IR-SE backbone using 152-layer block layout, final 512 embedding. | Stable dictionary entry. |

Important shape details:

- For `[112, 112]`, IR/IR-SE final linear input is `512 * 7 * 7`; ResNet final linear input is `2048 * 4 * 4`.
- For `[224, 224]`, IR/IR-SE final linear input is `512 * 14 * 14`; ResNet final linear input is `2048 * 8 * 8`.
- Assertions check only the first `input_size` element, but use square values (`[112, 112]` or `[224, 224]`) to match transforms and output-layer assumptions.

## Advanced source backbones

These classes are present in the PyTorch backbone source tree but are not wired into the stable training dictionary. Use them only after explicit source edits, shape checks, and optimizer/parameter-split review.

| Component | Constructor/signature | Notes and risk |
| --- | --- | --- |
| `MobileFaceNet` | `MobileFaceNet(embedding_size, out_h, out_w)` | Lightweight mobile face backbone. For 112x112 inputs, `out_h=7`, `out_w=7` is the expected spatial size before the depthwise output layer. Not README-supported in the stable training table. |
| `GhostNet` | `GhostNet(width=1.0, drop_ratio=0.2, feat_dim=512, out_h=7, out_w=7)` | GhostNet-style lightweight backbone modified to emit `feat_dim` embeddings. For 112x112 inputs, use `out_h=7`, `out_w=7`; for 224x224, re-check spatial size before choosing `out_h/out_w`. |
| `ResidualAttentionNet` | `ResidualAttentionNet(stage1_modules, stage2_modules, stage3_modules, feat_dim, out_h, out_w)` | Residual Attention Network variant. Requires choosing stage module counts and output spatial dimensions; not a drop-in stable training option. |
| EfficientNet-like source | `EfficientNet(out_h, out_w, feat_dim, blocks_args=None, global_params=None)` appears in source | The file contains stray non-Python text that causes `SyntaxError` during import. Its `from_name`/`from_pretrained` classmethods also appear inconsistent with the modified constructor. Treat as repair-required, not stable. |

## Heads: stable README-supported classes

`device_id=None` means normal CPU/single-device behavior. A list such as `[0, 1, 2, 3]` activates source model-parallel head logic: class weights are split along the class dimension, per-device logits are computed, and concatenated logits are returned on the first listed GPU.

| Name | Constructor | Forward call | Output |
| --- | --- | --- | --- |
| `Softmax` | `Softmax(in_features, out_features, device_id)` | `head(x)` | Logits shaped `[batch, out_features]`. README-supported, but omitted from the checked training `HEAD_DICT`; add it if selected. On modern PyTorch, construction may also require replacing source `nn.init.zero_` with `nn.init.zeros_` or explicit bias zeroing. |
| `ArcFace` | `ArcFace(in_features, out_features, device_id, s=64.0, m=0.5, easy_margin=False)` | `head(features, labels)` | Margin-adjusted logits shaped `[batch, out_features]`. Recommended stable margin head. |
| `CosFace` | `CosFace(in_features, out_features, device_id, s=64.0, m=0.35)` | `head(features, labels)` | Cosine-margin logits. |
| `SphereFace` | `SphereFace(in_features, out_features, device_id, m=4)` | `head(features, labels)` | Angular-margin logits with internal iteration-dependent lambda. |
| `Am_softmax` | `Am_softmax(in_features, out_features, device_id, m=0.35, s=30.0)` | `head(features, labels)` | Additive-margin softmax logits. |

Training pattern for stable margin heads:

```python
features = BACKBONE(inputs)
logits = HEAD(features, labels)
loss = LOSS(logits, labels)
```

For `Softmax`, the forward call is `HEAD(features)` and the loss is ordinary cross entropy or focal loss over logits.

## Heads: extra experimental classes found in source

The source includes newer margin or prototype heads below the README-supported block. Normal import of the full head module can fail because several later classes inherit from `Module` without importing it. The bundled inspector patches `Module = torch.nn.Module` only in memory so signatures can be inspected; real training code should repair the source import or change those base classes to `nn.Module`.

| Name | Signature | Status |
| --- | --- | --- |
| `AdaCos` | `AdaCos(feat_dim, num_classes)` | Experimental source class; not in stable training dictionary. |
| `AM_Softmax` | `AM_Softmax(feat_dim, num_class, margin=0.35, scale=32)` | Experimental; requires `Module` repair. Note the checked training source references a misspelled `AdaM_Softmax`, not this class. |
| `ArcNegFace` | `ArcNegFace(feat_dim, num_class, margin=0.5, scale=64)` | Experimental; loops over batch entries and needs runtime testing before scale use. |
| `CircleLoss` | `CircleLoss(feat_dim, num_class, margin=0.25, gamma=256)` | Experimental; requires `Module` repair. The checked training source references `Circleloss`, a mismatched name. |
| `CurricularFace` | `CurricularFace(feat_dim, num_class, m=0.5, s=64.0)` | Experimental; uses an adaptive curriculum buffer. |
| `MagFace` | `MagFace(feat_dim, num_class, margin_am=0.0, scale=32, l_a=10, u_a=110, l_margin=0.45, u_margin=0.8, lamda=20)` | Experimental; returns `(logits, regularizer)` rather than logits only, so training loss code must change. |
| `MV_Softmax` | `MV_Softmax(feat_dim, num_class, is_am, margin=0.35, mv_weight=1.12, scale=32)` | Experimental; requires `Module` repair and an explicit `is_am` choice. The checked training source contains an invalid `MV_Softmax.py()` reference. |
| `NPCFace` | `NPCFace(feat_dim=512, num_class=86876, margin=0.5, scale=64)` | Experimental; source forward path hard-codes CUDA use in at least one mask creation, so CPU training is not safe without repair. |
| `SST_Prototype` | `SST_Prototype(feat_dim=512, queue_size=16384, scale=30.0, loss_type='softmax', margin=0.0)` | Experimental prototype/queue head; forward signature is not the standard `(features, labels)` pattern and source needs a `random` import repair. |

Do not add experimental heads to a production training recipe until their import, forward signature, return type, device behavior, and objective integration have all been tested on a tiny fixture.

## Loss functions

| Name in config | Constructor | Forward | Notes |
| --- | --- | --- | --- |
| `Focal` | `FocalLoss(gamma=2, eps=1e-7)` | `loss(logits, labels)` | Wraps `torch.nn.CrossEntropyLoss`; scales CE by `(1 - p) ** gamma`. Stable README-supported loss. |
| `Softmax` | `torch.nn.CrossEntropyLoss()` | `loss(logits, labels)` | Ordinary cross entropy over logits. Stable README-supported loss value. |

Margin heads are not loss functions in this training loop. They are classification heads that produce logits; `FocalLoss` or cross entropy consumes those logits.

## Utility APIs used by training

| Utility | Signature | Use |
| --- | --- | --- |
| `make_weights_for_balanced_classes` | `make_weights_for_balanced_classes(images, nclasses)` | Computes per-image sampler weights from `ImageFolder.imgs` and class count. |
| `get_val_data` | `get_val_data(data_path)` | Loads seven bcolz validation arrays and seven `*_list.npy` files from `DATA_ROOT`. |
| `separate_irse_bn_paras` | `separate_irse_bn_paras(modules)` | Splits BatchNorm parameters from non-BatchNorm for IR/IR-SE style modules. |
| `separate_resnet_bn_paras` | `separate_resnet_bn_paras(modules)` | Splits parameters by names containing `bn` for ResNet modules. |
| `warm_up_lr` | `warm_up_lr(batch, num_batch_warm_up, init_lr, optimizer)` | Batch-wise linear warm-up. |
| `schedule_lr` | `schedule_lr(optimizer)` | Divides all optimizer group learning rates by 10. |
| `perform_val` | `perform_val(multi_gpu, device, embedding_size, batch_size, backbone, carray, issame, nrof_folds=10, tta=True)` | Eval-mode feature extraction with center crop, optional flip TTA, L2 normalization, and ROC/accuracy calculation. |
| `buffer_val` | `buffer_val(writer, db_name, acc, best_threshold, roc_curve_tensor, epoch)` | Writes validation scalar and ROC image summaries. |
| `accuracy` | `accuracy(output, target, topk=(1,))` | Computes top-k accuracy; tiny class-count runs must not request `top5` if fewer than five classes exist. |

## Safe inspection expectations

A minimal component smoke should avoid the training entrypoint and do only:

1. Import selected backbone/head/loss modules.
2. Construct the selected backbone in eval mode.
3. Forward a random tensor shaped `[batch_size, 3, H, W]`.
4. Assert the embedding shape is `[batch_size, 512]` for stable backbones.
5. If inspecting heads, construct stable heads with `device_id=None`, run synthetic labels, and assert logits shape `[batch_size, num_classes]`.

Use the bundled `inspect_pytorch_components.py` script for this check.
