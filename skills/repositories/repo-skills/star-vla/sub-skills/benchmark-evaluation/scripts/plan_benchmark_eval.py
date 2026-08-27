#!/usr/bin/env python3
"""Safe StarVLA benchmark-evaluation checklist generator.

This helper prints a plan for a named benchmark. It never starts a policy
server, imports simulator packages, downloads assets, or touches checkpoints.
"""

from __future__ import annotations

import argparse
import textwrap
from dataclasses import dataclass, field
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class BenchmarkPlan:
    name: str
    aliases: List[str]
    summary: str
    server_role: str
    client_role: str
    placeholders: List[str]
    server_steps: List[str]
    client_steps: List[str]
    expected_outputs: List[str]
    warnings: List[str] = field(default_factory=list)
    route_elsewhere: List[str] = field(default_factory=list)


COMMON_PLACEHOLDERS = [
    "CHECKPOINT_PATH: model checkpoint file served by StarVLA",
    "HOST and PORT: shared by server and simulator client",
    "UNNORM_KEY: statistics key for server-side unnormalization",
    "ACTION_CHUNK_SIZE: read from server metadata after startup",
    "OUTPUT_DIR: logs, videos, metrics, and run summaries",
]

COMMON_SERVER_STEPS = [
    "Use the StarVLA policy-serving environment, not the simulator environment.",
    "Start the websocket policy server with CHECKPOINT_PATH, PORT, and selected device.",
    "Wait until checkpoint loading completes and the port listens before starting the client.",
    "Record server metadata, especially action_chunk_size and available_unnorm_keys.",
]

COMMON_CLIENT_STEPS = [
    "Use the benchmark simulator environment with benchmark assets/data prepared.",
    "Connect to the policy server at HOST:PORT.",
    "Send examples with image, language, optional state/history, and UNNORM_KEY.",
    "Consume response data.actions and apply the benchmark-specific replanning cadence.",
]

COMMON_WARNINGS = [
    "This helper is planning-only: it does not launch servers, simulators, or downloads.",
    "If the client expects normalized_actions instead of actions, route to policy-deployment.",
    "If full training command construction or checkpoint creation is needed, route to training-config.",
    "If dataset registry/statistics/modality creation is needed, route to data-integration.",
]


