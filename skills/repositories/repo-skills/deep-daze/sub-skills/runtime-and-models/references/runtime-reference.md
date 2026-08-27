# deep-daze runtime and model reference

This reference is self-contained runtime guidance for installed `deep-daze`
package environments. It avoids generation and model loading unless explicitly
called out as a potentially expensive action.

## Package identity and entry points

| Surface | Expected value | Notes |
| --- | --- | --- |
| Installed distribution | `deep-daze` | Verified package version for this skill build: `0.11.1`. |
| Python import | `import deep_daze` | Public package module name uses an underscore. |
| Public exports | `DeepDaze`, `Imagine` | Importable as `from deep_daze import DeepDaze, Imagine`. |
| Console script | `imagine = deep_daze.cli:main` | CLI startup depends on `fire`; actual generation routes through `Imagine`. |
| Required package data | `deep_daze/data/bpe_simple_vocab_16e6.txt` | Used by the tokenizer at import/tokenize time. If it is missing, tokenization cannot be trusted. |

Use the bundled helper to verify these without downloads:

```bash
python scripts/check_deep_daze_runtime.py
```

## Dependency expectations

The package expects a PyTorch image-generation stack plus text-tokenization and
CLI helpers.

| Component | Import/module | Used for | Typical failure if absent |
| --- | --- | --- | --- |
| PyTorch | `torch` | tensors, CUDA detection, CLIP model execution, optimization | `ModuleNotFoundError: No module named 'torch'` |
| torchvision | `torchvision` | CLIP preprocessing transforms | import failure while importing CLIP helpers |
| siren-pytorch | `siren_pytorch` | SIREN image generator network | generation import or construction failure |
| torch optimizer | `torch_optimizer` | default optimizer `AdamP` and alternatives | default optimizer lookup/import failure |
| Fire | `fire` | `imagine` console command dispatch | CLI entry point import failure |
| ftfy | `ftfy` | CLIP text cleanup before BPE tokenization | tokenizer import failure |
| regex | `regex` | Unicode-aware tokenizer pattern | tokenizer import failure |
| einops | `einops` | tensor rearrangement in generation internals | generation import failure |
| imageio | `imageio` | optional progress media outputs | GIF/video/progress output failure |
| tqdm | `tqdm` | progress bars and checkpoint download progress | import/progress display failure |

The distribution dependency list includes `torch>=1.10`, while the package's
JIT compatibility branch still treats Torch `1.7.1` as the only JIT-compatible
version. In modern Torch environments this normally means JIT is disabled at
`Imagine` initialization time; see [JIT behavior](#jit-behavior).

## CLIP model names and defaults

`deep-daze` bundles a CLIP loader with this model registry:

- `RN50`
- `RN101`
- `RN50x4`
- `ViT-B/32`
- `ViT-L/14`

The default `model_name` for both CLI and Python `Imagine` workflows is
`ViT-B/32`. `AdamP` is the default optimizer name.

Model names are resolved by the CLIP loader. If the value matches one of the
registered names, loading attempts to locate or download that checkpoint. If the
value is an existing checkpoint file path, loading uses that file. Otherwise the
loader raises an error listing the available model names.

## Tokenizer facts

- Tokenizer entry point: `deep_daze.clip.tokenize`.
- CLIP context length: `77` tokens.
- A single string is normalized into a batch of one.
- Verified smoke fact: `tokenize('a house').shape == (1, 77)`.
- Tokenizer initialization requires the bundled BPE vocabulary package data.
- Long text without story-mode workflow handling can exceed the 77-token CLIP
  context and raise an input-too-long runtime error.

The safe helper checks the tokenizer shape without loading any CLIP model:

```bash
python scripts/check_deep_daze_runtime.py --json
```

## Checkpoint download, checksum, and cache behavior

CLIP checkpoints are not needed for import or tokenizer smoke checks. They are
needed when code calls `deep_daze.clip.load(...)`, constructs `Imagine(...)`, or
runs `imagine ...` generation.

When a registered CLIP model name is loaded:

1. The loader uses a per-user CLIP cache, defaulting to `~/.cache/clip`.
2. The checkpoint filename is taken from the model URL.
3. The expected SHA256 checksum is encoded in the URL path.
4. If a cached file exists and its SHA256 matches, the cached file is reused.
5. If a cached file exists but the checksum does not match, a warning is emitted
   and the file is downloaded again.
6. If the final downloaded file checksum still does not match, loading raises a
   runtime error.
7. If the cache target exists but is not a regular file, loading raises a
   runtime error.

Operational implications:

- A runtime preflight should not call the loader unless network and cache writes
  are acceptable.
- In offline environments, pre-populate the CLIP cache or provide a valid local
  checkpoint path through the generation workflow's `model_name` parameter.
- If checksums fail repeatedly, remove the corrupt cached checkpoint and retry
  in a network path that does not rewrite large binary downloads.

## JIT behavior

The generation constructor accepts `jit=True` by default, but it disables JIT
when the active Torch version string does not contain `1.7.1`. When that happens
it prints:

```text
Setting jit to False because torch version is not 1.7.1.
```

This warning is expected in modern environments where `torch>=1.10` satisfies
package dependencies. Prefer passing `jit=False` in CLI/API generation workflows
if the message is noisy or if using a non-JIT local checkpoint. Do not downgrade
Torch solely to silence the warning unless the whole environment is intentionally
pinned and tested for that legacy stack.

## CPU/GPU runtime selection

`deep-daze` chooses a device with CUDA-first logic:

```text
cuda if torch.cuda.is_available() else cpu
```

Consequences:

- CUDA-capable PyTorch is the only accelerator path selected automatically by
  the package's runtime device logic.
- CPU-only PyTorch can pass import and tokenizer checks and can technically run
  parts of the workflow, but full image generation is usually impractically slow.
- Apple MPS, ROCm naming, or other accelerator backends are not selected by this
  package's device logic unless they also appear through PyTorch CUDA semantics.
- If a user expected GPU acceleration but the helper reports `cuda_available:
  false`, fix the PyTorch build, driver, container runtime, or visible GPU
  devices before generation.

## Resource guidance before generation

Generation cost is dominated by CLIP checkpoint size, selected model, image
width, batch size, gradient accumulation, epoch count, iteration count, and
whether progress media are saved.

Practical guidance:

- Start with a known model name such as `ViT-B/32`; `ViT-L/14` can require more
  memory and download/storage than smaller models.
- Reduce `image_width` and `batch_size` first when facing out-of-memory errors.
- Reduce `iterations` and `epochs` for quick trials.
- Disable GIF/video/progress media unless needed.
- Use CPU-only runs for API wiring and very small experiments only; do not treat
  a CPU generation run as a normal performance baseline.

For exact CLI flags, route to [../../cli-workflows/SKILL.md](../../cli-workflows/SKILL.md).
For programmatic constructors and generation loops, route to
[../../python-api/SKILL.md](../../python-api/SKILL.md).
