# Cross-cutting troubleshooting

Read this when installation, imports, backend detection, or a workflow fails
before routing to the nearest sub-skill troubleshooting reference.

## Install and import

- **`No module named sat` or `No module named cpm_kernels`:** XrayGLM imports
  SwissArmyTransformer as `sat`; install the repository-compatible SAT release
  and its required runtime dependencies in the isolated environment. Do not
  infer success from `transformers` alone.
- **DeepSpeed import crashes with `torch.library.custom_op`:** an unbounded
  current DeepSpeed release is incompatible with the older PyTorch combination.
  Pin a DeepSpeed release compatible with the selected PyTorch, or omit it for
  inference-only work. Re-run `pip check` and import the exact route after
  changing versions.
- **`pip check` reports FastAPI/Pydantic conflicts:** old Gradio/DeepSpeed
  combinations may require mutually incompatible major Pydantic generations.
  Use a coherent pinned environment, not a sequence of latest upgrades; keep
  inference and training environments separate if variants conflict.
- **`pkg_resources` or `bitsandbytes` warnings:** legacy SAT/bitsandbytes code
  may expect older setuptools or CUDA runtime libraries. A warning is a reason
  to inspect the optional path, not a proof of quantization readiness.

## CUDA and memory

- **`torch.cuda.is_available()` is false:** inspect the PyTorch build, driver
  passthrough, visible devices, and container runtime. A visible GPU in another
  shell does not prove the selected Python sees it.
- **`no kernel image is available`:** the selected torch/extension build may not
  support the GPU architecture. Match the wheel and extension ABI before
  retrying; do not switch silently to CPU and call the model path verified.
- **Out-of-memory while loading or generating:** stop the run, record model,
  checkpoint, sequence limit, GPU visibility, and quantization state. Reduce
  sequence capacity or use an approved compatible checkpoint/quantization mode
  only after proving that the optional quantization backend works.
- **`nvcc` missing:** pip CUDA wheels can still run, but source-built CUDA
  extensions cannot be assumed installable. Do not launch a long compilation
  without confirming toolkit, compiler, RAM, and ABI compatibility.

## Data and privacy

- **Missing image or malformed JSON:** route to `data-preparation` or
  `fine-tuning` validators. Use an explicit base directory for relative paths;
  never repair records by guessing or silently dropping failures.
- **Unexpected or sensitive model output:** preserve prompt/checkpoint/sampling
  metadata, redact patient identifiers, and stop any clinical use. Model text
  may hallucinate, omit findings, or expose memorized content.
- **URL image fails or is slow:** confirm approved HTTPS/network policy and
  response content type/size. Prefer a local, audited copy for reproducible
  research; do not put credentials or private URLs into skill artifacts.

## Operations and state

- **CLI help works but model load fails:** this proves only argument parsing.
  Check checkpoint files, tokenizer cache, model revision, CUDA, and memory in
  that order.
- **WebUI says `Timeout!` for every error:** the source catches broad exceptions
  and uses a generic message. Inspect the server traceback and validate input
  image/text before changing timeout settings.
- **Conversation mixes Chinese and English or wrong image:** use `clear` and,
  for a language change, start a fresh session. The first image is retained as
  a processed tensor in history; do not carry it across patients/studies.
- **Training launcher behaves unexpectedly:** do not rerun blindly. Validate
  data, adapter flags, GPU count, hostfile, NCCL, output destination, and the
  corrected launcher template in the fine-tuning route. Preserve the base
  checkpoint and use a new output directory.
