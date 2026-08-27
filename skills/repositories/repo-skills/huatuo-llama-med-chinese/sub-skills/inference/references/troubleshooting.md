# Inference troubleshooting

Use this reference after building a dry-run command and before approving real model execution. Keep model downloads, GPU runs, and public serving behind explicit user authorization.

## Quick triage

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `NameError: name 'device' is not defined` in medical QA or literature inference | CUDA is not available. The batch/literature runners define `device` only inside `if torch.cuda.is_available()`. | Treat those runners as CUDA-required. Install/activate a CUDA-compatible PyTorch environment, verify `torch.cuda.is_available()` is true, and retry. For local UI experiments only, the Gradio workflow has CPU/MPS branches, but 7B CPU execution is usually impractical. |
| `AssertionError: Please specify a --base_model` in Gradio serving | `generate.py` asserts that the base model is non-empty. | Rebuild the command with explicit `--base-model`. Ensure it points to a local model directory or an authorized Hugging Face id. |
| `OSError`, `Repository Not Found`, auth errors, or cache/download attempts during `from_pretrained` | Base model path/id is missing, inaccessible, private without credentials, or not already cached. | Provide a valid local model path or authorize remote download/login. Keep model-family compatibility with the LoRA adapter. |
| PEFT errors for `adapter_config.json` or `adapter_model.bin` | LoRA adapter path is wrong, incomplete, or incompatible with the base model. | Use an adapter directory containing both files, or a valid adapter id. Match LLaMA adapters with LLaMA/Alpaca-style bases and Bloom/Huozi adapters with Bloom-derived bases. |
| CUDA out-of-memory during load or generation | 7B half-precision model plus LoRA exceeds available GPU memory; beams and max tokens increase memory. | Try `--load-8bit` only with a compatible bitsandbytes/CUDA stack, reduce batch/concurrency, lower `num_beams` or max tokens in custom code/UI, free GPU memory, or use a larger GPU. |
| `ValueError: Can't read templates/<name>.json` | Template lookup is current-working-directory dependent or the template name is unavailable. | Run from a compatible project root with a `templates/` directory, or adapt the runtime project to resolve templates explicitly. Use `med_template`, `literature_template`, or `bloom_deploy` when available. Route template asset validation to `prompt-data-formats`. |
| `IndexError` from response splitting, prompt echo, or empty parsed answer | Template `response_split` marker does not match generated output; common when using `med_template` for literature or Bloom punctuation with LLaMA template. | Choose `literature_template` for literature single/multi workflows, `med_template` for LLaMA/Alpaca medical QA, and `bloom_deploy` for Bloom/Huozi medical QA. Check full-width vs half-width Chinese colon differences. |
| JSON decode error or missing key such as `instruction`/`output` in medical QA | `--instruct_dir` is not JSON Lines or records lack required fields. | Use one JSON object per line with at least `instruction` and `output`. Route deeper schema conversion/validation to `prompt-data-formats`. |
| Literature multi-turn produces broken history or poor splits | Wrong template, missing `<user>:`/`<bot>:` convention, or pasted multiline user inputs changing history. | Use `literature_template`; keep user turns concise; remember the loop runs five turns and concatenates history as `<user>: ... <bot>: ...`. |
| Gradio endpoint reachable by others unexpectedly | Source serving defaults bind to all interfaces and enable share links. | Prefer the bundled builder defaults: `--server_name 127.0.0.1 --share_gradio False`. Use `0.0.0.0` or `--share-gradio` only after explicit authorization, network review, and medical-safety disclaimers. |
| Slow or apparently stuck load | Large model download/cache, CPU fallback, or first-time compilation. | Verify whether a download is occurring, whether GPU is visible, and whether the user authorized the model source. Disable unnecessary sharing/server exposure while debugging. |
| Repetitive, low-quality, or medically unsafe output | Model/adapter/template mismatch, small/limited training data, LLaMA/Alpaca Chinese limitations, or decoding settings. | First verify base-model/adapter/template alignment. Keep `temperature=0.1`, `top_p=0.75`, `top_k=40`, `num_beams=4` as the repo defaults for comparability; then experiment carefully. README evidence suggests Bloom/Huozi-style models may perform better for some Chinese medical outputs. Never present generated text as diagnosis. |

## Difficult cases

### Literature multi-turn with a medical template

If the user has a literature LoRA but asks for multi-turn inference with `med_template`, do not pass the command through unchanged. Explain that the literature workflow builds `<user>`/`<bot>` history and expects `literature_template` with `### 回复:`. Rebuild the dry-run command with `--workflow literature-multi --prompt-template literature_template` unless the user explicitly requests an ablation.

### Missing CUDA and `device` undefined

If a user reports `NameError: device is not defined`, identify it as a runner limitation rather than a bad prompt or bad data file. The medical QA and literature scripts never assign `device` on CPU. Verify CUDA first:

```bash
python - <<'PY'
import torch
print(torch.__version__)
print(torch.cuda.is_available())
print(torch.cuda.device_count() if torch.cuda.is_available() else 0)
PY
```

If CUDA is false, do not claim the batch/literature workflows are CPU-verified. Either use a CUDA environment, narrow the task to dry-run command construction, or use the Gradio workflow's CPU/MPS path only for explicitly accepted small/slow experiments.

## Routing reminders

- Dataset schema fixes, JSONL conversion, and template JSON editing belong to `prompt-data-formats`.
- LoRA training or changing training hyperparameters belongs to `finetuning`.
- Merging adapters into standalone checkpoints belongs to `checkpoint-export`.
- Running the three-way baseline/Alpaca/medical comparison is optional and expensive; use it only after the user authorizes all model assets and GPU execution.
