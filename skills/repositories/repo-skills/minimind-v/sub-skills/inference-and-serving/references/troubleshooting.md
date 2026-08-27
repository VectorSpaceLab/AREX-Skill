# Inference and WebUI Troubleshooting

## Wrong checkpoint mode

Symptom: a Transformers checkpoint path is treated like native `.pth` mode. Cause: mode selection checks whether `--load_from` contains substring `model`.

Recovery: use a Transformers path without `model` in its directory name, or use native mode intentionally with `--load_from model`.

## Missing native weight

Symptom: expected file such as `out/sft_vlm_768.pth` is absent.

Recovery: match `--weight`, `--hidden_size`, and `--use_moe`; `_moe` filenames require `--use_moe 1`. Use the preflight helper before generation.

## Missing SigLIP2

Symptom: processor/vision encoder is `None` or image tensor conversion fails.

Recovery: route setup to `data-and-resources`; the inference path needs `model/siglip2-base-p32-256-ve/` unless user code is adapted.

## WebUI finds no models

Cause: scanner only checks immediate child directories with `.bin`, `.safetensors`, or `model.safetensors.index.json`. It ignores the base directory itself and nested grandchildren.

Recovery: place each Transformers model under a direct child of the WebUI scan base and run `scan_transformers_models.py`.

## CUDA OOM or slow CPU

Reduce `--max_new_tokens`, use fewer images, choose CPU for file-path smoke, or confirm GPU memory before CUDA. Do not use generation as a default diagnostic.

## Untrusted custom code

Transformers mode and WebUI commonly use `trust_remote_code=True`. Static-inspect exports first and ask the user whether they trust the checkpoint/source before loading.
