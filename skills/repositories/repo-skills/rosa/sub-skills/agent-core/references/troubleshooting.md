# ROSA agent-core troubleshooting

## Import succeeds, construction fails on a ROS module

`import rosa` does not construct an agent and can succeed without ROS. During
`ROSA(ros_version=1, ...)`, ROSA imports the ROS 1 tools; during
`ROSA(ros_version=2, ...)`, it imports the ROS 2 tools. A missing `rospy`,
`rclpy`, or required ROS 2 command/runtime is therefore a middleware
installation/sourcing problem, not a missing `jpl-rosa` import. Install and
source the selected ROS distribution separately, then retry in that same
process environment. Do not claim that pip installation installs ROS.

Use [ros1-operations](../../ros1-operations/SKILL.md) or
[ros2-operations](../../ros2-operations/SKILL.md) for family-specific
prerequisites and failures. Do not switch `ros_version` merely to hide a
missing environment: it changes the tool family.

## Unsupported ROS version

The constructor accepts only `ros_version=1` or `ros_version=2`. Other values
are rejected while ROSA builds its tools with:

```text
Invalid ROS version. Must be either 1 or 2.
```

Fix the configuration rather than expecting a third-party ROS family to be
selected implicitly.

## Model cannot call tools

ROSA uses LangChain's tool-calling agent constructor. A plain text-only model,
a custom `BaseChatModel` without compatible `bind_tools`, or a provider model
without tool-call support can fail at construction or on the first call.
Choose a tested provider/model with tool calling, or validate a custom model
against a harmless tool before adding ROS operations. This is distinct from a
missing ROS module: both can occur at different construction stages.

## Provider extra, key, or server is missing

- OpenAI/Azure integration is part of the base package, but the service,
  endpoint/deployment, and credentials still must be configured.
- Install `jpl-rosa[anthropic]` for `ChatAnthropic` or
  `jpl-rosa[ollama]` for `ChatOllama`; do not assume either is installed by the
  base package.
- Anthropic requires its API key and reachable service. Ollama requires the
  optional integration, a reachable Ollama server, and a local tool-capable
  model. Check the provider client before constructing ROSA.
- `LLM_PROVIDER` is only a helper convention; invalid values in such a helper
  are configuration errors, not a ROSA `ros_version` issue.

Never put a real key in a prompt, test fixture, skill, or diagnostic output.

## `invoke()` returns an error-looking string

An ordinary exception is intentionally returned as:

```text
An error occurred: <exception text>
```

It is not raised through the public method, and the failed turn is not appended
to `chat_history`. Inspect the text for provider, tool schema, middleware, or
executor clues and report it as a failed call. `KeyboardInterrupt` is the
exception: `invoke()` re-raises it so an outer application can handle stop
behavior.

## Streaming errors or disabled streaming

`astream()` is valid only when the instance was created with `streaming=True`.
Otherwise iteration raises:

```text
Streaming is not enabled. Use 'invoke' method instead or initialize ROSA with streaming=True.
```

With streaming enabled, consume `token`, `tool_start`, `tool_end`, `final`, and
`error` dictionaries. Ordinary streaming exceptions become an `error` event.
The implementation also converts a `KeyboardInterrupt` during streaming into
an error event with content `Operation interrupted by user`; do not expect the
streaming interrupt behavior to match synchronous `invoke()`.

If a provider emits no usable stream chunks, prefer `invoke()` with
`streaming=False` and verify provider support rather than treating an empty
stream as a ROS result.

## Parser failures and iteration limits

ROSA passes `handle_parsing_errors=True` and `max_iterations` to
`AgentExecutor`. A malformed model tool call can therefore be fed back to the
executor as a parser observation and consume iterations. Use a finite,
positive limit appropriate to the task, inspect the executor's stop text, and
fix model/tool schemas instead of increasing the limit blindly. The public
`invoke()` still returns only the executor output string.

`return_intermediate_steps=True` requests more executor state and can increase
memory use, but it does not change the public `invoke()` return shape. Use
`verbose=True` for executor diagnostics, knowing that it prints output rather
than returning a structured trace.

## History is missing or unexpectedly repeated

- History accumulation defaults to on. Successful `invoke()` calls append a
  `HumanMessage` and `AIMessage`; ordinary failed invokes do not.
- `accumulate_chat_history=False` intentionally prevents appending.
- `clear_chat()` replaces the object's list with `[]`; it does not alter a
  provider, tool, or external conversation store.
- Streaming records a turn only after non-empty output has been accumulated;
  an error-only stream does not create a successful history pair.
- History is in-memory and per instance. Do not treat it as durable robot
  state, and avoid placing secrets in user queries or custom prompts.

## Token usage is absent

Token display is forced off whenever `streaming=True`. When streaming is off,
ROSA enables its callback only for `ChatOpenAI` and `AzureChatOpenAI`; it logs a
warning and disables the option for Anthropic, Ollama, or another model class.
This is expected behavior, not proof that the provider returned zero tokens.
Provider-specific usage APIs are outside this route.

## Prompt behavior differs from expectation

Pass a `RobotSystemPrompts` object through `prompts=`. Its non-empty public
string fields become a robot-specific system message; the optional dictionary
field is stored but is not rendered by `str()`. Keep prompt authoring,
blacklists, custom packages, and prompt mutation safeguards in
[tool-customization](../../tool-customization/SKILL.md). Keep ROS action
sequencing and discovery in the appropriate ROS-family route.
