# Model enrichment troubleshooting

- If `torch`, `timm`, `transformers`, `paddlepaddle`, `paddleocr`, `groundingdino`, or `segment_anything` is missing, the matching helper is unavailable.
- `recognize-anything-model` and `tag2text` depend on the Torch-based caption stack; `grounding-dino` and `segment-anything` depend on their own model stacks.
- If a model helper downloads weights, run it on a tiny subset first.
- `fd.enrich(...)` can run on a dataframe directly, but `fd.caption(...)` still requires a prior `fd.run()`.
- If search or embedding code fails with a width mismatch, check the feature dimension `d` and reuse a vector from the same run as the smoke query.
- `init_search` must be called before `search` or `vector_search`, and `vector_search` only works on vectors with the same width as the indexed space.
- If the helper picks the wrong device, pass the device explicitly and verify the target backend before scaling up.
- TensorBoard projector output requires TensorFlow; if it is not installed, keep that workflow documented rather than claiming it is runnable.
