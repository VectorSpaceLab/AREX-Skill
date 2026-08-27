# Android GUI cookbook reference

This is reference-only operating guidance for EasyR1's Android GUI number-game example family. The generated skill does not bundle device-control, game-service, or VLM-client scripts because those workflows require external services, Android devices or emulators, network endpoints, and mutable screenshots/clicks. Use this document to prepare the data, prompt, and reward contracts; use the `training-workflows` sub-skill for actual EasyR1 launch configuration.

## What the task is

The number game presents a screenshot with three number cards and one active traffic-light color. The model must output the position index of the correct card:

| Light color | Rule | Output |
| --- | --- | --- |
| Green | choose the largest number | position `0`, `1`, or `2` |
| Red | choose the smallest number | position `0`, `1`, or `2` |
| Yellow | choose the middle number | position `0`, `1`, or `2` |

The reward is sparse: `1.0` for the correct position, `0.0` otherwise.

## External prerequisites

Treat all of these as operator-provided prerequisites, not skill runtime dependencies:

- A hosted number-game web service reachable by the Android browser.
- One or more Android devices or emulators reachable through ADB over USB or TCP.
- Permission to capture screenshots and send taps to those devices.
- A visual-language model endpoint for interactive play evaluation, if running a play-agent outside training. The public example family used OpenAI-compatible vLLM or Ollama-style APIs.
- A full EasyR1 training runtime if training is launched: CUDA GPUs, Ray workers, flash-attn, vLLM, model weights, datasets, and logging credentials if used.
- A data-conversion step that turns collected screenshots and labels into a dataset matching the row contract below.

Quick prerequisite checks that do not depend on the original checkout:

```bash
adb devices
adb -s <device_id> shell wm size
adb -s <device_id> shell am start -a android.intent.action.VIEW -d "http://<game-host>:<port>/number_game.html"
```

Expected signal: the device appears in `adb devices`, reports a screen size, and opens the game URL in the browser. These checks do not validate EasyR1 itself.

## Dataset row shape

Use a vision-language dataset with the configured prompt and answer columns. A compact row shape is:

```json
{
  "problem": "<image>\nUse the traffic-light rule and output only the correct card position.",
  "images": ["screenshots/episode_001_round_03_question.png"],
  "answer": "1"
}
```

Guidance:

- Keep `answer` as a string digit: `"0"`, `"1"`, or `"2"`.
- Keep exactly one `<image>` placeholder for the screenshot.
- If storing relative image paths, configure the media root with `data.image_dir` in the training config.
- Keep labels deterministic. The label is the correct position, not the clicked position used during random data collection.
- If using collected metadata, preserve enough metadata to audit the round: episode id, round id, screenshot filename, clicked position if any, traffic-light color if annotated, displayed numbers, and final correct position.

## Prompt template

The distilled Android GUI prompt template is:

```jinja
You are playing a number selection game. Your goal is to select the CORRECT number based on the traffic light color.

Game Rules:
- There are 3 numbers to choose from (positions: left=0, middle=1, right=2)
- GREEN light: select the LARGEST number
- RED light: select the SMALLEST number
- YELLOW light: select the MIDDLE number

Your Task:
1. Look at the screenshot.
2. Identify the active light color.
3. Read the three numbers.
4. Apply the rule.
5. Output ONLY one digit: 0, 1, or 2.

{{ content }}
```

Keep the output restriction strict. Extra explanation is usually harmless for the reward's digit extractor, but it makes rollout analysis harder and may hide template failures.

## Reward function design

The Android GUI reward is a batch reward. It extracts the first digit in `[0, 1, 2]` from the decoded response and compares it with `ground_truth`.

```python
import re
from typing import Any

REWARD_NAME = "number_game"
REWARD_TYPE = "batch"

def extract_answer(response: str) -> str:
    response = response.strip()
    if response in {"0", "1", "2"}:
        return response
    match = re.search(r"[012]", response)
    return match.group(0) if match else ""

def compute_score(reward_inputs: list[dict[str, Any]]) -> list[dict[str, float]]:
    scores = []
    for item in reward_inputs:
        pred = extract_answer(item.get("response", ""))
        gt = str(item.get("ground_truth", "")).strip()
        acc = 1.0 if pred == gt else 0.0
        scores.append({"overall": acc, "accuracy": acc})
    return scores
```

Validate the contract before launching training:

```bash
python sub-skills/data-and-rewards/scripts/easyr1_reward_smoke.py --builtins android
```

Expected success: the script reports `android-batch` with `status: "ok"`.

## Reference workflow outline

Use this as a planning checklist, not a runnable bundled workflow:

1. Provision the game service and verify the page is reachable from each Android device.
2. Connect devices with ADB and open the game page in the browser.
3. Capture pre-action screenshots for each round.
4. Label each screenshot with the correct position. If random taps are used for data collection, do not confuse the random clicked position with the correct label.
5. Convert screenshots and labels into train/validation dataset files with `problem`, `images`, and `answer` fields.
6. Run the bundled reward smoke script to check the score contract.
7. Route to `training-workflows` for a CUDA EasyR1 launch using the Android prompt template and reward function.
8. Route to `checkpoint-export` after training if a Hugging Face model export is needed.

## Interactive play-agent considerations

If evaluating a trained model by playing the live game, plan for these behaviors:

- Screenshot capture and tap coordinates are screen-resolution dependent. Recompute card and next-button positions for each device class.
- The VLM endpoint must accept an image and prompt and return a text response. Parse only `0`, `1`, or `2` as actionable decisions.
- Save before-click screenshots, after-click screenshots, final score screenshots, and a JSON result summary per device/episode.
- Retain debug logs outside the generated skill tree. Do not store private endpoint URLs, device IDs, or screenshots in runtime skill files.

## Why no runnable Android scripts are bundled

The original example family controlled real devices, connected to external VLM services, hosted a game server, clicked browser UI coordinates, and wrote local screenshot directories. Bundling that behavior as a skill script would make this runtime skill unsafe and non-deterministic by default. This skill therefore preserves the stable contracts—dataset rows, prompt, reward, and prerequisite checklist—while leaving service/device orchestration to an explicitly provisioned environment.

## Minimal acceptance checklist

- [ ] Device and game service are reachable outside EasyR1.
- [ ] Dataset rows contain exactly one image per prompt and a string digit answer.
- [ ] Prompt instructs the model to output only one digit.
- [ ] Reward returns `overall` and `accuracy` for every batch item.
- [ ] Custom reward passes [the smoke script](../scripts/easyr1_reward_smoke.py) before training.
- [ ] Training is not treated as validated until the full CUDA/runtime stack is available.
