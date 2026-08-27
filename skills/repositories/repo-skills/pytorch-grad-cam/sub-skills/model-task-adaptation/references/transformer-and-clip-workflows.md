# Transformer and CLIP Workflows

## ViT

Typical DeiT/ViT activations are `B x (1 + patches) x C`: the first token is a
class token, and the remaining tokens form a square patch grid. Remove the class
token, reshape patches to `H x W`, then transpose to `B x C x H x W`.

Choose a layer before the final attention/head operation, such as a final block
normalization layer whose patch tokens still influence the classification score.
The common starting point is conceptually `model.blocks[-1].norm1`; adapt the
layer name to the actual model implementation.

## SwinT

Swin activations commonly have `B x (H*W) x C` tokens without a class token.
Reshape to `B x H x W x C` and transpose. For a 224-pixel model with 7x7 final
windows, the grid is often 7x7, but derive it from the actual activation shape.
A common target is the final block normalization layer before the head.

The optional `timm` dependency is not installed by `grad-cam`; install it only
when the user's model construction needs it. Avoid running a pretrained model
constructor until the user accepts network/model-cache requirements.

## CLIP and prompt explanations

A CLIP workflow wraps image/text scoring in a model whose `forward` returns one
logit/probability per prompt. The wrapper should:

1. Tokenize the user-provided labels/prompts.
2. Run the CLIP image and text encoders.
3. Return image-to-prompt logits or probabilities as a tensor shaped like
   classifier logits.
4. Target the prompt index with `ClassifierOutputTarget` or use `targets=None`.
5. Provide a ViT-style reshape transform for the CLIP vision encoder layer.

The optional `transformers` dependency and the model checkpoint are external to
`grad-cam`. Report missing `transformers`, missing model cache, authentication,
network, and device errors distinctly.

## HuggingFace image models

For a HuggingFace vision model, wrap the model if its output is a dataclass or
dict so that CAM sees a tensor of logits. Keep preprocessing normalization
consistent with the model's image processor. Target a class logit or custom
scalar and use a reshape transform for token activations.

## No-download validation

Run:

```bash
python sub-skills/model-task-adaptation/scripts/validate_reshape_transform.py --kind vit
python sub-skills/model-task-adaptation/scripts/validate_reshape_transform.py --kind swin --height 7 --width 7
```

These commands validate tensor layout only; they do not claim that a specific
external checkpoint or model wrapper is available.
