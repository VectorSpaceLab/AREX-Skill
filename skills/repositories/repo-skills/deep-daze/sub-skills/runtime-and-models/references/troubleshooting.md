# Runtime troubleshooting

Use this guide when `deep-daze` fails before or during CLIP loading, tokenizer
checks, CLI startup, or early generation setup. The safe preflight command is:

```bash
python scripts/check_deep_daze_runtime.py
```

It intentionally avoids CLIP checkpoint downloads and image generation.

## Missing dependency errors

| Symptom | Likely missing component | Fix direction |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torch'` | PyTorch | Install a PyTorch build matching the intended CPU/CUDA runtime. Verify with the safe helper before generation. |
| Import failure mentioning `torchvision` or transforms | torchvision | Install a torchvision version compatible with the installed Torch build. Mismatched Torch/torchvision wheels are common. |
| Import failure mentioning `siren_pytorch` or SIREN | `siren-pytorch` | Install the SIREN dependency used by the generator network. |
| Import failure mentioning `torch_optimizer` | `torch_optimizer` / torch optimizer package | Install the optimizer package before using default optimizer `AdamP` or optimizer selection features. |
| `imagine` command fails while importing `fire` | Fire | Install `fire`; it is required for console command dispatch. |
| Tokenizer import failure mentioning `ftfy` | ftfy | Install `ftfy`; tokenizer text cleanup depends on it. |
| Tokenizer import failure mentioning `regex` | regex | Install the third-party `regex` package; Python's built-in `re` is not a drop-in substitute here. |

After installing or repairing dependencies, rerun:

```bash
python scripts/check_deep_daze_runtime.py --strict
```

`--strict` treats warnings, such as a missing console script or unexpected model
registry, as a nonzero exit.

## Missing BPE vocabulary package data

The CLIP tokenizer requires the bundled BPE vocabulary file
`deep_daze/data/bpe_simple_vocab_16e6.txt`. If this data file is missing,
imports or tokenization can fail with file-not-found style errors, or the helper
can report a failed package-data check.

Fix direction:

1. Reinstall `deep-daze` from a package artifact that includes package data.
2. Avoid partial manual copies of only Python modules.
3. If building a wheel or source distribution, ensure the BPE text file is
   included as package data.
4. Rerun the helper and confirm `tokenize('a house')` returns shape `(1, 77)`.

Do not bypass the tokenizer by creating an empty vocabulary file. That can make
imports proceed while corrupting text-token semantics.

## CLIP checkpoint download, cache, checksum, and network failures

Safe preflight checks do not download CLIP models. Downloads begin when a
registered model name is loaded by generation code.

Common symptoms and actions:

| Symptom | Meaning | Fix direction |
| --- | --- | --- |
| Network timeout, DNS failure, or HTTP error while loading a model | The runtime cannot reach the CLIP checkpoint host | Retry on a network with outbound access, pre-populate the cache, or use a valid local checkpoint path in the generation workflow. |
| Warning that a cached file exists but SHA256 does not match | A cached checkpoint is corrupt or incomplete | Remove the corrupt checkpoint from the CLIP cache and retry the download. |
| Runtime error that final SHA256 does not match | Download completed but content does not match the expected model hash | Retry through a reliable network path that does not rewrite binary downloads. |
| Cache target exists and is not a regular file | A directory or special file blocks the expected checkpoint filename | Move/remove the blocking cache entry and retry. |
| `Model ... not found; available models = ...` | The supplied `model_name` is neither a registered CLIP name nor an existing checkpoint file | Use one of `RN50`, `RN101`, `RN50x4`, `ViT-B/32`, `ViT-L/14`, or provide a valid checkpoint path. |

The default cache is the per-user CLIP cache `~/.cache/clip`. Treat cache
mutation as an intentional setup step, not as part of a cheap smoke test.

## CPU-only Torch and accelerator expectations

The package automatically chooses CUDA only when `torch.cuda.is_available()` is
true; otherwise it falls back to CPU.

- CPU-only is acceptable for import checks, package-data checks, console-script
  discovery, and tokenizer shape validation.
- CPU-only generation can be extremely slow and should not be used as a routine
  acceptance test for image quality or performance.
- If CUDA was expected but the helper reports no CUDA, install a CUDA-enabled
  PyTorch build that matches the system driver/container runtime and make the
  GPU visible to the process.
- Other PyTorch backends such as MPS are not selected by this package's device
  choice logic, even if the installed Torch build exposes them.

## JIT warning on Torch versions other than 1.7.1

Default generation arguments can request `jit=True`, but the package disables
JIT when the Torch version string does not contain `1.7.1`. The message:

```text
Setting jit to False because torch version is not 1.7.1.
```

is expected for modern Torch installations. It is usually not a failure. Prefer
setting `jit=False` in generation workflows if you want the behavior to be
explicit. Do not treat the warning as proof that CLIP failed to load; look for a
separate download, checksum, CUDA, or checkpoint error.

## VRAM and resource pressure

Full generation combines CLIP inference, SIREN optimization, random cutouts,
image saving, and optional media export. It can fail or stall even after all
safe runtime checks pass.

If generation hits out-of-memory or stalls:

1. Lower `image_width`.
2. Lower `batch_size`.
3. Use fewer `iterations` and `epochs` for trials.
4. Prefer `ViT-B/32` or smaller registered models before trying `ViT-L/14`.
5. Disable GIF/video/progress outputs unless they are required.
6. Ensure the intended CUDA device is visible before blaming model parameters.

Use workflow-specific CLI or Python API guidance for exact flags and code.

## Why full generation is not a safe smoke check

A command that actually constructs `Imagine` or runs `imagine` can:

- download a large CLIP checkpoint;
- write to the per-user CLIP cache;
- run thousands of optimization steps with default settings;
- allocate significant CPU/GPU memory;
- create image, progress, GIF, or video outputs;
- ask about overwriting existing outputs or try to open an output folder;
- fail because of display/media tooling unrelated to core import readiness.

Therefore, use `scripts/check_deep_daze_runtime.py` for preflight. Run full
generation only when model downloads, cache writes, output files, runtime cost,
and hardware requirements are all acceptable.
