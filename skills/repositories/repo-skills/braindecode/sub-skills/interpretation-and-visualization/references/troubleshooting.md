# Interpretation troubleshooting

- **Captum import error**: install the visualization extra and verify Captum
  separately; use `amplitude_gradients` or a plain PyTorch gradient smoke when
  Captum is intentionally absent.
- **No gradients or wrong attribution target**: call `model.eval()`, ensure the
  input is a floating leaf requiring gradients, avoid `torch.no_grad()`, and
  provide one valid integer target per batch item.
- **Unexpected attribution shape**: inspect whether the selected method is
  input-space or layer-space; interpolate/squeeze only after recording the
  original axes.
- **NaN/empty frequency map**: check finite input/model output, filter size,
  sampling rate, and a non-degenerate input. Validate with a known frequency
  fixture.
- **Topomap montage error**: channel names, types, order, and positions must
  match the input. Set a montage or provide finite coordinates before plotting.
- **Headless/display failure**: select a non-interactive backend, save to an
  explicit writable path, and avoid `plt.show()` in automated jobs.
- **Overinterpretation**: compare methods and perturbations; a single gradient
  map is not a stable explanation or a causal result.
