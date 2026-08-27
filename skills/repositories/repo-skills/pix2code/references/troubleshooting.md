# pix2code Troubleshooting

## Purpose

Read this when setup, data preparation, model artifact validation, sampling, or DSL compilation fails in ways that cross workflow boundaries.

## Legacy dependency failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No matching distribution found for tensorflow==1.4.0` | Python is too new or the package index no longer exposes a compatible wheel. | Use an isolated legacy Python 3.6 environment for inspection. If the exact TensorFlow pin is unavailable, document the substitution and avoid claiming paper-result verification. |
| `No matching distribution found for opencv-python==3.3.0.10` | The old OpenCV wheel is unavailable from the current index. | Try a nearby old OpenCV wheel such as a 3.4.x release for data/image preprocessing checks, or install OpenCV through Conda. Record the substitution. |
| TensorFlow imports with a compiled-extension warning | Old TensorFlow binary was built against older compile-time assumptions. | If import succeeds, use it only for inspection or tiny smoke checks. Do not treat this as robust production support. |
| Keras imports a different backend or version | The environment has a modern Keras/TensorFlow stack shadowing historical pins. | Run `python scripts/check_pix2code_environment.py --include-ml` in the target environment and create a clean legacy prefix if versions are inconsistent. |

## Missing data or trained artifacts

- The official dataset is stored as split zip parts. Do not assume `datasets/<platform>/all_data` exists until the archive has been reconstructed and unpacked.
- Training creates model outputs in a user-provided output directory. Sampling requires `pix2code.json`, `pix2code.h5`, `meta_dataset.npy`, and `words.vocab` to coexist.
- The old shell helper expected pretrained results in a `results/<target>_results` directory that is not present in this checkout. Prefer explicit artifact validation and documented sampling commands instead of running that helper.

## Python path and script-location errors

Original source scripts assume they are launched from `model/` or `compiler/` so that imports like `from classes...` resolve. The bundled helper scripts avoid that assumption. If the user insists on original scripts, tell them to run from the expected source directory and make clear that this is a checkout-maintenance action, not a portable skill workflow.

## Research-code limitations

- The README states that pix2code is experimental and not intended for real UI code generation.
- Paper accuracy was measured on DSL tokens, not visual correctness of compiled output.
- Full training is expensive and dataset-specific; a tiny fixture check validates mechanics only.
- DSL compilers insert random placeholder text and IDs. Use deterministic seeds or post-process outputs if a test needs stable strings.
