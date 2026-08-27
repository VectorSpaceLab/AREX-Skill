# Interpretation workflows

Put a trained or tiny test model in `eval()` mode and use a detached clone of
an input with `requires_grad_(True)`. For class attribution, pass one target
index per batch item and check the returned tensor shape before reducing over
time or channels. Use a zero baseline only when it is meaningful for the
signal's scaling; otherwise use a documented reference.

For frequency gradients, keep the model and input on one device and relate
frequency bins to `sfreq`. A simple sinusoidal or known convolution filter is a
useful sanity fixture.

For channel maps, set a standard MNE montage or explicit channel locations and
verify that positions are finite/non-zero. In a headless environment select an
Agg-like backend before importing pyplot and save rather than displaying.

Attribution is a sensitivity diagnostic, not proof of causal importance. Repeat
across seeds, subjects, or perturbations before making scientific claims.
