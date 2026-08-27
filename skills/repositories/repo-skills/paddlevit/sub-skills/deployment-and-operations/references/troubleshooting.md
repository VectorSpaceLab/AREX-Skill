# Safe operational diagnosis

Classify the first failing layer before changing code or installing anything.
The goal is a smallest reproducible observation, not a blind retry.

## Triage matrix

| Symptom | First read-only checks | Likely boundary | Safe next action |
|---|---|---|---|
| `ModuleNotFoundError: config` or wrong builder | `pwd`, model directory, file names, `sys.path` from the intended process | source-root/import | Re-run from the one selected model directory; do not combine model roots. |
| YAML not found/unknown key | YAML path, `BASE` paths relative to YAML, parser fields | config | Correct an explicit path or key; do not download a config. |
| checkpoint not found | regular-file check and manifest, absolute path, extension | artifact/path | Ask for the intended checkpoint or stop; do not fabricate/download one. |
| `libcudnn`, `libcuda`, or CUDA loader error | `check_paddlevit_environment.py`, Paddle version/build, visible devices | Python/backend loader | Keep the original error; repair the private environment outside the public skill, then rerun the probe. |
| Paddle imports but CUDA tensor fails | compiled-CUDA flag, device count, tiny tensor/layer | backend compatibility | Use CPU only for parser/import evidence; do not make GPU claims. |
| inference import fails | `check_paddle_inference.py`, version and artifact manifest | Paddle Inference installation/artifacts | Separate API import from model compatibility; do not rename files. |
| `paddle.jit.to_static` fails | model eval mode, input spec, dynamic shape/indexing, functional ops | model graph/export | Reproduce with optimizations off and a tiny input; patch only the owning model. |
| predictor input/output mismatch | input names, expected NCHW shape/dtype, output names | static contract | Inspect handles and manifest; compare against export config. |
| accuracy collapse after export | deterministic dynamic/static batch, preprocessing manifest, dtype | parity/data | Match resize/crop/RGB/normalization before changing weights. |
| spawn hangs/NCCL error | visible devices, world size, one-GPU run, worker logs | distributed runtime | Stop and reduce to one/two devices; do not loop unbounded launches. |
| AMP NaN or unsupported op | same batch in FP32, GPU family, scaler path | precision/model op | Keep FP32 baseline; make AMP opt-in and model-specific. |
| quantized artifact rejected | distinguish `.pd*` prefix from `__model__`/`__params__` directory | PaddleSlim format | Use the matching runtime and a new output; do not mix formats. |
| ported model differs | mapping/buffers, Linear transpose, eval mode, batched allclose | optional conversion | Review mapping manually; missing torch/timm is an optional gap. |

## Missing CUDA or cuDNN

A machine can expose an NVIDIA device and still fail because the Paddle wheel,
CUDA runtime, driver, or cuDNN loader is incompatible or not discoverable.
Separate these observations:

1. Python can import `paddle`.
2. Paddle was compiled with CUDA.
3. A device is visible and a tiny tensor/layer can execute.
4. cuDNN-dependent model operations work.
5. NCCL multi-process communication works.

Only the relevant successful observation supports a claim. The construction host
needed a private cuDNN runtime-loader setup for its smoke; that is an
installation fact, not a portable PaddleViT requirement. Do not publish
absolute library paths, shell startup edits, cache locations, or secrets. Ask
the environment owner to repair/activate the correct runtime and rerun the
read-only probe. Do not solve a backend failure by silently switching to CPU
when the requested operation is GPU-specific.

## Artifact safety

Use `validate_checkpoint_manifest.py` to inspect regular files and sizes without
loading arbitrary checkpoint serialization. It does not prove that parameters
match a model. Keep dynamic checkpoint files (`.pdparams`) separate from static
export files (`.pdmodel`, `.pdiparams`, `.pdiparams.info`) and from PaddleSlim
quantized files. Treat a manifest as evidence of presence, not correctness.

Never diagnose by:

- downloading an absent model, dataset, or dependency;
- deleting or overwriting checkpoints/exports;
- running a shell string assembled from untrusted paths;
- copying private environment loader paths into a command or report;
- retrying a hung multi-process job without stopping its workers;
- declaring accuracy from random predictor input.

## Escalation record

For any unresolved issue, retain:

```text
commit/model directory:
entry script and exact argv:
working directory:
config + BASE chain:
checkpoint/export manifest:
Python, Paddle, CUDA/backend observations:
first error and full traceback location:
what was tried (read-only first):
next owner/action:
```

This makes a later repair reproducible and prevents a successful import from
being mistaken for a successful model run.

## Evidence boundary

Primary evidence: the PaddleViT configuration, AMP, multi-GPU, export,
prediction, quantization, and porting documents; representative export and
multi-GPU scripts; and `CONTRIBUTING.md` for test/review expectations. The
English prediction path named by the task is absent in this checkout, so the
available Chinese prediction document is the source for that boundary.
