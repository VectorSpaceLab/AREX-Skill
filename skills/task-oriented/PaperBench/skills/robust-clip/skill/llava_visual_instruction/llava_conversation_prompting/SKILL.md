---
name: llava_conversation_prompting
description: Format LLaVA-style multimodal prompts with image tokens, role boundaries, and answer-leakage checks.
---

# LLaVA Conversation Prompting

Use this skill when preparing visual-instruction examples for training, inference, or recovery checks that need LLaVA-like Human/Assistant turn boundaries. Do not use it for final answer scoring; scoring belongs to an evaluation skill.

## Inputs
- Instruction item with `human_prompt` and optional `assistant_answer`.
- Image token placeholder such as `<image>`.
- Separator policy, defaulting to `
### ` role separators.

## Outputs
A prompt record containing `user_prompt`, optional `training_prompt`, and metadata that states whether the assistant answer was withheld from the user side.

## Workflow
1. Prefix the human instruction with the image token.
2. Encode explicit `Human` and `Assistant` roles.
3. Keep the answer out of `user_prompt`; include it only in `training_prompt` when requested.
4. Return metadata suitable for generated-skill invocation logs.

## Validation
Run the included tests or `validate_skill_tree.py --run-tests`.

## Limitations
The formatter does not tokenize with Vicuna or load model weights; it preserves prompt contracts for bounded recovery.
