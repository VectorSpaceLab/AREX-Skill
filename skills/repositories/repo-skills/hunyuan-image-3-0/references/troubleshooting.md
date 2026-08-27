# Root Troubleshooting

Use this root page for cross-cutting failures. Workflow-specific details live
in the nearest sub-skill troubleshooting reference.

| Symptom | Likely cause | Action |
|---|---|---|
| `ModuleNotFoundError: No module named 'utils'` during `import hunyuan_image_3` | Package metadata omitted a top-level helper module used by lazy imports | Use a source/editable install that keeps top-level helper modules importable, or vendor the missing module into the environment. Verify with `scripts/check_hunyuan_image_environment.py`. |
| `PE` or `vllm_infer` imports fail | Optional top-level workflow modules are not installed or not on `PYTHONPATH` | If prompt rewrite or vLLM client workflows matter, install from a source layout that exposes those modules and rerun the safe import checker. |
| `hunyuan-image --help` raises `TypeError: main() missing 1 required positional argument: 'args'` | The console script points directly to `main(args)` | Do not use this console entry point. Use the bundled local runner or dry-run helper in `sub-skills/local-inference-cli/scripts/`. |
| Model path does not exist | Checkpoint was not downloaded, local path contains a raw HF id, or the directory was renamed incorrectly | Download the checkpoint into a dot-free local directory and pass that path as the model id. |
| CUDA import works but generation OOMs | Full checkpoint memory exceeds the host capacity | Re-plan hardware using `references/hardware-and-models.md`; do not treat import or parser checks as generation verification. |
| `flashinfer` or `flash_attention_2` import fails | Optional accelerator not installed or ABI mismatch | Fall back to eager MoE and SDPA attention until the accelerator build matches the torch/CUDA stack. |
| DeepSeek rewrite fails | Missing Tencent Cloud credentials, no network, PE module unavailable, or source parser typo | Route to `prompt-and-image-conditioning`; provide credentials only when intentionally authorized, or use manual/self-rewrite modes instead. |
| Gradio UI fails before `--help` | Current app imports stale module paths | Route to `gradio-app-and-prompt-ui`; run its import checker and use CLI fallback unless the app is patched. |
| vLLM client cannot connect | Server not running, wrong URL, or wrong model alias | Route to `vllm-serving`; render the server command and payload, then ensure payload `model` matches server `--served-model-name`. |
| vLLM server lacks HunyuanImage task support | Standard upstream vLLM or missing task env var | Use the custom HunyuanImage-3.0 vLLM branch and set `VLLM_ENABLE_HUNYUAN_IMAGE3_TASK=1`. |

## Safe escalation order

1. Run the root environment checker.
2. Use the owning sub-skill's dry-run, payload, or import helper.
3. Only then start GPU generation, the Gradio server, a vLLM server, or a
   networked DeepSeek call.

## Do not paper over required backend gaps

If the selected task is actual image generation, CPU import success is not a
CUDA substitute. If a required checkpoint, GPU memory level, custom vLLM branch,
or credential is absent, record the limitation and either narrow the task or
ask for the missing resource before claiming verification.
