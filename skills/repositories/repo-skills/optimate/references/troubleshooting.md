# Cross-Cutting Troubleshooting

## Common failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError` for one of the OptiMate packages | The package family is not installed in the active Python or the wrong environment is active. | Install the matching package family and rerun the bundled probe script. |
| `torch.cuda.is_available() == False` on a GPU host | CPU-only torch, incompatible wheel, or driver mismatch. | Fix the torch/CUDA pairing before debugging the higher-level package. |
| `ImportError: cannot import name 'Generator' from 'collections'` | Forward-Forward source uses an old Python import path. | Use Python 3.9 or patch the import to `collections.abc.Generator`. |
| ChatLLaMA import errors mentioning `deepspeed`, `pkg_resources`, `Accelerator`, or `setuptools` | The RLHF stack needs a compatible pin set. | Check the ChatLLaMA sub-skill troubleshooting page before broad upgrades. |
| Config path or JSON/YAML schema errors | The package expects a structured config/data file. | Run the sub-skill validator script for that workflow. |
| Compiler/backend install failures | The backend is optional and platform-specific. | Read the NebullVM backend sub-skill instead of retrying blindly. |

## Where to look next

- Speedster workflow issues -> `sub-skills/speedster-optimization/references/troubleshooting.md`
- NebullVM backend issues -> `sub-skills/nebullvm-backends/references/troubleshooting.md`
- Forward-Forward compatibility -> `sub-skills/forward-forward-training/references/troubleshooting.md`
- OpenAlphaTensor config/runtime issues -> `sub-skills/open-alpha-tensor/references/troubleshooting.md`
- ChatLLaMA data/config/runtime issues -> `sub-skills/chatllama-rlhf/references/troubleshooting.md`
