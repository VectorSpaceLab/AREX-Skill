# Troubleshooting

This reference covers cross-cutting tensorboardX issues that affect more than one sub-skill.

## Import and package mismatch

### Symptom
- `ImportError` or `ModuleNotFoundError` when importing `tensorboardX`
- the package imports, but the expected `SummaryWriter` or `GlobalSummaryWriter` symbol is missing

### Likely cause
- the package is not installed into the Python you are using
- the editable install is stale
- another `tensorboardX` on `PYTHONPATH` is shadowing the intended install

### First fix
- reinstall the package in the active environment
- rerun the bundled inspection helper
- confirm `from tensorboardX import SummaryWriter` works before looking at a deeper workflow

## Event files do not appear

### Symptom
- TensorBoard shows an empty run
- there is no `events.out.tfevents.*` file

### Likely cause
- the writer was not closed or flushed
- the run used `write_to_disk=False`
- the logdir is not the one TensorBoard is reading

### First fix
- use a context manager or call `flush()` and `close()`
- confirm the chosen logdir exists and matches `tensorboard --logdir <logdir>`
- if the workflow intentionally disables disk writes, do not expect a log file

## Optional dependency errors

### Common symptoms
- image or figure helpers complain about Pillow or matplotlib
- audio helpers complain about `soundfile`
- video helpers complain about `moviepy` or `imageio`
- graph/projector helpers complain about `torch` or `onnx`

### First fix
- install only the dependency for the route you are using
- do not treat a scalar-only install as proof that media or graph workflows are ready
- check the relevant sub-skill reference for the exact data shape or file-path contract

## Remote and credentialed integrations

### Symptom
- `s3://` or `gs://` paths fail
- Comet forwarding does nothing or raises configuration errors
- a cloud test asks for credentials

### First fix
- keep cloud integrations disabled unless the user explicitly needs them
- use the local or mock path first
- treat `boto3`, `moto`, `comet-ml`, and `google-cloud-storage` as explicit opt-in dependencies

## TensorBoard reader or protobuf issues

### Symptom
- event readers or tests complain about protobuf or TensorBoard stubs
- graph tests fail to import TensorBoard compatibility shims

### First fix
- install `tensorboard` alongside the package when the workflow needs TensorBoard readers or graph helpers
- if protobuf conflicts appear, align the dependency set for the active environment instead of mixing unrelated versions

## Where to go next

- Scalar, hparam, logdir, and event-file issues: [../sub-skills/logging-core/SKILL.md](../sub-skills/logging-core/SKILL.md)
- Image/audio/video/text/mesh issues: [../sub-skills/rich-media-summaries/SKILL.md](../sub-skills/rich-media-summaries/SKILL.md)
- Graph and projector issues: [../sub-skills/graph-and-embedding-plugins/SKILL.md](../sub-skills/graph-and-embedding-plugins/SKILL.md)
- Global writer, cloud, and Comet issues: [../sub-skills/remote-and-parallel-integrations/SKILL.md](../sub-skills/remote-and-parallel-integrations/SKILL.md)
