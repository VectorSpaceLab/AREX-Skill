# CLI reference

OmegaFold exposes the console script `omegafold`, installed from distribution metadata name `OmegaFold` and implemented as `omegafold.__main__:main`. If the console script is missing but the package imports, use the installed-package module fallback `python -m omegafold`.

## Command forms

```bash
omegafold INPUT_FILE.fasta OUTPUT_DIRECTORY [options]
```

```bash
python -m omegafold INPUT_FILE.fasta OUTPUT_DIRECTORY [options]
```

Prefer `omegafold` on `PATH` for installed packages and agent automation. Use `python -m omegafold` only as an installed-package fallback when the console script wrapper is missing.

## Positional arguments

| Argument | Meaning | Notes |
| --- | --- | --- |
| `input_file` | FASTA file to read | Entries use headers beginning with `>` or `:` followed by amino-acid sequence lines. |
| `output_dir` | Directory for PDB files | Created automatically by the full CLI if it does not already exist. |

## Options

| Flag | Default | Use |
| --- | --- | --- |
| `--model {1,2}` | `1` | Selects OmegaFold model weights/config. Model `2` uses the release-2 checkpoint and `make_config(2)`. Other ids fail. |
| `--num_cycle INT` | `10` | Number of optimization/recycling cycles used in input preparation and forward config. Lower values can reduce runtime, often with quality trade-offs. |
| `--subbatch_size INT` | full sequence length | Shards long-sequence execution. Smaller values reduce GPU memory but increase runtime. |
| `--device DEVICE` | auto | Explicit `cpu`, `mps`, `cuda`, or `cuda:N`. Auto-selection prefers CUDA, then MPS, then CPU. Unavailable explicit devices raise `ValueError`. |
| `--weights_file PATH` | model-specific cache path | Local checkpoint path to load. Defaults to `~/.cache/omegafold_ckpt/model.pt` for model 1 and `~/.cache/omegafold_ckpt/model2.pt` for model 2. |
| `--weights URL` | release-1 URL in parser | URL used by the loader when a checkpoint file is missing. The model selection logic chooses release-1 for `--model 1` and release-2 for `--model 2`. |
| `--pseudo_msa_mask_rate FLOAT` | `0.12` | Masking rate for generated pseudo MSAs. Keep default unless reproducing an experiment that needs a different pseudo-MSA corruption level. |
| `--num_pseudo_msa INT` | `15` | Number of generated pseudo MSA rows. Higher values can increase memory and runtime. |
| `--allow_tf32 BOOL` | `True` | Allows TF32 acceleration where Torch/CUDA supports it. Use `False` for stricter numerical reproducibility. |

## Weights and cache behavior

When full inference parses valid positional arguments, OmegaFold chooses a checkpoint URL/path from `--model` and `--weights_file`:

- `--model 1` defaults to `~/.cache/omegafold_ckpt/model.pt` and release-1 weights.
- `--model 2` defaults to `~/.cache/omegafold_ckpt/model2.pt` and release-2 weights.
- If the selected `weights_file` exists, the CLI loads it locally.
- If the selected `weights_file` does not exist and a weights URL is active, the CLI creates the cache directory and downloads the checkpoint before loading.
- If network access is not allowed, provide a pre-existing `--weights_file PATH` and verify the file before running.

`omegafold --help` is safe because `argparse` handles help before model and weight loading.

## Command templates

Basic installed CLI:

```bash
omegafold input.fasta outputs/
```

Model 2 with explicit CUDA and local weights:

```bash
omegafold input.fasta outputs/ --model 2 --device cuda --weights_file /path/to/model2.pt
```

Long sequence with lower GPU-memory pressure:

```bash
omegafold long.fasta outputs/ --device cuda --model 2 --subbatch_size 448 --num_cycle 10 --weights_file /path/to/model2.pt
```

CPU-only fallback for a tiny input when slow runtime is acceptable:

```bash
omegafold tiny.fasta outputs/ --device cpu --num_cycle 1 --subbatch_size 64 --weights_file /path/to/model.pt
```

Installed-package module fallback:

```bash
python -m omegafold input.fasta outputs/ --device mps --model 1
```

## Expected logs

Full inference logs should include these phases:

1. Loading or downloading weights.
2. Constructing `OmegaFold`.
3. Reading the FASTA file.
4. Predicting each sorted chain.
5. Saving each prediction to a `.pdb` path.
6. Final `Done!`.

A runtime failure for one sequence logs the exception, skips that chain, and continues with the next chain.