def plan_map() -> Dict[str, BenchmarkPlan]:
    plans = [
        BenchmarkPlan(
            name="libero",
            aliases=["libero", "libero-plus", "libero_plus"],
            summary="LIBERO suite evaluation with a StarVLA policy server and LIBERO simulator client.",
            server_role="Serve the StarVLA checkpoint and optional runtime config override.",
            client_role="Run a LIBERO task suite, save videos, and report suite success rates.",
            placeholders=COMMON_PLACEHOLDERS
            + [
                "TASK_SUITE_NAME: e.g. spatial/object/goal/long suite selector",
                "NUM_TRIALS_PER_TASK: requested rollout count",
                "LIBERO_SIM_ROOT: external LIBERO simulator/project root",
                "MUJOCO_GL / PYOPENGL_PLATFORM: simulator rendering backend values",
            ],
            server_steps=COMMON_SERVER_STEPS
            + [
                "For the released Qwen3 PI LIBERO checkpoint, apply the historical LayerwiseFM compatibility override at launch time.",
            ],
            client_steps=COMMON_CLIENT_STEPS
            + [
                "Verify task suite name and rollout count before any full run.",
                "Use server metadata for action_chunk_size; do not recompute it from old checkpoint fields.",
            ],
            expected_outputs=[
                "Per-suite success rates averaged over tasks/episodes.",
                "Videos in a checkpoint/run-derived result directory.",
            ],
            warnings=COMMON_WARNINGS
            + [
                "Do not edit checkpoint config for the compatibility override.",
                "Dataset preparation scripts can download large artifacts; skip unless explicitly requested.",
            ],
            route_elsewhere=["Policy-server schema or response errors -> ../policy-deployment/SKILL.md"],
        ),
        BenchmarkPlan(
            name="simplerenv",
            aliases=["simplerenv", "simpler", "widowx"],
            summary="SimplerEnv WidowX evaluation with StarVLA serving and a ManiSkill/SimplerEnv simulator client.",
            server_role="Serve the Bridge/RT-1 style checkpoint on a fixed port.",
            client_role="Run selected SimplerEnv tasks with overlay assets and simulator rendering configured.",
            placeholders=COMMON_PLACEHOLDERS
            + [
                "SIMPLERENV_ROOT: external simulator/project root",
                "OVERLAY_ASSETS: real-to-sim overlay image assets required by tasks",
                "TASK_ENV_NAMES: selected task IDs rather than the whole benchmark by default",
                "RENDER_BACKEND: Vulkan/MuJoCo/OpenGL settings for this machine",
            ],
            server_steps=COMMON_SERVER_STEPS,
            client_steps=COMMON_CLIENT_STEPS
            + [
                "Verify a minimal simulator build before debugging StarVLA policy behavior.",
                "Confirm whether UNNORM_KEY should select Bridge or RT-1 statistics.",
            ],
            expected_outputs=["Per-task logs and videos under a run/checkpoint-derived output directory."],
            warnings=COMMON_WARNINGS
            + [
                "Missing libvulkan.so.1 or GL context creation failures are simulator-side issues.",
                "Full task loops can run long; start with one task for debugging.",
            ],
            route_elsewhere=["Model/framework import errors inside the policy server -> ../policy-deployment/SKILL.md"],
        ),
        BenchmarkPlan(
            name="robocasa-tabletop",
            aliases=["robocasa", "robocasa-tabletop", "tabletop", "gr1"],
            summary="RoboCasa GR1 tabletop evaluation using a StarVLA websocket policy server.",
            server_role="Serve an OFT or GR00T RoboCasa tabletop checkpoint.",
            client_role="Run the RoboCasa tabletop simulator and map StarVLA chunks to named GR1 action groups.",
            placeholders=COMMON_PLACEHOLDERS
            + [
                "ENV_NAME: tabletop task name",
                "N_EPISODES and MAX_EPISODE_STEPS: rollout budget",
                "N_ACTION_STEPS: actions consumed from each predicted chunk",
                "SEND_STATE_POLICY: omit state for checkpoints trained without state; include state for state-aware checkpoints",
                "VIDEO_OUT_PATH: simulator video output directory",
            ],
            server_steps=COMMON_SERVER_STEPS,
            client_steps=COMMON_CLIENT_STEPS
            + [
                "Resize images to the checkpoint recipe size and keep camera ordering consistent.",
                "Choose the state toggle intentionally before judging policy quality.",
            ],
            expected_outputs=["Task success rates and videos from the simulator client."],
            warnings=COMMON_WARNINGS
            + [
                "QwenOFT tabletop checkpoint should omit state; GR00T uses state.",
                "If multiple statistics keys exist, pass the RoboCasa embodiment key explicitly.",
            ],
            route_elsewhere=["Named action-group protocol failures -> ../policy-deployment/SKILL.md"],
        ),
        BenchmarkPlan(
            name="robocasa365",
            aliases=["robocasa365", "robocasa-365", "robocasa_365"],
            summary="Upstream RoboCasa 365 task evaluation with server/client split.",
            server_role="Serve the StarVLA checkpoint from the policy-serving environment.",
            client_role="Run an upstream RoboCasa task such as a kitchen manipulation task.",
            placeholders=COMMON_PLACEHOLDERS
            + [
                "ENV_NAME: RoboCasa task id",
                "N_EPISODES, N_ENVS, MAX_STEPS, N_ACTION_STEPS: evaluation budget",
                "ROBOCASA_ASSETS: kitchen/object assets and dataset paths",
            ],
            server_steps=COMMON_SERVER_STEPS,
            client_steps=COMMON_CLIENT_STEPS
            + ["Keep short walk-through settings separate from official benchmark settings."],
            expected_outputs=[
                "Per-task JSON summary near the checkpoint or selected output path.",
                "Videos in the configured result/video directory.",
            ],
            warnings=COMMON_WARNINGS
            + ["A 100-step walk-through checkpoint is a smoke example, not full benchmark reproduction."],
            route_elsewhere=["Data registry or modality issues -> ../data-integration/SKILL.md"],
        ),
        BenchmarkPlan(
            name="robotwin",
            aliases=["robotwin", "robotwin2", "robotwin-2"],
            summary="RoboTwin 2.0 evaluation, either single-task manual debug or multi-device scheduler.",
            server_role="Launch one policy server per scheduler slot or a single server for manual debug.",
            client_role="Run RoboTwin tasks in clean/randomized modes and stream success-rate lines.",
            placeholders=COMMON_PLACEHOLDERS
            + [
                "ROBOTWIN_ROOT: external RoboTwin project root",
                "MODE: demo_clean or demo_randomized",
                "POLICY_RUN_NAME: used for log naming",
                "TASKS: one task, a task-list file, or all",
                "JOBS_PER_DEVICE and BASE_PORT: scheduler capacity controls",
                "ACTION_MODE and NORMALIZATION_MODE: deploy policy settings",
            ],
            server_steps=COMMON_SERVER_STEPS
            + ["For schedulers, allocate a unique port for each server/client slot."],
            client_steps=COMMON_CLIENT_STEPS
            + [
                "Verify external RoboTwin code forwards CHECKPOINT_PATH to the StarVLA adapter.",
                "Start with one task before using all tasks or multiple devices.",
            ],
            expected_outputs=[
                "Per-episode success-rate lines.",
                "Server/eval logs under a checkpoint/run-derived log root.",
            ],
            warnings=COMMON_WARNINGS
            + [
                "Patching third-party RoboTwin code is a user-authorized action, not a safe default.",
                "Schedulers may start many policy servers and simulator clients.",
            ],
            route_elsewhere=["Websocket action schema issues -> ../policy-deployment/SKILL.md"],
        ),
        BenchmarkPlan(
            name="domino",
            aliases=["domino"],
            summary="DOMINO dynamic manipulation evaluation with dynamic metrics and optional history payloads.",
            server_role="Launch one StarVLA policy server per task slot or a single server for manual debug.",
            client_role="Run DOMINO dynamic tasks and collect success/manipulation metrics.",
            placeholders=COMMON_PLACEHOLDERS
            + [
                "DOMINO_ROOT: external DOMINO project root",
                "MODE: clean_dynamic or random_dynamic evaluation mode",
                "RUN_NAME: result/log label",
                "TASKS: subset, task-list file, or all dynamic tasks",
                "HISTORY_K, HISTORY_STRIDE, HISTORY_MODE: optional bridge history payload settings",
            ],
            server_steps=COMMON_SERVER_STEPS,
            client_steps=COMMON_CLIENT_STEPS
            + [
                "Record both success and manipulation-score outputs.",
                "Enable history only when the target policy is expected to consume history payloads.",
            ],
            expected_outputs=[
                "Success Rate, Manipulation Score, route completion, penalty counts.",
                "Per-task logs in a run/checkpoint-derived log root.",
            ],
            warnings=COMMON_WARNINGS
            + ["A policy may ignore history_images even when the bridge sends them."],
            route_elsewhere=["Training a dynamic-history policy -> ../training-config/SKILL.md"],
        ),
        BenchmarkPlan(
            name="behavior",
            aliases=["behavior", "behavior1k", "behavior-1k"],
            summary="BEHAVIOR-1K evaluation planning for an experimental/under-construction StarVLA bridge.",
            server_role="Serve the checkpoint while keeping simulator rendering dependencies separate.",
            client_role="Run BEHAVIOR tasks with required assets/task descriptions and 23D action contract.",
            placeholders=COMMON_PLACEHOLDERS
            + [
                "BEHAVIOR_ROOT: external simulator project root",
                "ASSET_ROOT: BEHAVIOR asset dataset root",
                "TASKS_JSONL: task-description file",
                "INSTANCE_IDS: train/test evaluation instances",
                "RENDER_DEVICE: simulator-compatible rendering device",
            ],
            server_steps=COMMON_SERVER_STEPS,
            client_steps=COMMON_CLIENT_STEPS
            + ["Validate simulator rendering before diagnosing model performance."],
            expected_outputs=["Task videos and challenge/task success signals."],
            warnings=COMMON_WARNINGS
            + [
                "Source docs are under construction and may contain local placeholders.",
                "Avoid devices without simulator-required ray-tracing support for actual BEHAVIOR evaluation.",
                "If the adapter expects normalized_actions, treat it as stale relative to current server-side unnormalization.",
            ],
            route_elsewhere=["Response contract mismatch -> ../policy-deployment/SKILL.md"],
        ),
        BenchmarkPlan(
            name="vla-arena",
            aliases=["vla-arena", "vla_arena", "arena"],
            summary="VLA-Arena evaluation across task suites and difficulty levels.",
            server_role="Serve one or more StarVLA policy-server instances for suite groups.",
            client_role="Run selected VLA-Arena suites/levels through the external project environment.",
            placeholders=COMMON_PLACEHOLDERS
            + [
                "VLA_ARENA_PROJECT: external VLA-Arena project directory",
                "SUITES: one or more suite names",
                "LEVELS: difficulty levels to evaluate",
                "GPU_SELECTION and BASE_PORT: parallel launcher controls",
            ],
            server_steps=COMMON_SERVER_STEPS
            + ["For parallel evaluation, wait for every server slot before launching suite groups."],
            client_steps=COMMON_CLIENT_STEPS
            + ["Prefer one suite/level for debugging before full 11-suite parallel evaluation."],
            expected_outputs=["CSV summary, logs, success rate, and constraint cost for safety suites."],
            warnings=COMMON_WARNINGS
            + ["Parallel launcher selects devices and starts several servers; avoid for smoke checks."],
            route_elsewhere=["Constraint-cost interpretation remains benchmark-specific; do not infer model internals."],
        ),
        BenchmarkPlan(
            name="calvin",
            aliases=["calvin"],
            summary="Calvin evaluation using original Calvin validation data and a StarVLA policy server.",
            server_role="Serve the Calvin-trained StarVLA checkpoint.",
            client_role="Run Calvin evaluation sequences from original Calvin-format validation data.",
            placeholders=COMMON_PLACEHOLDERS
            + [
                "CALVIN_VALIDATION_DATA: original Calvin dataset containing validation data",
                "CALVIN_CONFIG: Calvin model/config directory",
                "EVAL_SEQUENCES_JSON: sequence file",
                "NUM_SEQUENCES: evaluation budget",
            ],
            server_steps=COMMON_SERVER_STEPS,
            client_steps=COMMON_CLIENT_STEPS
            + ["Keep LeRobot training data and original Calvin evaluation data separate."],
            expected_outputs=["Average sequence length and per-position task-chain success metrics."],
            warnings=COMMON_WARNINGS
            + ["Using training-format data for evaluation is a format mismatch."],
            route_elsewhere=["Data conversion/mixture setup -> ../data-integration/SKILL.md"],
        ),
        BenchmarkPlan(
            name="robodojo",
            aliases=["robodojo", "robo-dojo"],
            summary="RoboDojo evaluation delegated to RoboDojo/XPolicyLab StarVLA adapter.",
            server_role="Policy serving is managed by the companion adapter launcher for released checkpoints.",
            client_role="RoboDojo/XPolicyLab runs simulator startup, checkpoint handling, and result collection.",
            placeholders=[
                "ROBODOJO_ROOT: external RoboDojo project root containing the companion adapter",
                "POLICY_VARIANT: oft, groot, or pi_v3 released checkpoint family",
                "TASK: RoboDojo task name",
                "SEED: evaluation seed",
                "POLICY_DEVICE and SIM_DEVICE: device allocation",
                "EPISODE_COUNT: small debug count or native protocol count",
                "OUTPUT_DIR: adapter-managed logs/results",
            ],
            server_steps=[
                "Do not start the generic StarVLA websocket server manually unless adapting the integration.",
                "Let the companion adapter handle released-checkpoint serving when the user requests RoboDojo evaluation.",
            ],
            client_steps=[
                "Verify RoboDojo and companion adapter are installed before any run.",
                "Use one small task/seed before the full released protocol.",
                "Record the 50-action prediction horizon and 16-action replanning interval.",
            ],
            expected_outputs=["Success rate and score over requested tasks/episodes."],
            warnings=COMMON_WARNINGS
            + [
                "This is a delegated third-party integration, not the generic two-terminal websocket recipe.",
                "Released-protocol evaluation is long and should not be used as a smoke test.",
            ],
            route_elsewhere=["Training RoboDojo recipes -> ../training-config/SKILL.md"],
        ),
    ]

    out: Dict[str, BenchmarkPlan] = {}
    for plan in plans:
        for alias in plan.aliases:
            out[alias.lower()] = plan
    return out


