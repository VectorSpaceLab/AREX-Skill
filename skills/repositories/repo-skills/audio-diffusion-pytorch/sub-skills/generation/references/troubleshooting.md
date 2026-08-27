# Generation troubleshooting

Keep this page focused on waveform generator, text-conditioning, and inpainting problems. If the issue is really about upsampling, vocoding, or autoencoding, use `../conditioning/` instead.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Tiny smoke fails with a norm or divisibility error | `resnet_groups=8` does not divide small channel counts | Use `resnet_groups=1` for smoke configs or choose channel sizes divisible by 8. |
| Constructor complains about list lengths | `channels`, `factors`, `items`, `attentions`, `cross_attentions`, and `context_channels` must all have the same length | Make every list the same length before constructing `UNetV0`. |
| Text-conditioning import fails | `transformers` is not installed or not importable | Install `transformers`, or skip the optional text-constructor check. |
| Text-conditioning constructor wants a different embedding size | The default T5 text path expects `embedding_features=768` | Set `embedding_features=768` and keep the text-conditioning flags aligned. |
| `CrossAttentionItem requires channels, embedding_features, attention_*` | Cross-attention was enabled without attention dimensions | When any `cross_attentions` entry is nonzero, set `attention_heads` and `attention_features` too. |
| The text path seems slow or tries to use cache/network | The first T5 build can consult Hugging Face cache state | Treat the `--include-text-constructor` path as opt-in and avoid it when offline unless the model is already cached. |
| Inpainting throws a shape or type error | `mask` does not match `source`, or the mask is not boolean | Build `mask` with `torch.bool`, keep the same shape/device as `source`, and use `True` for the region you want to keep. |
| Sample or inpaint output is on the wrong device | Noise/source were created on a different device than the model | Keep model, source, noise, and mask on the same device. |
| Sampling quality looks unstable or strange | Too few steps or a custom schedule that runs the wrong direction | Use the default decreasing `LinearSchedule` and increase `num_steps` for real generation. |
| `DiffusionAR` asserts on length | `length` is not divisible by `num_splits` | Pick a divisible length or route the request to another workflow. |
| Illustrative large example tensors are expensive on CPU | The public usage examples use large shapes that are not the minimum smoke size | Use the bundled tiny smoke shapes for validation and reserve large shapes for real experiments. |
| You expected checkpoint guidance or a pretrained sample | This repo does not ship pretrained models or tested configs | Build your own small config or load your own weights; do not assume a blessed checkpoint is available. |
| The issue mentions `mel_sample_rate`, `audio_encoders_pytorch`, `auraloss`, or custom-loss tensors | That is an adjacent upsampling/vocoder/autoencoding workflow | Route to `../conditioning/` and use its troubleshooting notes. |

## Extra notes

- `VInpainter` treats `True` in the mask as keep-source and `False` as inpaint.
- `DiffusionModel.forward` is the training-loss route; `DiffusionModel.sample` is the sampler route.
- If you need a reproduction check, start from `scripts/tiny_generation_smoke.py` before trying a larger config.
