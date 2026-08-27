# Server Runtime API Reference

## Main CLI module

`python -m clip_server` loads a Jina `Flow` from one of three sources:

1. No argument: built-in `torch-flow.yml`.
2. One argument: the supplied YAML path or package resource name.
3. `-i`: YAML read from standard input.

The module loads the Flow with the package resource directory in `extra_search_paths`, which is why packaged names such as `onnx-flow.yml` can resolve after installation.

## Executor classes

### PyTorch executor

Verified constructor shape:

```text
clip_server.executors.clip_torch.CLIPEncoder(
  name='ViT-B-32::openai',
  device=None,
  jit=False,
  num_worker_preprocess=4,
  minibatch_size=32,
  access_paths='@r',
  dtype=None,
  **kwargs
)
```

Behavior facts:

- If `device` is omitted, CUDA is selected when `torch.cuda.is_available()` is true, otherwise CPU.
- If `dtype` is omitted, CPU uses `torch.float32`; non-CPU uses `torch.float16`.
- `traversal_paths` in kwargs is deprecated and maps to `access_paths` with a warning.
- Text and image docs are separated before model inference.
- `/rank` first calls encode on roots and matches, then computes CLIP ranking scores.

### ONNX executor

Constructor shape from source:

```text
clip_server.executors.clip_onnx.CLIPEncoder(
  name='ViT-B-32::openai',
  device=None,
  num_worker_preprocess=4,
  minibatch_size=32,
  access_paths='@r',
  model_path=None,
  dtype=None,
  **kwargs
)
```

Behavior facts:

- Requires `onnxruntime` import.
- Defaults to `fp32` on CPU and `fp16` on CUDA.
- `model_path` must be a directory with `textual.onnx` and `visual.onnx`.
- ONNX sessions are created with `ORT_ENABLE_ALL` graph optimizations and provider priority `CUDAExecutionProvider` then `CPUExecutionProvider` when CUDA is selected.

### TensorRT executor

Constructor shape from source:

```text
clip_server.executors.clip_tensorrt.CLIPEncoder(
  name='ViT-B-32::openai',
  device='cuda',
  num_worker_preprocess=4,
  minibatch_size=32,
  access_paths='@r',
  **kwargs
)
```

Behavior facts:

- Importing the TensorRT model path raises a clear ImportError if `tensorrt` is missing.
- `device` must start with `cuda` and `torch.cuda.is_available()` must be true.
- Engines are built from ONNX assets when cached TensorRT engines are absent.
- Engine build uses large dynamic-shape optimization profiles; it can fail from memory or unsupported model/runtime combinations.

## Helper functions that affect behavior

| Function | Verified signature/role | Important behavior |
| --- | --- | --- |
| `numpy_softmax(x, axis=-1)` | NumPy softmax helper | Used to normalize ranking logits. |
| `split_img_txt_da(doc, img_da, txt_da)` | Mutates image/text DocumentArray buckets | `.text` wins over URI/blob/tensor; otherwise image docs include `.blob`, `.tensor`, or `.uri`. |
| `preproc_image(da, preprocess_fn, device='cpu', return_np=False, drop_image_content=False, dtype=torch.float32)` | Converts images to tensor batch | Loads URI/blob as needed, can drop image content before return. |
| `preproc_text(da, tokenizer, device='cpu', return_np=False)` | Tokenizes text into `input_ids` and `attention_mask` | Sets text mime type and can return NumPy arrays for ONNX. |
| `set_rank(docs, _logit_scale=exp(4.60517))` | Scores and sorts matches | Adds `clip_score` (softmax) and `clip_score_cosine`, clears match embeddings, sorts descending. |

## Tokenizer behavior

Verified call signature:

```text
Tokenizer.__call__(texts, context_length=77, truncate=True)
```

- Default OpenCLIP/OpenAI-style tokenization uses a BPE vocabulary bundled in package resources and context length 77.
- M-CLIP names use a Hugging Face tokenizer and require `transformers`.
- CN-CLIP names use `cn_clip` and context length 52.
- If a default text is too long and `truncate=False`, tokenization raises instead of truncating.

## Model downloader behavior

`download_model(url, target_folder='~/.cache/clip', md5sum=None, with_resume=True, max_attempts=3)` downloads model artifacts with resume support and optional MD5 validation. It writes a `.part` file during download and moves it into place only after validation. Treat corrupt cache, network failure, and wrong MD5 as operational issues, not model API behavior.
