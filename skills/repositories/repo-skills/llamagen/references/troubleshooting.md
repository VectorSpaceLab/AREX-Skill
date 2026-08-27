# Cross-cutting troubleshooting

Use this page when a failure does not belong to one specific sub-skill.

## 1. Install or import failures
**Symptoms**
- `ModuleNotFoundError`
- `ImportError`
- `pip check` failures
- mismatched package versions after installation

**Likely causes**
- Missing CUDA-capable PyTorch or a version skew between torch and torchvision.
- `transformers`, `diffusers`, `vllm`, `gradio`, `tensorflow-cpu`, or `wandb` not installed in the active inspection environment.
- A stale editable install or an import from the wrong Python path.

**Recovery**
- Run `scripts/check_env.py` from the repo root and fix the first failing import.
- If you are only probing optional serving or evaluation extras, a missing optional dependency now reports `environment=partial` with the missing module name instead of a raw traceback.
- Re-run `python -m pip check` in the same environment.
- If a new dependency was added, reinstall only the needed package family instead of broad dev extras.

## 2. CUDA / GPU readiness
**Symptoms**
- `torch.cuda.is_available()` is false.
- Training or sampling scripts abort immediately.
- DDP or FSDP launchers complain about NCCL or world size.

**Likely causes**
- CPU-only PyTorch wheel.
- Driver / CUDA wheel mismatch.
- GPU launch variables do not match the machine.

**Recovery**
- Use the verified CUDA baseline and confirm a tiny tensor allocation with `scripts/check_env.py`.
- Match `nnodes`, `nproc_per_node`, `node_rank`, `master_addr`, and `master_port` to the actual launch topology.
- For FSDP resumes, keep the checkpoint world size compatible with the current launch.

## 3. Missing checkpoints or caches
**Symptoms**
- File-not-found errors for `pretrained_models`, T5 caches, or sample output trees.
- `load_state_dict` failures.
- `language/t5.py` cannot locate the local cache.

**Likely causes**
- The workflow is pointed at a path from a different stage.
- The checkpoint is for a different model family or precision layout.
- The data-preparation step was never run.

**Recovery**
- Confirm whether the workflow expects tokenizer weights, code caches, or T5 features.
- Route preprocessing problems to `data-preparation` instead of retrying the training job blindly.
- Check whether the checkpoint stores `model`, `module`, `state_dict`, or raw FSDP weights.

## 4. Evaluation dependencies
**Symptoms**
- CLIP, clean-fid, or TensorFlow import errors during evaluation.
- Evaluation scripts fail even though the generation scripts work.

**Likely causes**
- The environment was prepared only for training / sampling.
- TensorFlow or CLIP dependencies are missing or on incompatible versions.

**Recovery**
- Re-run the environment smoke with the evaluation flags enabled.
- Use the bundled evaluation references to confirm the expected sample-tree layout before launching the evaluator.

## 5. `app.py` import behavior
**Symptoms**
- Importing `app.py` triggers checkpoint loading or path resolution errors.

**Likely causes**
- `app.py` is a demo entry point, not a safe import-time helper.

**Recovery**
- Treat `app.py` as reference-only.
- Use the bundled serving sub-skill and its wrapper instead.

## 6. vLLM path and model-id errors
**Symptoms**
- A serving launch complains about a bad path or a malformed model identifier.

**Likely causes**
- The checkpoint or fake-JSON path was passed where a Hugging Face-style model id was expected.
- The wrong serving wrapper or model family was selected.

**Recovery**
- Use the class-conditional serving notes.
- Confirm the checkpoint and fake-JSON paths separately before launching.

## 7. Prompt / batch layout problems
**Symptoms**
- Evaluation cannot find generated images or prompt files.
- The sampler produces empty or malformed batch outputs.

**Likely causes**
- The prompt CSV / TSV columns do not match the expected `Prompt` column.
- The sample directory is missing `images/`, `result.jsonl`, or `captions.txt`.

**Recovery**
- Check the text-conditional evaluation notes for the expected layout.
- Use a tiny test batch before a full prompt run.
