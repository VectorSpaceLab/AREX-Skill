# Checkpoint format

A usable Walk These Ways policy run is a directory with a configuration
snapshot and a `checkpoints/` directory. The checked-in pretrained run was
used only as filename/format evidence; generated run data is not part of this
skill.

## Required files

```text
<run>/
├── parameters.pkl
└── checkpoints/
    ├── ac_weights_last.pt
    ├── body_latest.jit
    └── adaptation_module_latest.jit
```

Training also emits iteration-numbered state dictionaries such as
`ac_weights_000400.pt` and video/metric files, but those are not required for
pretrained TorchScript playback. At each save interval the numbered state
file is duplicated to `ac_weights_last.pt`; the final loop performs the same
save. The exact iteration number is a format clue, not a guarantee about
training progress.

## Artifact roles and tensor contracts

| Artifact | Role | Contract |
|---|---|---|
| `parameters.pkl` | trusted configuration snapshot | Pickle containing a `Cfg` entry in the source workflow; never load untrusted pickle data |
| `ac_weights_last.pt` | Python actor-critic state dict for resume/reconstruction | State dict must match the selected PPO/PPO-CSE class, hidden dimensions, observation/history widths, privileged width, and action count |
| `adaptation_module_latest.jit` | exported CPU adaptation module | CSE: `(B, 2100) -> (B, 2)` for the checked-in `70/2/2100/12` policy |
| `body_latest.jit` | exported CPU actor body | CSE: `(B, 2102) -> (B, 12)` because 2100 history values plus 2 latent values are concatenated |

The body is a script of `actor_body` only, not a full `ActorCritic`. The
adaptation module is scripted separately. Playback must run adaptation first,
concatenate `[obs_history, latent]` along the final dimension, and then call the
body. Do not feed the 70-scalar current observation directly into the exported
CSE body, and do not feed a 70-scalar frame where a 2100-value flattened history
is required.

For ordinary PPO, inspect the selected actor-critic source and export contract
before assuming the CSE widths; the repository contains both variants and they
do not have interchangeable actor inputs. A state dict alone cannot establish
that a configuration matches.

## Safe integrity and compatibility checks

Before use, check:

- all required files are present and are regular files;
- no path escapes the caller-selected run directory;
- file sizes are non-zero and the run is not a partial temporary directory;
- `parameters.pkl` is trusted and its presence is reported without automatic
  unpickling by safe tooling;
- optional TorchScript inspection can load each JIT file in a subprocess and
  report metadata, but must not run a simulator or mutate files;
- a synthetic finite tensor test confirms the expected input/output widths when
  Torch is available;
- the state dict and JIT exports were generated from the same effective config.

The bundled `inspect_checkpoint_layout.py` is deliberately conservative: it
checks names, ordinary file metadata, optional iteration files, and optional
TorchScript load/forward metadata. It never writes, extracts, unpickles
`parameters.pkl`, calls network services, or depends on the original checkout.

## Mismatch interpretation

- Missing `body_latest.jit`: playback cannot produce actions even if the state
  dict exists.
- Missing `adaptation_module_latest.jit`: CSE/RMA playback cannot produce the
  latent and must stop; do not substitute zeros.
- Missing `ac_weights_last.pt`: playback may still be possible from the two JIT
  files, but resume/reconstruction is not supported by the complete run
  contract.
- Present files with incompatible widths: treat as a hard mismatch, not a
  warning. Locate the matching `parameters.pkl` and model architecture or
  regenerate all exports together.
- A readable file that fails TorchScript load: treat as corrupt/incomplete;
  do not rename or overwrite it automatically.

Model weights and generated experiment data remain caller-owned artifacts and
must not be copied into this runtime skill.
