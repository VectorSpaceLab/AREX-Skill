# Cross-Cutting Troubleshooting

## When to read this

Read this for failures that affect more than one Deep Daze workflow: install and
import errors, missing package data, CLIP checkpoint downloads, backend choice,
headless execution, output files, and expensive-run safety.

For workflow-specific failures, also read:

- `sub-skills/runtime-and-models/references/troubleshooting.md`
- `sub-skills/cli-workflows/references/troubleshooting.md`
- `sub-skills/python-api/references/troubleshooting.md`

## Fast diagnosis

Run the safe helper before trying to generate an image:

```bash
python scripts/deep_daze_inspect.py
```

If it fails, fix import/dependency/package-data issues first. This helper does
not download CLIP checkpoints and does not instantiate `Imagine`.

## Install/import failures

Symptoms:

- `ModuleNotFoundError: No module named 'deep_daze'`
- `ModuleNotFoundError` for `torch`, `torchvision`, `siren_pytorch`,
  `torch_optimizer`, `fire`, `ftfy`, `regex`, `einops`, `imageio`, or `tqdm`
- `imagine: command not found`

Likely causes and recovery:

1. The package is not installed in the Python environment used by the agent or
   shell. Run `python -m pip install deep-daze` in that environment.
2. The console script directory is not on `PATH`. Use `python -m pip show
   deep-daze` to confirm installation, then run via the environment's script
   path or fix `PATH`.
3. A dependency installation is broken. Run `python -m pip check` and reinstall
   the missing package or Deep Daze in a clean environment.

## Missing tokenizer vocabulary

Symptoms:

- Importing `deep_daze.clip` or calling `tokenize(...)` fails while reading
  `bpe_simple_vocab_16e6.txt`.
- Tokenization works in a source checkout but fails after packaging.

Deep Daze expects the BPE file to be packaged under `deep_daze/data/`. Reinstall
from a proper wheel/source distribution that includes package data, or verify
that the installed package preserves the `MANIFEST.in` package-data behavior.
The safe inspection helpers check `tokenize('a house')` and package-data
presence.

## CLIP checkpoint downloads and cache failures

Symptoms:

- Generation hangs or fails before optimization starts.
- Errors mention URL opening, network, checksum mismatch, or a CLIP model file.
- A partially downloaded checkpoint exists in the CLIP cache.

Deep Daze downloads CLIP checkpoints lazily when `deep_daze.clip.load(model_name)`
runs, which occurs during `Imagine(...)` construction. The default cache location
is controlled by the vendored CLIP loader. Recovery steps:

1. Confirm the requested model name is one of `RN50`, `RN101`, `RN50x4`,
   `ViT-B/32`, or `ViT-L/14`.
2. Ensure network access or pre-populate the CLIP cache with a valid checkpoint.
3. If a checksum warning/error appears, remove the corrupt cached checkpoint and
   retry with a stable network.
4. Do not treat a safe import/tokenizer check as proof that checkpoint download
   and full generation will succeed.

## CPU, CUDA, ROCm, and memory expectations

Deep Daze selects `cuda` when `torch.cuda.is_available()` is true; otherwise it
uses CPU. ROCm PyTorch builds often expose compatible devices through the CUDA
API naming used by PyTorch, but the environment must be installed for that
backend.

If generation is too slow or out of memory:

- Reduce `image_width` first; `256` is the usual low-memory starting point.
- Reduce `batch_size` and compensate with a larger `gradient_accumulate_every`.
- Reduce `num_layers`/avoid `--deeper` for smoke tests.
- Use smaller `epochs` and `iterations` until the workflow is verified.
- Close other GPU workloads or use a smaller CLIP model if supported by the
  task.

The README's VRAM examples are practical guidance, not a guarantee. Always run a
small smoke generation before a long creative run.

## Headless and automated runs

Symptoms:

- `xdg-open`, desktop browser, or file-manager errors appear.
- A CLI process blocks on an overwrite prompt.

Recovery:

- Set `--open_folder=False` or `open_folder=False`.
- Use `--save_date_time=True` / `save_date_time=True` or a clean output
  directory to avoid overwrite prompts.
- Use `--overwrite=True` only when replacing the existing file is intentional.

## Prompt length and story mode

Normal CLIP text encoding has context length 77. Long prompts can fail during
tokenization. For poems, paragraphs, or stories, use story mode and save
progress frames so transitions are visible:

```bash
imagine "scene one. scene two." --create_story=True --story_separator=. --save_progress=True --open_folder=False
```

## Verification limits

The bundled helpers prove install/import/API/CLI surfaces. They deliberately do
not prove image quality, checkpoint availability, generation speed, GPU memory
fit, or creative convergence. Verify those with a bounded real generation run
only after the runtime is ready and the user accepts the compute/network cost.
