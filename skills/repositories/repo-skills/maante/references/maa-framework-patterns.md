# MaaFramework Patterns Verified for MaaNTE

## When To Read

Read this when you need the MaaFramework API shapes MaaNTE relies on, or when translating between Pipeline JSON and Python CustomAction/CustomRecognition code.

## Verified Python Binding Facts

Inspection of MaaFramework Python bindings for `maafw` 5.10.4 verified these public shapes:

```python
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
from maa.context import Context

AgentServer.custom_action(name: str)
AgentServer.custom_recognition(name: str)
AgentServer.start_up(identifier: str) -> bool
AgentServer.join() -> None
AgentServer.shut_down() -> None

CustomAction.run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult | bool
CustomAction.RunResult(success: bool)

CustomRecognition.AnalyzeResult(box, detail: dict)

Context.run_task(entry: str, pipeline_override: dict = {})
Context.run_action(entry: str, box=(0, 0, 0, 0), reco_detail: str = "", pipeline_override: dict = {})
Context.run_recognition(entry: str, image, pipeline_override: dict = {})
Context.run_recognition_direct(reco_type, reco_param, image)
Context.get_node_data(name: str) -> dict | None
Context.override_next(name: str, next_list: list[str]) -> bool
Context.set_anchor(anchor_name: str, node_name: str) -> bool
```

`Tasker` exposes `controller`, `resource`, `running`, `stopping`, `post_task`, `post_recognition`, `post_action`, `post_stop`, log/debug methods, and detail lookup helpers.

## Pipeline Recognition Types Used by MaaNTE

MaaNTE uses both v2 nested and older shorthand forms. Prefer v2 for new code.

| Type | Use in MaaNTE | Key notes |
| --- | --- | --- |
| `TemplateMatch` | Buttons/icons, scene status, minigame UI, character portraits | Template paths are relative to resource image root; thresholds often 0.6–0.8; `green_mask` appears in many assets. |
| `OCR` | Buttons, dialogue, labels, result screens, task state | Use complete text where possible; multilingual expected arrays are common; regex/partial strings may need i18n skip handling. |
| `ColorMatch` | Fishing cursor/hook, PinkPaw monsters, Tetris board states | MaaNTE often uses `method: 40`, `count`, and `connected` to reduce noise. |
| `DirectHit` | Entry nodes, unconditional action after a prior recognition, config placeholders | Use carefully; never replace a real state check with blind DirectHit unless the previous node proves the state. |
| `And` / `Or` | Scene gating and composite status checks | Use nested recognitions or node references; set `box_index` when a later action should click a specific child result. |
| `Custom` recognition | BagelSpam LLM generation and any logic Pipeline cannot express | Register with `AgentServer.custom_recognition` and return `AnalyzeResult` or `None`. |

## Pipeline Action Types Used by MaaNTE

| Type | MaaNTE use | Notes |
| --- | --- | --- |
| `Click`, `LongPress`, `Swipe`, `ClickKey` | Ordinary GUI/game actions | Coordinates/key codes are 1280×720 and Win32 virtual-key oriented. |
| `Custom` | Python actions for fishing, navigation, audio, minigames, registry helpers | `custom_action` must match the decorated Python registration name exactly. |
| `DoNothing` | Entry/status/config nodes | Useful for pure routing or recognition-only nodes. |
| `StopTask` | PinkPaw finish/abort and task exits | Prefer explicit stop nodes for long-running loops. |
| `TouchMove`, `KeyDown`, `KeyUp`, relative move methods | Movement and heist internals | Release held controls in Python finally blocks when long-running. |

## Flow-Control Patterns

- `next` is ordered: MaaFramework tries candidates and continues with the first hit. Put likely business states before broad fallback handlers, but include popups/loading/exit states where needed.
- `[JumpBack]NodeName` lets a node temporarily handle a scene transition, popup, or loading state and then return to the parent recognition list.
- `[Anchor]Name` resolves to a runtime node set by an `anchor` declaration or Python action. Fishing and character sync use anchors to route restarts or callbacks.
- `pre_wait_freezes` and `post_wait_freezes` are preferred over hard sleeps when waiting for UI stability.
- `max_hit` is used for bounded loops, but should not hide a missing state transition. Investigate root cause before adding blind retries.

## Python CustomAction Pattern

```python
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from utils.logger import logger
from utils.maafocus import PrintT

@AgentServer.custom_action("example_action")
class ExampleAction(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        try:
            # parse argv.custom_action_param as dict or JSON string
            # use context.tasker.controller for screenshots/clicks/keys
            # check context.tasker.stopping in long loops
            return CustomAction.RunResult(success=True)
        except Exception as exc:
            logger.error("example_action failed: %s", exc)
            PrintT(context, "example_action.failed", str(exc))
            return CustomAction.RunResult(success=False)
```

MaaNTE has a compatibility helper `agent/custom/action/Common/utils.py::load_params` for `None`, dict, JSON string, and invalid input cases.

## Direct Recognition Helpers

When Python needs a Pipeline node or one-off recognition without executing the node's action:

- `context.run_recognition(node_name, image, pipeline_override={...})` uses an existing node definition.
- `context.run_recognition_direct(JRecognitionType.OCR, JOCR(...), image)` builds a recognition object directly.
- `context.get_node_data(node_name)` can read config/attach nodes such as `SoundDodgeEnableConfig` or `OnlineMapNavigationSettingsConfig`.

## Delay Defaults and Common Pitfall

MaaFramework has default waits when fields are omitted. In MaaNTE, nodes that need fast or deterministic loops should explicitly set:

```json
"rate_limit": 0,
"pre_delay": 0,
"post_delay": 0
```

Do not globally remove delays from UI transitions that need animation or load-state stability; replace hard sleeps with concrete intermediate recognition nodes where possible.
