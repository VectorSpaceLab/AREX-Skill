# Model inference troubleshooting

Use this reference when pretrained model setup, artifact planning, or sample
command construction fails. For cross-cutting installation issues that also
affect UI, projection, constraints, or training, consult the root troubleshooting
reference from the parent iGAN skill when available.

## Fast triage

1. Is the request only to build a command or URL plan? Use the bundled helpers;
   no Theano, CUDA, OpenCV, model file, or network should be required.
2. Is the model name known? Compare with the model-zoo table in
   [model-workflows.md](model-workflows.md).
3. Does the planned model file exist? Use `--check-existing` or `--check-model`.
4. Is native execution requested? Confirm legacy Python/Theano/CUDA/cuDNN/OpenCV
   requirements before running the generated command.
5. Did the failure mention projection, AlexNet, PyQt4 UI, constraint maps, or
   training data? Route to the sibling sub-skill that owns that workflow.

## Symptom: helper says the model artifact is missing

Likely causes:

- The pretrained model has not been downloaded or staged.
- The file is in a different directory from the command's `--model_file`.
- The user chose a custom model name but kept the default model-file convention.
- The model type suffix is not `dcgan_theano`.

Recovery:

```bash
python sub-skills/model-inference/scripts/igan_artifact_urls.py outdoor_64 --check-existing
python sub-skills/model-inference/scripts/build_model_command.py \
  --model_name outdoor_64 \
  --model_file models/outdoor_64.dcgan_theano \
  --check-model
```

If the artifact is still missing, download or copy the exact URL/target reported
by the planner only after network access and storage are allowed. The planner
itself never downloads.

## Symptom: `Unknown model name` or missing config function

Likely causes:

- Typo such as `outdoors_64` instead of `outdoor_64`.
- Requesting a trained custom model without adding a matching config function.
- Confusing model-zoo names with dataset names or projection/AlexNet artifact
  names.

Recovery:

- Use one of: `outdoor_64`, `church_64`, `handbag_64`, `shoes_64`,
  `hed_shoes_64`.
- For a custom model, add a compatible config with `npx`, `n_layers`, `n_f`, and
  `nc`, then use `--allow-unknown` in dry-run helpers only when you intentionally
  accept that native execution is not yet proven.
- If the task is about AlexNet or `conv4`, route to image-projection rather than
  this sub-skill.

## Symptom: `ImportError`, `ModuleNotFoundError`, or `No module named theano`

Likely causes:

- Native sample generation was attempted in a modern Python environment without
  legacy Theano.
- The command was run outside a checkout containing repo-local `model_def` and
  `lib` modules.
- Optional dependencies such as OpenCV are not installed.

Recovery:

- Use the dry-run helpers first to verify command and model-file paths.
- Run native generation only in an environment intentionally prepared for the
  legacy stack.
- Ensure the working directory contains the iGAN scripts and local modules when
  running the original sample command.
- Install OpenCV for the runtime if native writing is required; command building
  does not require it.

## Symptom: Theano CUDA/cuDNN compile failure

Likely causes:

- The original project targeted a Python2-era Theano stack with older CUDA and
  cuDNN assumptions.
- Modern CUDA drivers, NumPy versions, compilers, or Theano forks may not be
  ABI/API-compatible with the old code.
- `THEANO_FLAGS` names a GPU that is unavailable.
- cuDNN headers/libraries are not visible to Theano.

Recovery:

- Treat this as an optional native-runtime blocker, not a model-zoo planning
  failure.
- Verify hardware with a lightweight GPU probe before running Theano.
- Adjust `THEANO_FLAGS` to a real device such as `device=gpu0` only when the
  legacy stack supports it.
- If the goal is documentation or command planning, stop at the dry-run command
  and record the CUDA/Theano blocker.
- If the goal is actual image generation, recreate a compatible legacy runtime
  rather than patching random compile errors one by one.

## Symptom: `UnicodeDecodeError`, pickle load failure, or missing artifact keys

Likely causes:

- The file at `--model_file` is not a valid iGAN `.dcgan_theano` artifact.
- A partial download or HTML error page was saved as the model file.
- The artifact comes from a different model implementation or an incompatible
  training/export path.
- The artifact lacks required keys such as `gen_params` or `gen_batchnorm`.

Recovery:

- Re-plan the URL and target with `igan_artifact_urls.py`.
- Check file size and provenance before rerunning native generation.
- Replace partial or non-model files with the correct artifact.
- For custom trained models, route training/packing details to training-data and
  verify that the pack/export step produced compatible generator parameters.

## Symptom: generated image exists but colors look wrong

Likely causes:

- Confusion between RGB and BGR order at OpenCV save/display boundaries.
- A downstream viewer expects a different channel order.
- One-channel `hed_shoes_64` output was treated as RGB content.

Recovery:

- Preserve the documented sample script's final color conversion unless you have
  a controlled test image proving it is wrong for your environment.
- Check whether the output came from `hed_shoes_64`; it is a one-channel model
  intended for sketch/HED workflows.
- Route UI shadow-mode behavior to interactive-ui.

## Symptom: assertion failure in `gen_samples`

Likely causes:

- Custom code called `gen_samples` with `n` not divisible by `batch_size` while
  `z0` is omitted.
- A caller changed the documented sample count or batch size without updating
  the divisibility condition.

Recovery:

- Use the documented `n=196` and `batch_size=49` for the standalone sample grid.
- For custom API usage, set `n` to a multiple of `batch_size`, or provide `z0`
  explicitly and handle the resulting batch size behavior.

## Symptom: PyQt4, qdarkstyle, display, or UI errors

Likely causes:

- The user is launching the interactive interface, not the sample-generation
  script.
- The environment lacks a desktop display or PyQt4 packages.
- Remote desktop/VNC latency or display artifacts are involved.

Recovery:

- Route the task to interactive-ui.
- Keep this sub-skill focused on model artifact setup and standalone sample
  command construction.

## Symptom: Lasagne, AlexNet, HOG, SciPy optimizer, or predictor errors

Likely causes:

- The user is running image-to-latent projection rather than random samples.
- The model file lacks predictor parameters required by some projection modes.
- AlexNet artifacts are missing.

Recovery:

- Route the task to image-projection.
- Use this sub-skill only to confirm the base DCGAN model artifact and general
  `dcgan_theano.Model` facts.

## Symptom: Fuel, HDF5, dataset, cache, or pack-model errors

Likely causes:

- The user is preparing data, training a model, estimating batchnorm, training a
  predictor, or packing a custom model.
- Large external datasets or GPU training are involved.

Recovery:

- Route the task to training-data.
- Return here only after a compatible `*.dcgan_theano` artifact exists and the
  task is inference/sample generation.

## Reporting unresolved blockers

When native generation is not run or fails for environmental reasons, record a
precise blocker such as:

- `MISSING_MODEL_ARTIFACT: models/outdoor_64.dcgan_theano not present; URL plan emitted; no network download performed.`
- `BLOCKED_LEGACY_THEANO_CUDA: dry command built, but host lacks compatible Theano CUDA/cuDNN stack.`
- `BLOCKED_OPENCV_RUNTIME: command built, but native sample writing would require cv2.`
- `ROUTED_IMAGE_PROJECTION: request referenced AlexNet/solver; see image-projection.`

Do not mark the model workflow as verified by native execution unless the sample
command exits successfully and writes the requested image.
