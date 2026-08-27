# OCR API Reference

## When to Read

Read this when writing Python code around `pix2tex.cli.LatexOCR` or checking
what helper functions do without opening source files.

## Verified Public Objects

| Object | Signature | Notes |
|---|---|---|
| `pix2tex.cli.LatexOCR` | `(arguments=None)` | Initializes model config/checkpoint state. If `arguments` is omitted, defaults include `config='settings/config.yaml'`, `checkpoint='checkpoints/weights.pth'`, `no_cuda=True`, and `no_resize=False`. Missing checkpoints trigger automatic download. |
| `LatexOCR.__call__` | `(self, img=None, resize=True) -> str` | Accepts a `PIL.Image` or reuses the last image if `img` is omitted. Returns a post-processed LaTeX string and tries to copy it to the clipboard. |
| `minmax_size` | `(img, max_dimensions=None, min_dimensions=None)` | Resizes down to max bounds and pads up to min bounds. |
| `check_file_path` | `(paths, wdir=None) -> list[str]` | Resolves file arguments and simple globs for the CLI loop. |
| `pad` | `(img, divable=32)` | Converts to grayscale-like data, normalizes/inverts, crops non-background pixels, and pads dimensions to a multiple of 32. |
| `post_process` | `(s: str)` | Removes unnecessary whitespace while preserving text/operator constructs. |

## Argument Object Fields

The CLI builds an `argparse.Namespace` with these important fields:

- `temperature`: sampling temperature; default from CLI is `0.333`.
- `config`: config YAML path; default `settings/config.yaml` inside the package
  model directory.
- `checkpoint`: model weights path; default `checkpoints/weights.pth`.
- `no_cuda`: if true, force CPU even when CUDA is available.
- `no_resize`: skip the image-resizer model.
- `show` / `katex`: render prediction locally with TeX or online with KaTeX.
- `file`: zero or more image file paths; if absent, CLI reads clipboard or enters
  an interactive prompt.

## Checkpoint Behavior

`LatexOCR.__init__` changes into the package model directory while reading
configs and locating checkpoints. If `checkpoint` does not exist, it calls the
checkpoint downloader. Avoid model construction when offline or when downloads
are out of scope.
