# Model-based metric troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `BERTScore` or `InfoLM` tries to download a Transformer model | The default pretrained model is not cached locally | Use a local checkpoint path, prefetch the model, or choose a non-model metric route if downloads are not allowed. |
| `CLIPScore` or `CLIP-IQA` fails during model initialization | The CLIP model or the optional `piq` dependency is missing | Install the route-specific extra and verify the model name or path. |
| FID/KID/LPIPS/DISTS/ARNIQA/Perceptual Path Length fails to import | `torchvision` or `torch_fidelity` is missing, or the installed extras do not match the chosen metric | Install the image/model extra for the chosen metric family and retry the import check. |
| `DNSMOS` or `NISQA` complains about `librosa`, `onnxruntime`, or `requests` | Audio model-backed metric dependencies are missing | Install the audio extra or the exact package named in the error, then rerun the import check. |
| `VideoMultiMethodAssessmentFusion` import fails | `vmaf_torch` is missing | Install the video extra or the missing package, then rerun the import check. |
| A model-backed metric is slow or memory-heavy | The pretrained backbone and batch size are too large for the environment | Lower the batch size, move the metric to a larger device, or choose an alternate metric with lighter dependencies. |
| `feature` or `model_name_or_path` seems wrong | The metric expects a specific backbone, model id, or feature dimensionality | Check the constructor signature and the metric docs before instantiating the model. |
| A no-download smoke check passes but runtime scoring still fails | The model assets are not cached or a downstream download is blocked | Treat import-only checks as API verification only, not full model execution proof. |
| A simple text or image metric is being routed here | The request does not actually need a pretrained model | Route to `../audio-text-metrics/` or `../vision-detection-metrics/` instead. |
