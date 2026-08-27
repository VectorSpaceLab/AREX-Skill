# Wavelet Packet Troubleshooting

## When to read

Read this when packet paths, axes, or reconstruction output fail.

## Invalid path names

### Symptoms
- `IndexError: Path length is out of range.`
- `ValueError: Subnode name must be in [...]`
- `TypeError` from bad tuple path contents

### Causes
- The path extends beyond the tree's maximum decomposition depth.
- A child token is not valid for the packet class (`a/d`, `a/h/v/d`, or ND tokens).
- A tuple path contains non-string tokens.

### Recovery
- Check `maxlevel` before descending deeper.
- Use the correct packet class for the data dimensionality.
- Pass path tuples made only of valid string tokens.

## Reconstruction shape surprises

### Symptoms
- The reconstructed array is trimmed or shaped differently than expected.
- A node reconstructs to the local coefficient shape instead of the root shape.

### Causes
- Packet trees trim excess boundary coefficients back to the original input size.
- A subnode reconstruction only rebuilds the local branch.

### Recovery
- Compare the reconstructed root against the original input, not the intermediate node, when checking whole-tree correctness.
- For odd transformed axis lengths, expect trimming in the reconstructed root and branch-level outputs.

## Axis and data-shape mismatches

### Symptoms
- `ValueError` about axes or duplicate axes.
- Reconstruction errors on ND trees with custom axis subsets.

### Causes
- The axes tuple is invalid, duplicated, or longer than the input rank.
- The selected packet class does not match the intended transformed axes.

### Recovery
- Use `WaveletPacket` for 1D, `WaveletPacket2D` for two transformed axes, and `WaveletPacketND` for arbitrary axes.
- Keep axis choices stable through both construction and reconstruction.

## Next helper to run

- Run `../../scripts/check_pywavelets_install.py` to confirm that a tiny packet reconstruction still works in the installed environment.
