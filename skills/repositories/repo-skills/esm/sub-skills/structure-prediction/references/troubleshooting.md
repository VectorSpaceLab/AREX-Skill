# ESMFold Troubleshooting

## Missing ESMFold Dependencies

Symptoms:

- `ModuleNotFoundError` for `openfold`, `dllogger`, `deepspeed`, `omegaconf`, `ml_collections`, `biotite`, or related packages.
- Base `import esm` works, but `esm.pretrained.esmfold_v1()` or `esm-fold` fails.

Likely cause: only base `fair-esm` is installed. ESMFold needs optional dependencies from the `esmfold` extra and OpenFold-style packages. The original README recommends Python `<=3.9`, PyTorch installed first, then `fair-esm[esmfold]`, `dllogger`, and an OpenFold commit. Modern environments may use alternative maintained ESMFold/Transformers paths, but this repo's native `esm-fold` path still expects the older OpenFold-compatible stack.

Response:

1. Verify PyTorch is installed before installing ESMFold extras.
2. Use an isolated environment for ESMFold rather than mutating a working base ESM environment.
3. If OpenFold install fails, check `nvcc`, CUDA toolkit, CUDA-compatible PyTorch, and Python version compatibility.
4. If the user only needs a command or API sketch, use the bundled command builder and do not attempt model loading.

## Python Version and Legacy Dependency Pins

The repo's ESMFold setup notes use Python `<=3.9`, and the conda environment pins older packages such as Python 3.7-era OpenFold dependencies. On newer Python versions, dependency resolution may fail even when base `fair-esm` imports.

Response:

- Prefer a dedicated legacy-compatible environment for native `esm-fold`.
- If the user cannot use old Python/CUDA dependencies, consider whether a Hugging Face Transformers ESMFold implementation or hosted Atlas folding API is acceptable, but keep those as alternatives rather than this sub-skill's native path.
- Do not claim native `fair-esm` ESMFold will work in modern Python without verifying its optional dependency stack.

## CUDA, NVCC, and OpenFold Build Failures

Symptoms:

- OpenFold or CUDA extension build errors.
- Messages about missing `nvcc`.
- CUDA version mismatch between PyTorch, toolkit, and driver.

Response:

1. Confirm `python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"` in the target environment.
2. Confirm `nvcc --version` if installing OpenFold from source.
3. Match PyTorch CUDA build, local CUDA toolkit, and driver compatibility.
4. Use CPU-only only as a fallback for very small work or correctness checks; it does not avoid all installation requirements if OpenFold imports are missing.

## CUDA Out of Memory

Symptoms:

- `RuntimeError: CUDA out of memory` from Python inference.
- `esm-fold` logs OOM for a batch or individual sequence and skips that prediction.

Response for short-sequence batches:

1. Lower `--max-tokens-per-batch` from `1024` to `512`, `256`, or `128`.
2. Set `--max-tokens-per-batch 0` to disable batching if needed.
3. Add `--chunk-size 128`, then try `64` or `32`.
4. Lower `--num-recycles` if quality/runtime tradeoff is acceptable.

Response for one long sequence:

1. Use `--chunk-size 128`, then `64`, then `32`.
2. Lower `--num-recycles`.
3. Try `--cpu-offload` when CUDA works but GPU memory is the bottleneck.
4. Fall back to `--cpu-only` only with a clear warning that inference can be slow.

## CPU-Only Dtype and Runtime Issues

Symptoms:

- fp16/half precision errors on CPU.
- Folding appears to hang or takes much longer than expected.

Response:

- In Python, call `model.esm.float()` before `model.cpu()` and inference.
- In CLI, use `--cpu-only`; the native script performs the fp32 conversion.
- Use tiny sequences for CPU smoke tests and warn that realistic ESMFold CPU runs can be impractically slow.
- Keep `--chunk-size` set for long CPU sequences to avoid memory spikes, while noting that smaller chunks are slower.

## CPU Offload Problems

Symptoms:

- FSDP, distributed process group, NCCL, or CUDA initialization errors with `--cpu-offload`.

Response:

- `--cpu-offload` still requires CUDA/NCCL; it is not CPU-only mode.
- Do not combine `--cpu-offload` with `--cpu-only`.
- Ensure no other process is using the local init port if the native script initializes a local process group.
- If CPU RAM is limited, offload can still fail; reduce chunk size/recycles or use a smaller workload.

## FASTA and Output Path Errors

Symptoms:

- `FileNotFoundError` for FASTA.
- Output directory cannot be created or written.
- Unexpected output filenames.

Response:

- Validate the FASTA file exists before running `esm-fold`.
- Create or choose an output directory whose parent exists and is writable.
- Use unique, simple FASTA headers because the CLI writes `<header>.pdb`.
- Use the bundled command builder to validate paths and print the command before running heavy inference.

## Model Downloads and Cache Control

Symptoms:

- Download blocked by offline environment.
- Repeated downloads or unexpected cache location.
- Permission errors under a shared cache.

Response:

- ESMFold model loaders download weights through PyTorch Hub-style cache behavior when weights are absent.
- Use `esm-fold --model-dir MODEL_CACHE` to set the torch hub cache parent for CLI folding.
- For Python workflows, configure torch hub cache before loading the model if a controlled cache is required.
- Confirm network/download permission before real folding; `esm-fold --help` and the bundled builder do not download weights.

## Multimer Formatting Mistakes

Symptoms:

- Chains are folded independently instead of as one complex.
- FASTA parser produces multiple predictions when one multimer was intended.

Response:

- Put the full complex in one FASTA record with chains separated by `:`.
- Example: `MKTAYIAKQRQISFVKSHFSRQ:DLLKKALE`.
- In Python, pass the colon-separated complex as one string to `model.infer_pdb` or one list element to `model.infer`.

## Scope Misrouting

- If the user asks for embeddings, contacts, or `.pt` representation files, route to `../model-embeddings/SKILL.md`.
- If the user asks to design sequences from a backbone or score sequences against coordinates, route to `../inverse-folding/SKILL.md`.
- If the user asks for mutation-effect scoring or DMS prediction, route to `../variant-effect-prediction/SKILL.md`.
