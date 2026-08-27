# Pretrained and foundation models

Treat checkpoints as data with a contract, not as interchangeable model files.
Record model class, channel names/order, sampling frequency, input time range,
output head, parameter format, and the source/version of the checkpoint.

For a local checkpoint:

1. Instantiate the matching backbone and task head.
2. Load with an explicit CPU `map_location` first and use `strict=False` only
   when the expected missing keys are the freshly initialized task head.
3. Fail on unexpected keys or missing backbone keys; print the counts and names.
4. Run `model.eval()` and a bounded forward pass with the exact input shape.
5. Only then freeze layers, replace the final head, or build `EEGClassifier`.

Hub-backed examples may use `huggingface_hub` and model-specific extras. They
can require network, cache space, authentication, or license acceptance. Do not
bundle a downloader or tell a future agent to run a source-repository script;
provide the repository ID, expected files, and validation logic explicitly after
an authorized user has selected that integration.

Foundation and interpolated models often depend on exact sampling/channel
metadata and may return features or structured outputs. Read the model's
constructor and output documentation, then test `return_features` and output
rank before attaching a class loss.
