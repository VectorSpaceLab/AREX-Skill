# Repo Workflows

## Purpose

Read this when you need the quickest path from a user request to the owning sub-skill.

## Route summary

1. **Inference / transcription**
   - Start with `sub-skills/inference/`.
   - Use when the user already has audio and wants a Distil-Whisper checkpoint to transcribe it.

2. **PyTorch pseudo-labelling and training**
   - Start with `sub-skills/pytorch-training/`.
   - Use when the user wants to generate pseudo-labels, initialize a student checkpoint, train distillation, or evaluate with the PyTorch scripts under `training/`.

3. **JAX/Flax reproduction**
   - Start with `sub-skills/flax-reproduction/`.
   - Use when the user wants the original Flax package, long-form transcription, checkpoint conversion, or TPU-oriented reproduction steps.

## Environment first

Before any workflow, run `scripts/check-env.py`.

That script should confirm:

- `distil_whisper` imports.
- The CPU torch stack imports cleanly.
- `jax` and `flax` import cleanly.
- The core audio and Hugging Face dependencies are present.

## Common command families

### Inference

- Load a checkpoint with `AutoModelForSpeechSeq2Seq` and `AutoProcessor`.
- Use `pipeline("automatic-speech-recognition", ...)` for the simplest transcription path.
- Add `chunk_length_s` for chunked long-form transcription.
- Pass an `assistant_model` for speculative decoding.

### PyTorch training

- `training/run_pseudo_labelling.py` for dataset transcription and pseudo-label generation.
- `training/create_student_model.py` for student checkpoint initialization.
- `training/run_distillation.py` for teacher-student training.
- `training/run_eval.py` for WER evaluation.

### Flax reproduction

- `training/flax/create_student_model.py` for Flax student initialization.
- `training/flax/run_eval.py` for short-form evaluation.
- `training/flax/run_long_form_transcription.py` for long-form evaluation.
- `sub-skills/flax-reproduction/scripts/convert_train_state_to_hf.py` for the bundled export helper. The source repo script remains `training/flax/convert_train_state_to_hf.py` if you need to compare behavior or the distributed training variant.

## When to stop and read troubleshooting

Read the matching `references/troubleshooting.md` if you see:

- A missing package or import error.
- A version mismatch between Transformers, JAX, Flax, NumPy, or SciPy.
- A script that assumes distributed JAX or a TPU/GPU setup.
- A dataset column, split-name, or Hub-auth problem.
