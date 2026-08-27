# Version and Family Map

MobileAgent is a family repository, not one installable package. Route by user intent and platform first.

## Recommended routes

| Family | Best for | Prefer when | Avoid when |
|---|---|---|---|
| Mobile-Agent-v3.5 / GUI-Owl 1.5 | Current phone, desktop, and browser GUI control | New GUI automation work, OpenAI-compatible VLM endpoints, 0-1000 coordinate tool-call outputs | You need persistent cross-task evolution, legacy reproducibility, or post-training |
| Mobile-Agent-E | Android tasks with self-evolution, persistent tips, shortcuts, task memories | The user says Mobile-Agent-E, evolution, individual/evolution settings, task list JSON, persistent tips/shortcuts | The task is just one current GUI-Owl v3.5 deployment or desktop/browser |
| PC-Agent | Desktop automation using screenshot + OCR/accessibility + SoM on Mac/Windows | The user says PC-Agent, mac/windows desktop, SoM, OCR API/local OCR, ratio/font/A11y | Browser-only tasks or Android phone tasks |
| Mobile-Agent-v3 | Legacy Android/HarmonyOS Mobile-Agent v3 | The user names v3, HDC/HarmonyOS, `coor_type`, or `notetaker` | New v3.5 GUI-Owl work unless migration is requested |
| Mobile-Agent-v2 | Older Android Mobile-Agent with edited source settings and reflection/memory switches | Reproducing or migrating v2 scripts | New tasks; dependency stack is older/heavier |
| Mobile-Agent-v1 | Legacy hosted API or local v1 stack | Preserving a v1 integration, especially hosted `run_api.py` | New local perception work unless exact reproduction is needed |
| AndroidWorld/OSWorld/Web benchmarks | Benchmark/eval command preparation and safe skip classification | The user names AndroidWorld, MiniWoB, OSWorld, WebArena, WebVoyager, VisualWebArena, trajectory output, judge/eval | Ordinary live phone/desktop/browser task execution |
| GUI-Critic-R1 / grounding / GUI knowledge | Data/schema validation and model/checkpoint eval guidance | The user names GUI-Critic, score tags, grounding benchmark, GUI knowledge benchmark | Live local inference without checkpoint/GPU/API budget |
| UI-S1 | Semi-online RL/post-training, SOP eval, trajectory JSONL, checkpoint merge | The user names UI-S1, verl, GRPO/DAPO/PPO, Ray/vLLM, Qwen2.5-VL, model merger | Live GUI automation without training |

## Action format notes

- GUI-Owl v3.5 mobile/desktop expects a single `<tool_call>` JSON block with nested `arguments`; coordinates are normalized `0..1000` and are rescaled to the observed screenshot size.
- Legacy Mobile-Agent-v3 `--coor_type qwen-vl` also uses Qwen-style relative coordinates. Do not assume those are absolute pixels.
- PC-Agent has its own desktop action grammar and coordinate scaling controlled by OS-specific `ratio`, font, SoM, OCR, and accessibility options.
- Mobile-Agent-E uses the Mobile-Agent-E perceptor/actor stack and adds persistent memory behavior across task lists in evolution mode.
- UI-S1 data/eval stores model responses and actions in trajectory JSONL and should be validated before training/evaluation.

## Migration shortcuts

- From v1/v2 to current workflows: prefer GUI-Owl v3.5 for new Android runs, but preserve original instructions, `add_info`, API endpoint choices, and typing/ADB Keyboard assumptions.
- From v2 reflection/memory to persistent evolution: only route to Mobile-Agent-E when cross-task tips/shortcuts are required. A one-off task with hints belongs in current GUI-Owl `--add_info`.
- From v3 HarmonyOS/HDC: stay on legacy-agents for HarmonyOS unless the user changes device/runtime target; current v3.5 Android helpers are ADB-oriented.
- From browser source scripts to benchmark eval: route ordinary web task execution to current-gui-owl browser, and dataset/task-id benchmark evaluation to benchmarks-and-evaluation.
