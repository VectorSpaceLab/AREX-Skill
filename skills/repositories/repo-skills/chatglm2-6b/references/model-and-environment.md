# Model and Environment Reference

## When to read

Read this before installing dependencies, choosing a backend, or deciding
whether a documented demo/benchmark can be run on the current machine.

## Repository contract

ChatGLM2-6B is exposed through Hugging Face Transformers remote model code,
not through a local importable package. The public model id is
`THUDM/chatglm2-6b`; a complete local model directory can replace it. Calls
use `trust_remote_code=True`. A pinned model revision is preferable when a
reproducible implementation is required.

The repository requirements specify `transformers==4.30.2`, `torch>=2.0`,
`cpm_kernels`, `accelerate`, `sentencepiece`, and UI/streaming dependencies.
The demo code is from the Gradio/Streamlit API era in which Gradio's
`Textbox.style()` still exists. The verified compatibility choice for this
skill was `gradio==3.50.2` and `streamlit==1.24.0`; newer versions may require
source adaptation.

## Backend planning

| Backend | Repository support | Operational note |
| --- | --- | --- |
| CUDA | Default for CLI, web demos, APIs, C-Eval, and P-Tuning scripts. | Verify PyTorch CUDA and free VRAM; official scripts call `.cuda()`. |
| CPU | Documented fallback. | Slow and memory-heavy; unquantized deployment is documented around 32 GB RAM. |
| MPS | Documented Mac-specific alternative. | Use a local model path and compatible PyTorch; do not use CUDA-only quantization kernels. |
| Multi-GPU | `utils.load_model_on_gpus` with `accelerate`. | Inspect and validate the device map; first-device module placement avoids input/embedding mismatch. |
| DeepSpeed | Optional full-parameter fine-tuning. | Install separately only for the expensive four-GPU path. |

The README reports roughly 13 GB for FP16/BF16 and about 5–6 GB for INT4 on
particular context lengths. These are planning estimates, not hard limits;
KV cache, context, batch, PyTorch attention implementation, and concurrent
requests alter actual memory.

## Minimum checks

Run the bundled checker before weights:

```bash
python scripts/check_installation.py --backend auto
```

For a local model path:

```bash
python scripts/check_installation.py --backend cuda --model-path /models/chatglm2-6b
```

The checker reports missing packages, CUDA/MPS availability, device count, and
path existence. It never contacts the Hub. Full generation, benchmark, service,
and training checks require deliberate model/data/listener decisions.
