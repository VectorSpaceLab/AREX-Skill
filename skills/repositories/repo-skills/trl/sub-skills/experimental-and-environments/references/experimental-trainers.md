# Experimental Trainers

`trl.experimental` is a shipped but unstable namespace for fast iteration. Treat every import from it as opt-in incubating behavior: APIs may change or be removed in patch releases, fixes may lag stable trainers, and public examples should mention the warning and migration risk.

## Stability Contract

- Importing any `trl.experimental` module emits `TRLExperimentalWarning` unless `TRL_EXPERIMENTAL_SILENCE=1` is set.
- Prefer stable top-level trainers when the user's task can be solved without experimental features.
- Pin TRL and key dependencies in reproducible workflows; avoid promising compatibility across minor/patch updates.
- Do not silently move code from experimental to stable imports; check whether the target trainer actually graduated.

## Trainer Map

| Trainer family | Import pattern | Typical dataset/use case | Notes |
| --- | --- | --- | --- |
| A2PO | `trl.experimental.a2po` | Verifiable binary rewards | Assumes rewards in `{0, 1}` for A*-PO-style training. |
| BCO | `trl.experimental.bco` | Unpaired preference data | Binary classifier objective; optional UDM classifier setup. |
| CPO | `trl.experimental.cpo` | Preference data | Supports CPO variants such as SimPO, CPO-SimPO, and AlphaPO via config loss settings. |
| GKD / MiniLLM / GOLD | `trl.experimental.gkd`, `minillm`, `gold` | Distillation | GKD wraps SFT-style distillation; MiniLLM uses reverse-KLD-style distillation; GOLD adds logit/cross-tokenizer distillation features. |
| KTO | `trl.experimental.kto` | Unpaired or converted paired preference data | TRL v1.0 moved KTO into the experimental namespace. |
| Nash-MD / Online DPO / XPO | `trl.experimental.nash_md`, `online_dpo`, `xpo` | Prompt-only online preference/RL-style training | Reward model/functions score generated completions; use missing-EOS penalties when length control matters. |
| ORPO / TPO | `trl.experimental.orpo`, `tpo` | Preference data | ORPO prefers explicit prompts; TPO requires `prompt`, `chosen`, `rejected`, and `reference`. |
| PAPO / GMPO | `trl.experimental.papo`, `gmpo` | GRPO-family experiments | Keep usage close to documented config/trainer pairs because APIs are incubating. |
| PPO / PRM | `trl.experimental.ppo`, `prm` | PPO-style RL or stepwise supervision | PPO includes value-head wrappers; PRM uses standard stepwise-supervision datasets. |
| SDFT / SDPO / SSD | `trl.experimental.sdft`, `sdpo`, `ssd` | Self-distillation and sampled self-distillation | SDFT/SDPO can use vLLM; SSD needs only prompts and model-generated samples. |

## Usage Pattern

```python
from trl.experimental.kto import KTOConfig, KTOTrainer

args = KTOConfig(output_dir="model-kto")
trainer = KTOTrainer(
    model=model,
    args=args,
    processing_class=tokenizer,
    train_dataset=train_dataset,
)
```

Use the config class from the same experimental module as the trainer. Avoid mixing stable trainer configs with experimental trainer classes unless the module explicitly documents that pattern.

## Review Checklist

- Confirm the import is intentionally experimental and warn the user when they ask for production stability.
- Confirm the dataset shape matches the trainer family before changing trainer code.
- Confirm optional integrations such as vLLM, PEFT, Liger, or reward models are already in scope; route backend tuning elsewhere.
- Keep method-specific paper or docs references close to the changed trainer; if implementing a new paper method in the repo, update the paper index in the source repository.
- For duplicated trainer patterns, preserve consistency across experimental trainers when touching shared-style logic.
