# Troubleshooting

## Purpose

Use this when model selection, load, save, or generation fails. If the problem is really about data shape, training backend, CLI/API serving, or evaluation, switch to the neighboring sub-skill first.

## Load and registry problems

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `AssertionError: The model_name ... is not valid` | The key is not registered in `BaseModel.registry` | Use one of the keys listed in `references/model-catalog.md`. |
| `No xturing.json found in local directory ... Pass model_name=...` | The path is a plain Hugging Face checkpoint directory, not a saved xTuring checkpoint | Call `BaseModel.load(path, model_name="<family-key>")` or use `GenericModel(path)` when the checkpoint is not family-backed. |
| `The xturing.json file is not correct. model_name is not available...` | A saved checkpoint directory is missing the expected metadata | Re-save the checkpoint from xTuring or repair the metadata before loading it again. |
| `Loading model from xTuring hub` followed by a download failure | The `x/...` hub path needs network access or the cached artifact is missing | Use a saved local checkpoint or retry with network access. |

## Backend and quantization problems

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `Int8 models are not supported on CPU` | The model variant requires a GPU or a different CPU path | Pick a non-int8 model, or use the CPU INT8 path only when the ITRex backend is available. |
| `To use Lora with 8-bit quantization, please install the bitsandbytes package.` | The quantized LoRA backend is missing | Install the quantization backend or switch to a non-quantized LoRA family. |
| `CUDA Setup failed despite GPU being available` from bitsandbytes | The CUDA runtime, wheel, or library path does not match the installed bitsandbytes build | Repair the CUDA/bitsandbytes stack, then rerun `scripts/inspect_xturing_install.py`. |
| `To run int8 or k-bits model on cpu, please install the intel-extension-for-transformers package.` | The CPU INT8 route expects ITRex | Install `intel-extension-for-transformers` or avoid the CPU INT8 path. |
| `WARNING: CUDA is not available, using CPU instead` | The active PyTorch build is CPU-only | Use CPU-safe model families or install a CUDA-capable PyTorch build before trying LoRA INT8/K-bit work. |

## Unsupported targets

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `StableDiffusion` raises `NotImplementedError` | The model class is a placeholder only | Choose a supported causal model family instead. |

## Practical checks

- Run `scripts/inspect_xturing_install.py` to confirm the installed package, registry, and backend state before debugging a model issue.
- If the problem is about a saved checkpoint from this package, verify that `xturing.json` exists and that the saved directory matches the expected model key.
- If the problem is about a plain local checkpoint, prefer the generic wrapper or pass `model_name=` explicitly.
