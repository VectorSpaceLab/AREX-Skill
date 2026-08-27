# Chat and Demo Troubleshooting

## Missing or incorrect model files

- **Symptom:** `from_pretrained` cannot resolve files, hangs on download, or
  loads a tokenizer that does not match the model.
- **Likely cause:** no Hub access/cache, incomplete Git LFS checkout, or a
  tokenizer/model path mismatch.
- **Recovery:** use one complete local model directory for both calls, verify
  the model's config/tokenizer files, optionally pin a known revision, and run
  the bundled environment checker with `--model-path`. Do not package weights
  inside the skill.

## Remote-code or revision errors

- **Symptom:** unknown model class or an attribute missing from `chat`/
  `stream_chat`.
- **Likely cause:** `trust_remote_code=True` was omitted or a moving model
  revision changed the implementation.
- **Recovery:** add the flag, pin a compatible revision, and keep tokenizer and
  model revisions aligned. Do not mix ChatGLM-6B and ChatGLM2-6B checkpoints.

## CUDA out of memory

- **Symptom:** failure during model load, the first generation, or a long
  conversation.
- **Likely cause:** FP16/BF16 model/context/KV cache exceeds VRAM, another
  process occupies the GPU, or PyTorch is too old to use the efficient
  attention path.
- **Recovery:** inspect free memory, shorten `max_length`, use a supported
  INT4/INT8 model, reduce batch/concurrency, or use the multi-GPU route. A
  PyTorch version below 2.0 may fall back to a more memory-hungry attention
  implementation. Do not claim a CPU import proves CUDA capacity.

## Gradio `.style()` failure

- **Symptom:** `Textbox` has no attribute `style` during demo import.
- **Likely cause:** a modern Gradio release removed the legacy method.
- **Recovery:** use the tested legacy range (`gradio==3.50.2`) or adapt the
  source UI to the current constructor API. Do not blindly downgrade unrelated
  packages; run `pip check` afterward.

## Streamlit or UI startup problems

- **Symptom:** nothing opens, session state resets, or a port is already in
  use.
- **Recovery:** launch through `streamlit run`, check the printed local URL,
  choose a free port, and confirm model initialization completes before
  debugging widgets. Keep the app bound to localhost unless authentication and
  network policy are handled elsewhere.

## CPU, OpenMP, and MPS

- **Symptom:** CPU quantization reports `-fopenmp`/OpenMP errors or Mac MPS
  cannot load the model.
- **Recovery:** install a platform-supported OpenMP/compiler runtime; on Mac
  follow the documented OpenMP instructions only after reviewing their system
  effects. For MPS, use a local model path and a compatible PyTorch build. The
  CUDA INT4 kernel is not a valid MPS fallback.

## Multi-GPU device mismatch

- **Symptom:** an embedding/input tensor and the model's input device differ,
  or an encoder layer is dispatched to a missing GPU.
- **Recovery:** run `inspect_device_map.py --num-gpus N`, ensure `N` matches
  `torch.cuda.device_count()`, keep embeddings/final layer norm/output layer on
  the first device as the repository helper does, and inspect actual module
  names before passing a custom map.
