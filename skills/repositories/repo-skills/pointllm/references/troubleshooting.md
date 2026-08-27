# Cross-cutting troubleshooting

Read this reference when the failure spans installation, package imports,
CUDA, or multiple PointLLM routes. Start with the bundled read-only diagnostic:

```bash
python skills/disco/pointllm/scripts/check_env.py
python -m pip check
```

## Import and dependency failures

- `No module named pointllm`: install the distribution in the environment that
  will execute the route, or use the environment's documented package path. Do
  not mix the DisCo Python with a separate training environment.
- `No module named torch.utils._sympy...`, missing `pkg_resources`, or a
  Transformers LLaMA import failure usually means a legacy PointLLM stack was
  combined with a newer Deepspeed/Setuptools release. Recreate an isolated
  Python 3.10 environment and follow the tested torch/Transformers versions;
  do not patch random package files.
- `tokenizers` or Transformers ABI/version errors mean the pinned
  `tokenizers==0.12.1` and Transformers commit are not aligned. Verify both
  versions before loading a checkpoint.
- `timm`, `easydict`, `open3d`, `objaverse`, or `sentence_transformers` import
  errors identify optional route dependencies. Install only the dependency for
  the selected route: PointBERT imports `timm`; Gradio file/object handling
  uses Open3D and Objaverse; traditional metrics use Sentence-BERT and model
  downloads.
- The evaluator source uses the legacy OpenAI Python API. A modern client that
  lacks `openai.error` or `openai.ChatCompletion` is incompatible without an
  adapter; use the legacy client version or do not run that evaluator.

## CUDA and memory

- `torch.cuda.is_available()` must be true for model chat, batch generation,
  and the shipped training launchers. A successful import is not CUDA proof.
  Check driver, torch CUDA tag, GPU capability, and a one-element allocation.
- Out-of-memory errors are expected when dtype/model size exceeds the README
  budget: approximately 14/28 GB for 7B float16/float32 and 26/52 GB for 13B
  float16/float32, before runtime headroom. Lower model size, use a supported
  lower-memory dtype, reduce batch size, or stop; do not silently switch to CPU
  because the launchers call `.cuda()`.
- `flash_attn` and Deepspeed failures are compiled-backend failures, not data
  schema errors. Match Python, torch, CUDA, compiler, and extension versions;
  the training route's validator can detect missing FlashAttention without
  launching `torchrun`.

## Data and checkpoint failures

- Missing `<object_id>_8192.npy`, malformed `(N,6)`, non-finite values, RGB
  outside `[0,1]`, zero-radius XYZ, or an annotation/object mismatch should be
  fixed with the data route's local validator before model loading.
- A checkpoint/config mismatch involving `point_backbone_config_name`, point
  token count, or PointBERT v1.1/v1.2 weights can produce shape or token errors.
  Keep the checkpoint's config and point-backbone weight family paired.
- If a generation output already exists, the batch launcher loads it instead
  of recomputing. Check the expected output path and preserve the old artifact
  before starting a fresh run.

## Network, API, and serving safety

- Hub model identifiers, Objaverse object IDs, traditional metric models, and
  WordNet may access the network or download large artifacts. Treat them as
  explicit preconditions, not smoke checks.
- OpenAI scoring requires an approved key, network access, model entitlement,
  and a cost ceiling. Never put a key in a skill file or committed result.
- The Gradio demo binds `0.0.0.0` and is a research preview. Keep sharing off,
  use a controlled temporary directory, and review file-access exposure before
  making it reachable outside a trusted host.
