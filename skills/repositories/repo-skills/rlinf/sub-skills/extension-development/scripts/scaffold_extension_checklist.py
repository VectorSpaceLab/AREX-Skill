#!/usr/bin/env python3
"""Print a safe RLinf extension checklist.

This helper is intentionally read-only: it prints guidance for a requested
extension kind and never creates, edits, deletes, imports, or installs anything.
"""

from __future__ import annotations

import argparse
import sys
from textwrap import dedent

CHECKLISTS: dict[str, str] = {
    "algorithm": """
    # Algorithm extension checklist for {name}

    - [ ] Decide whether this is an external plugin or a core RLinf algorithm.
    - [ ] Pick the selector: `algorithm.adv_type` for advantages, `algorithm.loss_type` for policy losses, or both.
    - [ ] Implement a tensor-safe function with the kwargs expected by RLinf dispatch.
    - [ ] Register advantages with `register_advantage(\"{selector}\")` and policy losses with `register_policy_loss(\"{selector}\")`.
    - [ ] Use lowercase selector names in YAML.
    - [ ] Return `(advantages, returns)` for advantages or `(loss_tensor, metrics_dict)` for losses.
    - [ ] Add config validation for group size, value heads, critic requirements, masks, bootstrap, and incompatible runner modes.
    - [ ] If external and used on Ray workers, import the registration from `RLINF_EXT_MODULE.register()`.
    - [ ] Add unit tests for math, shapes, masks, registry dispatch, and invalid config combinations.
    - [ ] Add the smallest e2e config/job if the algorithm is public.
    - [ ] Update docs and contributor handoff with unsupported backends or hardware assumptions.
    """,
    "model": """
    # Model extension checklist for {name}

    - [ ] Choose external `register_model(...)` plus `RLINF_EXT_MODULE` or core built-in registration.
    - [ ] Implement a builder `build_model(cfg, torch_dtype)` and register selector `{selector}` with category `embodied` when applicable.
    - [ ] Ensure every Ray worker and checkpoint utility can import the registration.
    - [ ] Implement the needed `BasePolicy` methods: at minimum `default_forward(...)` and `predict_action_batch(...)` for embodied RL.
    - [ ] Preserve rollout `forward_inputs` needed to recompute logprobs, values, entropy, and algorithm-specific outputs.
    - [ ] Decide whether actions are already executable or need env-side `prepare_actions(...)` support.
    - [ ] Add FSDP wrap policy for transformer blocks, vision encoders, projectors, adapters, and value heads.
    - [ ] For Megatron, cover model provider, checkpoint conversion, parallel-size validation, rollout support, and weight sync.
    - [ ] Add config presets with static YAML values and validation for model-specific fields.
    - [ ] Update install selectors, model requirements, Docker target, CI filters/jobs, docs, and e2e when public.
    - [ ] Add unit tests for registration/building, FSDP wrap policy, output contract, and bad config messages.
    """,
    "env": """
    # Environment extension checklist for {name}

    - [ ] Add a core `SupportedEnvType` value for `{selector}`; current env validation is enum-based.
    - [ ] Add a lazy `get_env_cls(...)` branch that imports heavyweight simulator modules only inside the branch.
    - [ ] Implement a gym-style env with compatible constructor config, rank, vectorized `num_envs`, `group_size`, seed, and return device handling.
    - [ ] Implement reset/step, observation/action spaces, reward/success info, termination, truncation, and deterministic reset behavior.
    - [ ] Add action conversion only when the env cannot consume model-returned actions directly; test chunk shape, dtype, scale, gripper semantics, and slicing.
    - [ ] Add offload/wrapper state serialization if `enable_offload` or decoupled rollout needs it.
    - [ ] Add static train/eval config presets and Python validation for env-specific invariants.
    - [ ] Add install support, env requirements, asset/path notes, Docker target, CI filters/jobs, docs, and e2e when public.
    - [ ] Add unit/smoke tests for factory resolution, action conversion, reset/step, validation errors, and hardware skips.
    """,
    "worker": """
    # Worker extension checklist for {name}

    - [ ] Decide whether to subclass `Worker` directly or an existing model/env/reward/rollout worker manager.
    - [ ] Put remote setup in `init_worker(...)` or an explicitly invoked remote method, not in driver-only code.
    - [ ] Launch with `create_group(...).launch(...)`; never instantiate the worker directly in the driver.
    - [ ] Define placement requirements and component name, including node group or hardware rank needs.
    - [ ] Use `Channel` or `send`/`recv` with paired communication, consistent devices, and explicit async behavior.
    - [ ] Use `self.log_info`, `self.log_warning`, and `self.log_error` for worker diagnostics.
    - [ ] Return rank-consistent metric dictionaries and detach tensors before metric logging.
    - [ ] Add config validation for worker-required fields and incompatible modes.
    - [ ] Add unit/remote-launch tests that are CPU-safe where possible, plus e2e if the worker is public.
    """,
    "runner": """
    # Runner extension checklist for {name}

    - [ ] Confirm this really needs a new runner rather than a config/worker branch in an existing runner.
    - [ ] Add or update task type validation if `runner.task_type` gains a new value.
    - [ ] Build an entrypoint that calls config validation, builds a cluster, builds placement, launches workers, creates the runner, and calls `run()` or `run_eval()`.
    - [ ] Let the runner own global step, channels, worker init order, rollout/reward/advantage/update loop, eval cadence, metrics, checkpoints, resume, and shutdown.
    - [ ] Reuse model-parallel placement for reasoning/agentic flows or hybrid placement for embodied flows unless the new task proves otherwise.
    - [ ] Keep user-facing config fields read-only after validation; derived defaults belong in validation.
    - [ ] Add unit tests for config and runner wiring, plus the smallest e2e for public task loops.
    - [ ] Update docs, CI filters/jobs, and troubleshooting with checkpoint/eval/metric behavior.
    """,
    "reward": """
    # Reward extension checklist for {name}

    - [ ] Choose rule-based text reward, embodied reward model, VLM input builder, VLM reward parser, or API reward path.
    - [ ] For rule-based rewards, implement `__init__(config)` and `get_reward(...)`, then register with `register_reward(\"{selector}\", RewardClass)`.
    - [ ] For VLM builders/parsers, register lowercase names and select them in `reward.model.input_builder_name` / `reward.model.reward_parser_name`.
    - [ ] For embodied reward models, implement `compute_reward(observations)` and wire the reward-model registry.
    - [ ] If external and used in Ray workers, import all registration code from `RLINF_EXT_MODULE.register()`.
    - [ ] Validate `reward.worker_type`, `reward.model.model_type`, reward-server placement, history-buffer settings, and parser params.
    - [ ] Test malformed outputs, empty batches, history windows before minimum size, local/API parity, timeouts, and batch order preservation.
    - [ ] Add install/docs/e2e coverage for public reward pipelines and note required endpoints or GPUs.
    """,
}


def selector_from_name(name: str | None, kind: str) -> str:
    """Return a normalized placeholder selector for checklist text."""
    if name:
        return name.strip().lower().replace("-", "_")
    return f"your_{kind}"


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Print a read-only checklist for an RLinf extension kind. "
            "The command never mutates source files."
        )
    )
    parser.add_argument(
        "--kind",
        required=True,
        choices=sorted(CHECKLISTS),
        help="Extension kind to scaffold guidance for.",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Optional model/env/reward/algorithm/worker/runner name to include.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the checklist printer."""
    parser = build_parser()
    args = parser.parse_args(argv)
    display_name = args.name or f"your {args.kind}"
    selector = selector_from_name(args.name, args.kind)
    text = CHECKLISTS[args.kind].format(name=display_name, selector=selector)
    print(dedent(text).strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
