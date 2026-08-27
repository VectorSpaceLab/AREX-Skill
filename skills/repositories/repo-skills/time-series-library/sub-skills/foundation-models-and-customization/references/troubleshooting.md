# Model and Customization Troubleshooting

## Selected model is not found

Symptoms:

- `NotImplementedError: Model [Name] not found in 'models' directory.`

Fixes:

- Confirm the exact file basename under `models/`; model names are case-sensitive.
- Ensure the source tree contains `models/<Name>.py` and that the command runs from the TSLib checkout or has the checkout on `PYTHONPATH`.
- Run `scripts/inspect_tslib_models.py --models <Name>`.

## Model file imports but class is missing

Symptoms:

- `AttributeError: Module models.<Name> has no class 'Model' or '<Name>'`.

Fix:

Expose either `Model` or a class named after the file. The simplest TSLib-compatible pattern is `class Model(nn.Module): ...`.

## Optional dependency missing

Symptoms:

- `ModuleNotFoundError: No module named 'mamba_ssm'`
- `ModuleNotFoundError: No module named 'chronos'`, `timesfm`, `uni2ts`, `tirex`, or `transformers`.

Fixes:

- Decide whether the requested model family is needed. If not, switch to a core model for the task.
- For Mamba, install a CUDA/Linux wheel that matches Python, PyTorch, CUDA, and ABI; validate import before running benchmark scripts.
- For LTSM models, install the selected package only, prepare model cache/network access, and inspect whether the model file hard-codes CUDA.
- Do not treat a base TSLib install as broken solely because optional model imports fail.

## Remote-code or model-weight risk

`Sundial` and `TimeMoE` use `transformers.AutoModelForCausalLM.from_pretrained(..., trust_remote_code=True)`. Before running:

- Confirm the model source is trusted.
- Confirm network or local cache availability.
- Confirm device and memory requirements.
- Avoid executing these paths in an offline or security-sensitive task without approval.

## New model shape errors

Likely causes:

- `forward` returns the wrong shape for the task.
- `configs.enc_in`, `configs.c_out`, or `configs.pred_len` is ignored.
- Classification did not use the padding mask.
- Imputation did not accept/use the `mask` argument.

Fixes:

- For forecasting, return `[batch, pred_len, output_channels]`.
- For imputation/anomaly, return reconstruction over the input window.
- For classification, return logits `[batch, num_class]`.
- Build a tiny tensor smoke before full `run.py`.

## Augmentation is slow or fails

- DTW-based augmentations can be slow; test on a small subset first.
- Class-guided methods need label structure; they may skip samples when no same-class partner exists.
- Use one augmentation flag at a time with `--augmentation_ratio 1` while debugging.

## Contribution rejected or out of scope

The upstream project states it prefers officially published papers for new model additions. For unpublished or private models, keep the changes local or in a fork and do not assume upstream acceptance.
