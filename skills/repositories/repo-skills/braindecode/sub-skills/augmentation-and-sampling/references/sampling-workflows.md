# Sampling workflows

## Batch augmentation

Start with a `TensorDataset` or a small window dataset and one deterministic
transform. Verify one batch before connecting it to `EEGClassifier`. Keep clean
samples first when `n_augmentation > 0`; this makes the expansion and label
alignment observable. Use a smaller batch if device memory is limited.

## Sequence sampling

Use `SequenceSampler` for temporally ordered windows when a model needs context.
Confirm that the sequence length, stride, trial boundaries, and labels are
available. Do not let a sequence cross a subject/session split.

## Relative positioning and self-supervision

Relative-positioning samplers pair windows from the same recording according to
temporal relationships. Self-supervised samplers may return pairs or tuples
rather than ordinary class labels. Inspect a sample and adapt the model/loss
contract before using a classifier wrapper.

All samplers should be tested with a tiny metadata fixture first. Network-backed
sleep or corpus examples are evidence for workflow intent but are not required
for a local smoke check.
