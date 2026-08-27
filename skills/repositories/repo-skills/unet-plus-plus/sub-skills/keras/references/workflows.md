# Keras workflows

## 1. Build a tiny segmentation model

Use the public builders with `encoder_weights=None` when you only need a shape
or import smoke.

Recommended order:

1. Pick the architecture: `Unet`, `Nestnet`, `Xnet`, `FPN`, or `PSPNet`.
2. Pick a backbone name from the bundled catalog.
3. Confirm the input shape is large enough for the selected backbone/head.
4. Build the model.
5. Optionally compile and fit on your own data.

The bundled smoke script follows this pattern on tiny inputs.

## 2. Prepare custom data for the Keras stack

The repository's example scripts expect image tensors and masks already shaped
for the chosen model family.

Guidance:

- Normalize the image range to match the chosen preprocessing helper.
- Keep channels in the order expected by the backbone.
- Check whether the model uses sigmoid or softmax activation.
- Confirm the number of classes before compiling.

## 3. Use BRATS2013 as a reference workflow

`BRATS2013_application.py` shows how the legacy stack handled a large medical
imaging application.

Use it to understand:

- how the repo loaded `.npy` arrays,
- how the architecture/backbone/init flags are threaded through the app,
- how a training loop and evaluation loop were wired,
- what kinds of output files the legacy workflow writes.

Do not treat it as a cheap smoke test. It is dataset-bound and long-running.

## 4. Choose preprocessing correctly

For image input normalization, call `get_preprocessing(backbone)`.

Typical workflow:

1. Decide the backbone.
2. Fetch the matching preprocessing function.
3. Apply it before feeding the model or fine-tuning.

## 5. Select the right architecture for the job

- `Unet` is the default simple segmentation route.
- `Nestnet` and `Xnet` are the nested skip-connection variants.
- `FPN` is useful when the user wants a feature-pyramid decoder.
- `PSPNet` is the strictest on input size and divisibility.

## 6. Use the smoke helper before deeper debugging

Run `scripts/check-segmentation-models.py` when you need a quick confirmation
that the legacy stack can still build the core models in the current
environment.

## 7. Native evidence to remember

The repository also ships a network-dependent ImageNet test under the
classification-models bundle. Keep it as reference-only unless the user
explicitly wants a networked verification path.