def wrap_item(text: str, indent: str = "  - ") -> str:
    return textwrap.fill(text, width=96, initial_indent=indent, subsequent_indent=" " * len(indent))


def print_section(title: str, items: Iterable[str]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    for item in items:
        print(wrap_item(item))


def render(plan: BenchmarkPlan) -> None:
    print(f"StarVLA benchmark evaluation plan: {plan.name}")
    print("=" * (36 + len(plan.name)))
    print(textwrap.fill(plan.summary, width=96))
    print("\nTerminal roles")
    print("--------------")
    print(wrap_item(f"Policy-server terminal: {plan.server_role}"))
    print(wrap_item(f"Simulator-client terminal: {plan.client_role}"))

    print_section("Placeholders to fill", plan.placeholders)
    print_section("Policy-server responsibilities", plan.server_steps)
    print_section("Simulator-client responsibilities", plan.client_steps)
    print_section("Expected outputs", plan.expected_outputs)
    print_section("Warnings", plan.warnings)
    if plan.route_elsewhere:
        print_section("Route elsewhere", plan.route_elsewhere)

    print("\nSafe next step")
    print("--------------")
    print(wrap_item("Write a one-task manual debug plan with concrete placeholders, then ask for explicit permission before launching any server, simulator, download, or third-party patch."))


def main() -> int:
    plans = plan_map()
    canonical = sorted({plan.name for plan in plans.values()})

    parser = argparse.ArgumentParser(
        description="Print a safe StarVLA benchmark evaluation checklist. No execution is performed.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Available benchmarks: " + ", ".join(canonical),
    )
    parser.add_argument(
        "benchmark",
        nargs="?",
        help="Benchmark name or alias. Use --list to show supported canonical names.",
    )
    parser.add_argument("--list", action="store_true", help="List supported benchmark names and aliases.")
    args = parser.parse_args()

    if args.list:
        print("Supported benchmarks and aliases:")
        seen = set()
        for name in canonical:
            plan = next(plan for plan in plans.values() if plan.name == name)
            if plan.name in seen:
                continue
            seen.add(plan.name)
            print(f"- {plan.name}: {', '.join(plan.aliases)}")
        return 0

    if not args.benchmark:
        parser.error("benchmark is required unless --list is used")

    key = args.benchmark.strip().lower()
    if key not in plans:
        valid = ", ".join(canonical)
        parser.error(f"unknown benchmark {args.benchmark!r}; choose one of: {valid}")

    render(plans[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
