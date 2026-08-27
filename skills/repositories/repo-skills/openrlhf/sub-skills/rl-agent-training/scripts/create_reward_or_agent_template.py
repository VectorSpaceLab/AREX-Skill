#!/usr/bin/env python3
"""Create small OpenRLHF reward or agent function templates."""

from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent

TEMPLATES = {
    "reward": r'''
import torch


def reward_func(queries, prompts, labels, **kwargs):
    """Return rewards for generated responses.

    queries: full prompt + response strings
    prompts: original prompt strings
    labels: values from --data.label_key, or None if no label key is set
    """
    rewards = []
    for query, prompt, label in zip(queries, prompts, labels):
        response = query[len(prompt):] if isinstance(prompt, str) and query.startswith(prompt) else query
        is_good = bool(response.strip())
        rewards.append(1.0 if is_good else 0.0)

    rewards = torch.tensor(rewards, dtype=torch.float)
    return {
        "rewards": rewards,
        "scores": rewards,
        "extra_logs": {"non_empty_rate": rewards.mean().item() if len(rewards) else 0.0},
    }
''',
    "math-reward": r'''
import re

import torch

_BOXED_RE = re.compile(r"\\boxed\{([^{}]+)\}")


def _extract_boxed(text):
    matches = _BOXED_RE.findall(text or "")
    return matches[-1].strip() if matches else ""


def _normalize(text):
    return str(text or "").strip().replace(" ", "")


def reward_func(queries, prompts, labels, **kwargs):
    """Reward boxed-answer math completions.

    Replace _normalize/_extract_boxed if your dataset uses another answer format.
    """
    rewards = []
    parse_failures = 0
    for query, prompt, label in zip(queries, prompts, labels):
        response = query[len(prompt):] if isinstance(prompt, str) and query.startswith(prompt) else query
        prediction = _extract_boxed(response)
        if not prediction:
            parse_failures += 1
        rewards.append(1.0 if _normalize(prediction) == _normalize(label) else 0.0)

    rewards = torch.tensor(rewards, dtype=torch.float)
    batch_size = max(len(rewards), 1)
    return {
        "rewards": rewards,
        "scores": rewards,
        "extra_logs": {
            "math_accuracy": rewards.mean().item() if len(rewards) else 0.0,
            "parse_failure_rate": parse_failures / batch_size,
        },
    }
''',
    "multiturn": r'''
from typing import Any, Dict

import torch

from openrlhf.utils.agent import AgentInstanceBase, MultiTurnAgentExecutor


class AgentInstance(AgentInstanceBase):
    def __init__(self, *args, **kwargs):
        self.step_idx = 0
        self.max_steps = 2

    async def reset(self, states: dict, **kwargs):
        self.step_idx = 0
        return {"observation": states["observation"]}

    async def step(self, states: dict, **kwargs) -> Dict[str, Any]:
        action_text = states["action_text"]
        label = states["label"]
        self.step_idx += 1
        done = self.step_idx >= self.max_steps

        if done:
            reward_value = 1.0 if label and str(label).lower() in action_text.lower() else 0.0
            reward = torch.tensor(reward_value, dtype=torch.float)
            return {
                "rewards": reward,
                "scores": reward,
                "environment_feedback": "\n\nHuman: [DONE]\n</s>",
                "done": True,
                "extra_logs": {"success": reward},
            }

        return {
            "rewards": torch.tensor(0.0),
            "scores": torch.tensor(0.0),
            "environment_feedback": (
                "\n\nHuman: Please inspect your previous answer, fix any issue, "
                "and provide the final answer.\n</s>\n\nAssistant: "
            ),
            "done": False,
            "sampling_params": states.get("sampling_params"),
        }


class AgentExecutor(MultiTurnAgentExecutor):
    def __init__(self):
        super().__init__(AgentInstance)
''',
    "vlm-multiturn": r'''
from typing import Any, Dict

import torch
from PIL import Image

from openrlhf.utils.agent import AgentInstanceBase, MultiTurnAgentExecutor

# Replace these tokens with the image placeholders expected by your VLM chat template.
USER_START = "\n<|im_start|>user\n"
USER_END = "<|im_end|>\n<|im_start|>assistant\n"
IMAGE_PLACEHOLDER = "<|vision_start|><|image_pad|><|vision_end|>"


def _blank_feedback_image():
    return Image.new("RGB", (32, 32), color=(240, 240, 240))


class AgentInstance(AgentInstanceBase):
    def __init__(self, *args, **kwargs):
        self.step_idx = 0
        self.max_steps = 2

    async def reset(self, states: dict, **kwargs):
        self.step_idx = 0
        return {"observation": states["observation"]}

    async def step(self, states: dict, **kwargs) -> Dict[str, Any]:
        action_text = states["action_text"]
        label = states["label"]
        self.step_idx += 1
        done = self.step_idx >= self.max_steps

        if done:
            reward_value = 1.0 if label and str(label).lower() in action_text.lower() else 0.0
            reward = torch.tensor(reward_value, dtype=torch.float)
            return {
                "rewards": reward,
                "scores": reward,
                "environment_feedback": "\n<|im_end|>\n",
                "done": True,
                "extra_logs": {"vlm_success": reward},
            }

        return {
            "rewards": torch.tensor(0.0),
            "scores": torch.tensor(0.0),
            "environment_feedback": (
                f"{USER_START}{IMAGE_PLACEHOLDER}\n"
                "Here is updated visual feedback. Reconsider the task and answer again.\n"
                f"{USER_END}"
            ),
            "environment_images": [_blank_feedback_image()],
            "done": False,
            "sampling_params": states.get("sampling_params"),
        }


class AgentExecutor(MultiTurnAgentExecutor):
    def __init__(self):
        super().__init__(AgentInstance)
''',
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=sorted(TEMPLATES), required=True)
    parser.add_argument("--output", required=True, help="Template output path")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output file")
    return parser.parse_args()


def main():
    args = parse_args()
    output = Path(args.output)
    if output.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing file: {output}. Use --force to replace it.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(dedent(TEMPLATES[args.kind]).lstrip() + "\n", encoding="utf-8")
    print(f"Wrote {args.kind} template to {output}")


if __name__ == "__main__":
    main()
