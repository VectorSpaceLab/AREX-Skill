# Cross-cutting troubleshooting

Start here for failures that occur before a more specific sub-skill diagnosis.

## Package import failures

1. Run:

   ```bash
   python scripts/check_align_anything_environment.py --json
   ```

2. If `align_anything` is missing, install the package in the active environment before using runtime scripts.
3. If the import failure mentions Transformers tokenization utilities, reinstall a consistent Transformers wheel rather than adding ad-hoc shims.
4. If PyTorch fails with missing shared libraries or oneAPI/JIT symbols, reinstall a consistent PyTorch stack for the platform and CUDA version.
5. If `pip check` reports broken requirements, fix dependency conflicts before interpreting trainer or serving failures.

## CUDA, DeepSpeed, and custom-op failures

- `torch.cuda.is_available() == False`: do not claim GPU training or generation readiness. Use the skill for planning/static checks only.
- `CUDA_HOME` missing: DeepSpeed may import but later fail compiling fused/custom ops. Install a CUDA toolkit matching the PyTorch CUDA build or disable fused/custom op paths.
- OOM or ZeRO failures: reduce per-device batch size, enable gradient accumulation, adjust ZeRO stage, use LoRA/QLoRA/BnB if supported by the workflow, or narrow the model/modality.
- Distributed initialization hangs: verify `MASTER_PORT`, `CUDA_VISIBLE_DEVICES`, launcher world size, Slurm environment, and whether the trainer expects DeepSpeed initialization.

## Model and processor failures

- `trust_remote_code` errors: verify the model repository is trusted and compatible with the installed Transformers version.
- Tokenizer/processor mismatches: pair the model, processor, template, and modality together; multimodal models often need a processor path or model-specific `auto_model_kwargs`.
- Media failures: install PyAV/moviepy/ffmpeg system support and validate image/audio/video paths before launching a Gradio CLI.
- Reward/value model shape errors: distinguish base language models from score/reward/cost/value models and choose the right loader/trainer path.

## Dataset/config failures

- Missing dataset splits, names, or data files: inspect the selected config with `sub-skills/training-and-alignment/scripts/inspect_alignment_config.py` and make every required dataset field explicit.
- Preference data shape errors: ensure chosen/rejected or prompt/response fields match the selected dataset class/template.
- Remote reward math verifier errors: ensure the dataset has `question` and `answer` fields and that answers can be compared in the expected math format.
- Project workflows: use `sub-skills/project-workflows/` before executing project scripts; many require optional packages or separate runtimes.

## Security and side effects

- Do not run source shell scripts or project scripts just to discover capabilities. Use bundled scripts and static inspection first.
- Do not expose Gradio servers, API credentials, model cache paths, or benchmark outputs without user approval.
- Do not delete checkpoints or output directories unless the user explicitly asks.
