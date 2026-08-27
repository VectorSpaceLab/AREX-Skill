# Image Projection Troubleshooting

Use this guide when `iGAN_predict.py` or a planned projection run fails. Start
from the visible symptom, then check the likely cause and recovery steps.

## Legacy Python and Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError: No module named theano` | The legacy Theano dependency is not installed in the active environment. | Use an environment prepared for old Theano. Do not treat modern PyTorch/JAX installs as substitutes. |
| `ImportError: No module named lasagne` | Lasagne is required by AlexNet and model layers. | Install a Lasagne version compatible with the selected Theano version, or mark native projection blocked. |
| `ImportError: No module named scipy` or `No module named PIL` | SciPy optimization and PIL/Pillow image IO are required. | Install SciPy and Pillow in the runtime environment. |
| `ImportError: No module named theano_utils` while touching HOG code | Python 2 implicit relative import assumptions in the HOG module can break in Python 3 package execution. | Prefer the default AlexNet `conv4` path. For a custom HOG path, patch imports deliberately and revalidate. |
| Syntax or division issues around `BS / 2` or `is` comparisons | Python 2 era code running on modern Python. | Use the project's intended Python 2 style environment when possible; otherwise treat Python 3 execution as a porting task, not a verified native run. |

Projection itself does not require PyQt4 or qdarkstyle. Those are UI workflow
dependencies. OpenCV and Fuel are also not direct projection requirements, though
they may appear in adjacent model, constraint, or training workflows.

## Artifact and Path Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `IOError`, `FileNotFoundError`, or pickle load failure for `models/shoes_64.dcgan_theano` | The DCGAN model file is missing or `--model_name`/`--model_type` derived the wrong default path. | Build a dry command, confirm the planned `--model_file`, and route model-zoo acquisition to the model-inference sub-skill. |
| Error loading `models/caffe_reference_conv4.pkl` | AlexNet `conv4` pickle is missing. | Run the bundled planner with `--layer conv4`, then let the user perform any approved download manually. |
| Error loading `lib/ilsvrc_2012_mean.npy` | The iGAN library support file is missing from the runtime checkout. | Restore the local library file set or use a complete checkout/equivalent distribution. |
| Input image cannot be opened | Path is wrong, file is not an image, or the image mode is unsupported by PIL/Pillow. | Verify the path and convert to a standard RGB PNG before projection. |
| Output file overwrites input or has a surprising name | Default output is a literal `.png` string replacement. | Provide explicit `--output_image`, especially for JPEGs or filenames without `.png`. |

Use [../scripts/build_projection_command.py](../scripts/build_projection_command.py)
to make all derived paths visible before native execution.

## Solver and Predictor Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `KeyError: 'predict_params'` or missing predictor arrays | The DCGAN model was packed without trained predictor parameters. | Use a model known to include predictor params, or route predictor training/packing to the training-data sub-skill. |
| `TypeError: 'NoneType' object is not subscriptable` inside predictor batchnorm | `predict_batchnorm` is absent even though predictor compilation was attempted. | Use a packed model with `predict_batchnorm`; downloading AlexNet will not fix this. |
| `UnboundLocalError` or no reconstruction for a solver string | Solver value was not one of `cnn`, `opt`, or `cnn_opt`. | Validate solver choices with the command builder before running. |
| `cnn` runs but reconstruction quality is poor | Predictor is fast but approximate, or the image is outside the model's training distribution. | Try `cnn_opt` if optimization dependencies are available, and choose a model matching the input domain. |
| `opt` unexpectedly fails due to predictor setup | The native setup compiles the predictor before the solver dispatcher. | Prefer a packed model with predictor data. If the user owns the code, patch setup to compile predictor only for `cnn`/`cnn_opt` and revalidate. |

Remember: AlexNet `conv4` is the feature-loss network. It is separate from the
DCGAN predictor network. Missing predictor params must be fixed in the DCGAN
model lifecycle, not by downloading AlexNet.

## Theano, CUDA, and cuDNN Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `theano.sandbox.cuda` errors | The code targets old Theano CUDA APIs. | Use a compatible legacy Theano/CUDA/cuDNN stack or mark native projection unavailable. |
| cuDNN compile/link failures | CUDA/cuDNN versions are too new, missing, or incompatible with the Theano build. | Check `THEANO_FLAGS`, CUDA paths, and cuDNN installation; do not claim verification on a modern incompatible host. |
| Very slow compile or projection | Theano graph compilation and L-BFGS-B are expensive; CPU fallback is not real-time. | Warn the user, use `cnn` only if predictor params exist, or defer native execution to a GPU machine. |
| GPU out-of-memory or device unavailable | Wrong `device=` flag, no visible GPU, or another process uses memory. | Change `device=gpu0` to the available device, reduce concurrent runs, or run only dry planning. |
| Remote server display warnings | Projection CLI does not need PyQt4 display, but shared environment notes may mention VNC for UI. | Do not require `$DISPLAY` for projection; route UI launch problems to interactive-ui. |

The documented environment was a GPU-era stack, not a modern universal Python
package. Treat CUDA/Theano failures as backend compatibility failures unless a
known-good legacy environment is available.

## AlexNet and HOG Feature Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| AlexNet load fails for a layer other than `conv4` | The requested pickle target does not exist or the native CLI was modified. | Use `conv4` for the standard workflow; use the planner for other layers only when maintaining a custom script. |
| Shape mismatch in AlexNet parameters | The pickle layer does not match the network layer being loaded. | Align `caffe_reference_<layer>.pkl` with the exact feature layer. |
| HOG path fails with CUDA convolution or import errors | HOG is an internal branch relying on old Theano CUDA and Python 2 imports. | Avoid HOG for standard projection. If required, treat it as custom source work and test separately. |

## Image and Domain Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Reconstruction has wrong object category | The selected model was trained on a different domain. | Choose a model whose training domain matches the input, such as a shoe model for shoe images. |
| Reconstruction loses details | The GAN latent space and 64 x 64 model resolution limit fidelity. | Set expectations: projection searches for a plausible GAN reconstruction, not pixel-perfect inversion. |
| Color shifts after projection | AlexNet preprocessing, GAN normalization, and generator domain bias can change colors. | Validate with a domain-matched model and compare solvers. |
| Aspect ratio is preserved but details are blurred | The script resizes to square model resolution and back. | Use higher-resolution/custom models only if the repository has a compatible config and model file. |

## Safe Recovery Order

1. Rebuild the command with `build_projection_command.py` and verify solver, model, input, and output paths.
2. Plan AlexNet `conv4` with `igan_alexnet_urls.py`; do not assume AlexNet is present.
3. Confirm the DCGAN model file is domain-matched and contains predictor data.
4. Confirm Theano/Lasagne/SciPy/Pillow imports in the intended runtime.
5. Confirm CUDA/cuDNN compatibility only if a native GPU run is required.
6. Run native projection only after missing artifacts and backend constraints are resolved or explicitly accepted as unknown.

## Quick Triage Phrases

- "Dry-run only": use bundled helpers; no GPU, no network, no model loading.
- "Artifact missing": report exact target and route downloads/training to the owning sub-skill.
- "Backend blocked": old Theano/CUDA stack is absent or incompatible.
- "Predictor missing": DCGAN model lacks packed predictor params; AlexNet does not solve it.
- "Domain mismatch": command can run, but reconstruction quality is limited by the chosen GAN model.
