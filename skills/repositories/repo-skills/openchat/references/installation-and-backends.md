# OpenChat installation and backend notes

Use this reference before running any OpenChat prompt, serving, or evaluation workflow. It summarizes package and backend requirements without relying on the original source checkout.

## Package identity

- Distribution name: `ochat`
- Import package: `ochat`
- Python support from package metadata: `>=3.8`
- Source snapshot used for this skill: package version `3.6.1`

The package metadata declares a broad dependency set that includes serving, evaluation, data, and training-related packages. Even if a task only needs prompting, a normal `pip install ochat` may install heavy GPU/runtime dependencies such as PyTorch, vLLM, Ray, FlashAttention, datasets, and W&B.

## Install patterns

For released usage:

```bash
python -m pip install ochat
```

For a local development checkout supplied by the user:

```bash
python -m pip install -e .
```

If dependency resolution fails, identify the selected workflow first:

| Workflow | Minimum practical imports | Runtime notes |
| --- | --- | --- |
| Prompt/model config | `torch`, `transformers`, `pydantic`, `colorama`, `sentencepiece` when slow tokenizers are used | Real tokenizers may download Hugging Face files unless model artifacts are cached locally. |
| Serving | prompt deps plus `fastapi`, `uvicorn`, `ray`, `vllm`, `shortuuid`, `orjson` | Actual generation requires model weights and enough CUDA GPU memory. |
| Evaluation | prompt deps plus `openai`, `tenacity`, `tqdm`, `orjson`, `sympy`, `pylatexenc`, and vLLM stack for local model evaluation | OpenAI API path needs credentials; local path needs model weights and GPU memory. |
| Training/data generation | intentionally out of scope for this skill | Requires additional data, DeepSpeed/FlashAttention-oriented runtime, and long-running GPU work. |

## CUDA and vLLM expectations

OpenChat's server and local benchmark path use vLLM. Treat CUDA as required when users ask to load local OpenChat model weights for serving or local evaluation.

A quick backend smoke check:

```bash
python scripts/check_openchat_import.py --check-cuda
```

The script confirms imports and a tiny CUDA tensor allocation. It does not prove that a specific 7B/8B model will fit in memory.

## FlashAttention notes

The package metadata declares `flash-attn`, and OpenChat's internal unpadded model implementations import FlashAttention for training/model classes. Prompting and serving guidance in this skill does not require running a training loop, but a clean package install may still need a FlashAttention wheel or a CUDA toolkit capable of building one.

If a source build fails with errors like `nvcc was not found` or `CUDA_HOME environment variable is not set`, prefer a prebuilt wheel matching the installed PyTorch major/minor version, CUDA generation, Python ABI, and C++ ABI. Do not start a long source build unless the user has authorized the compiler/toolkit installation and time cost.

## Model artifact expectations

OpenChat code often auto-detects the model type by reading `openchat.json` from the model repository/cache. In offline or custom model deployments, pass the canonical `--model-type` explicitly.

- Existing OpenChat Hugging Face model repos normally include the required tokenizer files and metadata.
- Custom Llama 3 models need `<|eot_id|>`, `<|start_header_id|>`, and `<|end_header_id|>` tokens.
- Mistral/OpenChat 3.5-style models need `<|end_of_turn|>`.
- If EOT tokenization produces multiple token IDs, serving tokenization can fail because the server expects one EOT stop token ID.

## Safe checks versus real runs

Safe checks in this skill:

- import `ochat.config`, `ochat.serving.openai_api_protocol`, and `ochat.evaluation.match_answer`;
- print CLI help for serving/evaluation modules;
- run synthetic prompt and answer-matcher smoke scripts.

Real runs that require explicit task context:

- downloading tokenizer/model files;
- starting a FastAPI/vLLM server;
- running a benchmark suite;
- calling OpenAI-compatible APIs with credentials;
- running training/data-generation pipelines.
