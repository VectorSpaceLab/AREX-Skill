# Troubleshooting: Pipeline Basics

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: transformers.generation_utils` | Newer `transformers` releases removed the legacy alias used by OpenPrompt 1.0.1. | Use the pinned inspection stack or keep the compatibility shim in `scripts/check_openprompt_install.py`. |
| `ModuleNotFoundError: yacs` | The package import path pulls `yacs.config.CfgNode`. | Install `yacs` and rerun the smoke. |
| `ModuleNotFoundError: torch` | PyTorch is missing or the wrong wheel is active. | Install the CPU torch wheel first; OpenPrompt imports it broadly. |
| Import errors for `sklearn`, `rouge`, or `scipy` | Those runtime deps are imported indirectly through the package surface. | Install the repo runtime bundle before debugging the pipeline. |
| `RuntimeError: Either wrapped_tokenizer or tokenizer_wrapper_class should be specified.` | The loader was given neither a wrapper object nor a wrapper class. | Pass a wrapper instance, or pass both `tokenizer_wrapper_class` and `tokenizer`. |
| `RuntimeError: No tokenizer specified to instantiate tokenizer_wrapper.` | A wrapper class was provided without a tokenizer. | Supply the tokenizer object even for a fake wrapper. |
| `TypeError: got multiple values for keyword argument 'label'` | Wrapper output and metadata both contained the same key. | Keep wrapper-returned keys disjoint from metadata keys; `label` is the common collision. |
| Loader batches are empty or key shapes do not line up | The fake wrapper returned the wrong lengths or missing `loss_ids`. | Make the wrapper return tensor-friendly lists and keep template lengths consistent. |
| `PromptForGeneration` stops too early or never stops | Generation workflow is missing the EOS / teacher-forcing setup. | Use `teacher_forcing=True`, `predict_eos_token=True`, and a generation-aware template. |
| `load_plm()` tries to download weights | The model path is not cached locally. | Point `model_path` to a local cache or avoid calling `load_plm()` in offline smoke checks. |

## Fast triage order

1. Verify the pinned CPU inspection env or equivalent dependency set.
2. Run `scripts/check_openprompt_install.py` from a temp directory.
3. If the smoke fails, inspect wrapper kwargs and metadata collisions before looking at template logic.
