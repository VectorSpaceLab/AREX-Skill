# MOSS model-runtime troubleshooting

## Import failures

**Symptoms**

- `ModuleNotFoundError: No module named 'models'`
- `ImportError` for `MossForCausalLM`, `MossTokenizer`, or `MossConfig`
- Hugging Face `AutoModelForCausalLM` cannot find remote custom classes

**Likely causes**

- The MOSS source checkout is not on `PYTHONPATH`.
- The environment has not installed `torch`, `transformers`, `accelerate`, or
  `huggingface_hub`.
- A Hugging Face load omitted `trust_remote_code=True`.

**Recovery**

1. Run `scripts/check_model_runtime.py --repo-root /path/to/MOSS --json`.
2. For local checkout scripts, add the checkout root to `PYTHONPATH` or run from
   a context that imports `models.*` correctly.
3. For Hugging Face checkpoint loading, use `trust_remote_code=True` with both
   tokenizer and model/config loads.
4. Do not treat a local source import as proof that remote checkpoint loading
   will work; remote loading still needs network/cache and model files.

## Missing package metadata

MOSS does not expose a conventional `pyproject.toml` or `setup.py` package. A
`pip install -e .` style workflow may not be available. Prefer installing the
requirements into an environment and then importing from either the MOSS source
root or Hugging Face remote code.

## CUDA and memory failures

**Symptoms**

- `torch.cuda.is_available()` is false.
- CUDA tensor allocation fails.
- Full checkpoint load raises out-of-memory.
- Generation begins but fails near longer context lengths.

**Recovery**

1. Use `scripts/check_model_runtime.py --cuda` for a tiny CUDA check.
2. Compare the target checkpoint precision with the memory table in
   [../../../references/model-overview.md](../../../references/model-overview.md).
3. Prefer INT4 for single-GPU low-memory inference, but do not use INT4/INT8 for
   model parallelism.
4. Reduce prompt/history length and generation length before blaming tokenizer
   or model code.

## Quantized runtime and Triton failures

**Symptoms**

- Errors importing or compiling `triton` kernels.
- Quantized checkpoint loads but generation fails in matrix multiplication.
- Multi-GPU quantized launch raises a model-parallel ValueError.

**Recovery**

- Confirm that `triton` is installed on Linux/WSL; the public docs note that
  Triton support is not currently for Windows or macOS.
- Use one GPU with `moss-moon-003-sft-int4` or `moss-moon-003-sft-int8`.
- Use the FP16 `moss-moon-003-sft` checkpoint when more than one GPU is needed.
- If a quantized path must be proven, run an actual small generation only after
  checkpoint availability and CUDA memory are explicit.

## Checkpoint download/cache failures

**Symptoms**

- Hugging Face snapshot download times out or requires credentials.
- Local path is treated as a model id or vice versa.
- Tokenizer files `vocab.json` or `merges.txt` are missing.

**Recovery**

1. Decide whether `model_name` is a local directory or a Hugging Face id.
2. Pre-download or point to a complete local checkpoint when network access is
   unreliable.
3. Ensure tokenizer files and config/model shards are from the same checkpoint
   family.
4. Keep `trust_remote_code=True` for Auto* loading unless using the local
   `models.*` classes directly.

## License and release constraints

MOSS separates code, data, and model licenses. Before redistributing weights,
serving externally, or using data commercially, check the relevant license or
agreement terms. This sub-skill can guide runtime use, but it is not legal
approval.
