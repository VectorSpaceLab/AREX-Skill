# Cross-cutting troubleshooting

## Import fails inside `taming.models.vqgan`

Symptom:

```text
ModuleNotFoundError: No module named 'pytorch_lightning.utilities.distributed'
```

Likely cause: `taming-transformers-rom1504` expects the older PyTorch Lightning 1.x module layout. Modern Lightning 2.x removed that import path.

Recovery:

1. Use a private environment, not a shared base environment.
2. Install a Lightning 1.x version compatible with the package, for example `pytorch-lightning<1.8`.
3. Run `python -m pip check` and then `python -c "import dalle_pytorch"` again.

## `OpenAIDiscreteVAE` fails before downloading weights

Symptom:

```text
AssertionError: torch version must be <= 1.10 in order to use OpenAI discrete vae
```

Likely cause: the source intentionally guards OpenAI's released VAE wrapper to torch 1.10-era behavior.

Recovery choices:

- Use a trained local `DiscreteVAE` checkpoint and pass it to DALL-E training.
- Use `VQGanVAE` with explicit model/config paths.
- Create a separate legacy environment with torch `<=1.10` only if the user specifically needs OpenAI's VAE wrapper and accepts the old dependency stack.

Do not silently downgrade a user's working torch environment.

## Training or generation script fails with CUDA errors

Symptoms include:

- `AssertionError: Torch not compiled with CUDA enabled`
- `RuntimeError: CUDA error: no kernel image is available`
- `RuntimeError: Found no NVIDIA driver`
- script calls `.cuda()` even for tiny fixtures

Likely cause: the historical helpers expect CUDA and do not expose a CPU switch. They also write checkpoints/images and may use W&B.

Recovery:

1. Verify `python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"`.
2. If CUDA is unavailable, use API-level CPU smokes or rewrite a minimal training loop instead of running the helper script.
3. If CUDA is available but kernels fail, match torch/CUDA wheel, driver, and GPU compute capability.
4. For DeepSpeed/Apex/Horovod, route to `sub-skills/distributed-and-backends/SKILL.md`.

## W&B blocks or prompts during training

The training helpers use W&B for experiment tracking and artifact logging. If the user does not want network/account side effects:

- ask before running a full training job;
- use W&B offline/disabled settings appropriate for their environment;
- keep smoke tests to parser/API checks instead of launching training.

## Text is too long for the tokenizer context

Symptom:

```text
RuntimeError: Input ... is too long for context length ...
```

Recovery:

- Pass `truncate_text=True` in API calls or `--truncate_captions` in DALL-E training commands.
- Increase `text_seq_len` only if the model/checkpoint is being created with the same length; do not change it when resuming a checkpoint with fixed `hparams`.

## Image/text folder appears empty

Symptoms:

- `assert len(ds) > 0, 'dataset is empty'`
- no paired examples despite images and text files existing

Likely causes:

- image and `.txt` stems do not match exactly;
- files are nested differently but names collide;
- captions are empty lines only;
- unsupported extension.

Recovery:

```bash
python sub-skills/dalle-training/scripts/validate_image_text_folder.py /path/to/image-text-data --strict
```

Use the validator result to fix missing text, missing images, empty captions, or unsupported files before training.

## Checkpoint/VAE mismatch during generation

Symptom:

```text
you trained DALL-E using <class> but are trying to generate with <other class>
```

Recovery:

- Inspect the checkpoint's `vae_class_name`, `vae_params`, and `hparams` keys.
- Pass `--taming` plus matching VQGAN model/config paths only when the checkpoint was trained with `VQGanVAE`.
- Use a standard saved DALL-E checkpoint for generation; DeepSpeed ZeRO directories may need consolidation before ordinary generation.

## Sparse attention import or runtime failure

Likely causes:

- `attn_types` includes `sparse` but DeepSpeed sparse attention or compatible `triton<1.0` is not installed;
- source-built ops do not match torch/CUDA;
- the task only needs axial/conv-like sparse attention, which is implemented in the package and does not require DeepSpeed sparse attention.

Recovery: route to `sub-skills/distributed-and-backends/references/distributed-backends.md` and install only the backend actually selected by the workflow.
