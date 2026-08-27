# Installation and Runtime Preparation

Read this before running any real Huatuo/BenTsao model workflow. The safe bundled validators and command builders use only the Python standard library, but actual inference, training, Gradio serving, and export require a compatible ML environment and model assets.

## Package shape

The repository is script-based and does not define an installable distribution through `pyproject.toml`, `setup.py`, or `setup.cfg`. Public workflows are entrypoint scripts plus data/template assets rather than importable package commands.

For a real runtime project, keep the workflow code, templates, and data assets together so template lookup and relative paths are predictable. The bundled command builders in this skill print dry-run commands and warnings; they do not install dependencies or launch the workflows.

## Python and dependency notes

- Python: repository docs recommend Python 3.9+.
- Documented dependency file includes Accelerate, AppDirs, BitsAndBytes, Black, Datasets, Fire, PEFT, Transformers, Gradio, SentencePiece, SciPy, and W&B.
- Torch is required by model scripts but is not listed in the documented dependency file.
- Choose Torch/CUDA wheels that match the host driver and GPU. Do not treat a CPU-only Torch import as validation of CUDA inference or 8-bit/bitsandbytes training.
- For older PEFT/Transformers versions, avoid mixing very new package versions unless you have tested the script imports and adapter APIs.

## Suggested environment planning by task

| Task | Minimum runtime requirements |
| --- | --- |
| Validate prompt/data assets | Python stdlib only; use `prompt-data-formats/scripts/validate_assets.py`. |
| Build dry-run commands | Python stdlib only; use the bundled command builders. |
| Medical QA or literature inference | Torch, Transformers, PEFT, Fire, SentencePiece/tokenizer dependencies, CUDA-capable device for the observed batch/literature runners, base model, LoRA adapter, matching template assets. |
| Gradio serving | Inference requirements plus Gradio; review server binding and share-link risks. |
| LoRA fine-tuning | Torch/CUDA, Transformers, PEFT, Datasets, Fire, W&B if enabled, bitsandbytes/load-in-8bit compatibility, base model, training JSONL, output storage. |
| Checkpoint export | Torch, Transformers, PEFT, enough CPU RAM/storage, base model, LoRA adapter. State-dict export additionally assumes a LLaMA-7B-compatible architecture. |

## Safe escalation checklist

Before running any expensive or networked workflow:

1. Validate assets with the prompt/data sub-skill.
2. Build the command with the nearest bundled command builder and inspect the warnings.
3. Confirm base model and LoRA adapter family compatibility.
4. Confirm template compatibility and `response_split` behavior.
5. Confirm model weights and adapter files are already available or that downloads are explicitly authorized.
6. Confirm CUDA/VRAM for batch/literature inference or training; for serving, confirm binding and share-link policy.
7. For medical outputs, record that generated content is non-clinical research output.

## Minimal checks that do not require model weights

```bash
python scripts/check_skill_assets.py --skill-root .
python sub-skills/prompt-data-formats/scripts/validate_assets.py --asset-root <asset-root> --max-records 100
python sub-skills/inference/scripts/build_inference_command.py --workflow medical-qa --base-model <base> --lora-weights <adapter> --instruct-dir <input-jsonl>
python sub-skills/finetuning/scripts/build_finetune_command.py --base-model <base> --data-path <train-jsonl> --validate-data
python sub-skills/checkpoint-export/scripts/build_export_command.py --mode hf --base-model <base> --adapter-weights <adapter> --output-dir <out>
```

These commands are intended for validation and planning. They do not prove that a large model can be loaded or that medical generation quality is acceptable.
