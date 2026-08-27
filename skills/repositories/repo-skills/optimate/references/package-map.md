# Package Map

| Distribution | Import root | Main workflow | Sub-skill |
| --- | --- | --- | --- |
| `speedster` | `speedster` | Inference optimization, save/load, telemetry, and backend filtering | `speedster-optimization` |
| `nebullvm` | `nebullvm` | Data/device handling and backend selection | `nebullvm-backends` |
| `forward_forward` | `forward_forward` | Forward-Forward training | `forward-forward-training` |
| `OpenAlphaTensor` | `open_alpha_tensor` | AlphaTensor-style training/configuration | `open-alpha-tensor` |
| `chatllama-py` | `chatllama` | ChatLLaMA RLHF preparation and training | `chatllama-rlhf` |

## Notes

- The repository is a collection of related packages, not a single import tree.
- `open_alpha_tensor` and `chatllama` are the public import roots; their training CLIs live under the same bundled skill tree.
- Python 3.9 is the safest baseline for Forward-Forward imports because the source-era code still touches `collections.Generator`.
