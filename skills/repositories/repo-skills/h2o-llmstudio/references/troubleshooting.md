# Cross-cutting Troubleshooting

Use this before entering a sub-skill when the failure could be install, runtime-root, backend, credential, or external-service related.

| Symptom | Likely cause | Recovery |
|---|---|---|
| Python refuses to install or dependencies resolve to surprising versions | H2O LLM Studio expects Python 3.10 and a locked GPU-oriented stack | Use a fresh Python 3.10 environment and the repo-supported install path; do not reuse a random Python 3.11/3.12/3.13 environment for training. |
| `ModuleNotFoundError: llm_studio` | Package/source root is not on the Python path or the command is not running in the intended runtime environment | Verify the environment with `python scripts/check_environment.py --import-only`; run commands from the user's H2O LLM Studio runtime root or install the package into that environment. |
| Config construction fails with missing `prompts/`, `model_cards/`, `static/`, or `pyproject.toml` | The process is running from a directory that lacks H2O LLM Studio runtime assets | Run from a runtime root containing those assets, use Docker, or copy/mount the expected assets into the runtime working directory. |
| `torch.cuda.is_available()` is false on a GPU host | CPU-only torch wheel, driver/container GPU passthrough issue, or incompatible CUDA runtime | Check `nvidia-smi`, package wheel tags, Docker `--gpus`/NVIDIA runtime, and run the training sub-skill backend checker. |
| DeepSpeed import or `train.py -h` fails with `CUDA_HOME does not exist` or missing `nvcc` | PyTorch CUDA runtime exists but CUDA toolkit compiler is not visible | Install/use a CUDA toolkit matching the environment and set `CUDA_HOME` to the toolkit root before DeepSpeed import or training. |
| `no kernel image is available`, undefined CUDA symbol, or extension import crash | Wheel/toolkit/GPU compute capability mismatch | Match the torch/CUDA/deepspeed/bitsandbytes/flash-attn versions to the GPU and driver; disable optional flash attention when not required. |
| GPU out of memory during training | Model/backbone too large, batch/sequence length too high, precision/LoRA choices too heavy | In the training sub-skill, reduce batch size, max length, generation length, use LoRA/quantization carefully, use gradient checkpointing, adjust mixed precision, or choose a smaller backbone. |
| W&B, OpenAI judge, Hugging Face export, cloud storage, S3/Azure/H2O Drive, or Kaggle calls fail | Missing credentials, blocked network, wrong account/repo/data path, or external-service quota | Ask before using credentials. Verify tokens with a safe preflight. Avoid uploading/publishing/downloading large assets unless the user approves. |
| Keyring warning appears on app import | Host has no recommended OS keyring backend | Nonfatal for many flows; app falls back or disables keyring save option. Use settings/app sub-skill if persistent secrets are required. |
| App starts locally but remote browser cannot connect | Port/proxy/origin or timeout configuration, not necessarily model/training failure | In app-and-ui, check `H2O_WAVE_ALLOWED_ORIGINS`, Wave timeout env vars, port `10101`, proxy URL, and `H2O_WAVE_PRIVATE_DIR`. |
| Experiment directory exists but status is unclear | Training crashed, was killed, or rank 0 did not finish writing flags/artifacts | In training-and-experiments, inspect `flags.json`, `logs.log`, `charts_cache`, `checkpoint.pth`, and `validation_predictions.csv`; do not infer success from directory existence alone. |
| Prompt/export fails on a trained experiment | Missing `cfg.yaml`, checkpoint, tokenizer/backbone files, prompt templates, wrong device, or non-generation problem type | Use export-and-prompt preflight scripts before loading a model or publishing. |

## Safety boundaries

Stop and ask before:

- starting long training or UI services on public ports;
- downloading full models/datasets or running OASST/Kaggle/HF examples;
- using API keys, cloud credentials, W&B, OpenAI judge metrics, or Hugging Face publishing;
- changing system CUDA/NVIDIA drivers/container runtime;
- overwriting existing experiment outputs or modifying a user-owned Python environment.
