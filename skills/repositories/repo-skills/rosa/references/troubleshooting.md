# ROSA cross-cutting troubleshooting

Use the symptom and boundary first, then follow the owning sub-skill for the
specific API or workflow. Do not paper over a missing middleware or provider
with guessed entities or a CPU-only import claim.

## Install and import

**Symptom:** `pip` cannot resolve, `import rosa` fails, or `from rosa import
ROSA` is missing.

- Confirm Python is `>=3.9,<4`, install the public distribution `jpl-rosa`, and
  use `python -m pip` from the intended environment.
- Distinguish the distribution name (`jpl-rosa`) from the import name (`rosa`).
- Check `python -m pip check` and retry the import without relying on a source
  checkout or a different interpreter on `PATH`.
- If a compiled dependency fails to build, use a supported Python wheel or the
  package's documented build prerequisites; do not install unrelated extras.

## ROS family and middleware

**Symptom:** `ModuleNotFoundError: rosgraph`, `rospy`, or `rclpy`, or ROSA
construction fails before a model call.

- Package installation does not install ROS. Install/source the intended ROS 1
  or ROS 2 runtime using its platform documentation, then check the matching
  tools and Python modules in the same shell.
- Match `ros_version` to the sourced runtime; do not combine ROS 1 and ROS 2
  tools.
- A top-level `import rosa` is only a package smoke check. It does not prove
  `ROSA(...)` can initialize a selected ROS family.

**Symptom:** lists are empty or return a connection error.

- Treat connection errors as middleware/master/daemon/domain/environment
  problems, not proof that the robot has no nodes or topics.
- Run the family-specific doctor/list checks, verify the sourced overlay and
  `ROS_MASTER_URI` (ROS 1) or domain/RMW/daemon context (ROS 2), then retry one
  operation at a time.

## Provider and credentials

**Symptom:** provider import error, missing key, unavailable local model, or
model refuses tool calls.

- Install only the needed `jpl-rosa[anthropic]` or `jpl-rosa[ollama]` extra;
  the OpenAI integration is in the base distribution.
- Validate the provider key/service/model outside the robot action path. Do not
  print keys or copy them into prompts.
- Use a chat model with LangChain tool-calling support. A plain text-only model
  may construct but fail when the agent binds tools.
- For Ollama, verify the service and model are reachable before constructing
  ROSA. For Anthropic, verify the extra and key. For Azure, verify deployment
  and endpoint configuration.

## API and execution behavior

**Symptom:** `invoke()` returns `An error occurred: ...`.

The synchronous method converts ordinary executor exceptions to an error
string and does not record the failed call in chat history. Inspect the inner
message, provider/tool configuration, and selected ROS family. Do not treat the
error string as a successful robot action. `KeyboardInterrupt` is propagated.

**Symptom:** `astream()` raises that streaming is disabled, or events do not
complete.

Construct with `streaming=True`, consume the async iterable in order, and
handle `token`, `tool_start`, `tool_end`, `final`, and `error` events. Streaming
errors become error events; they are not proof that the requested action ran.
For a complete synchronous string, use `invoke()` with `streaming=False`.

**Symptom:** token usage is absent.

Token display is disabled for streaming and for non-OpenAI/Azure model classes.
Set `show_token_usage=True` only for a supported non-streaming model and keep
provider billing output separate from robot state.

**Symptom:** repeated turns use stale context or memory grows unexpectedly.

`accumulate_chat_history` defaults to true. Use `clear_chat()` between tasks or
construct with `accumulate_chat_history=False` when calls must be stateless.
`return_intermediate_steps=True` increases memory use and does not change the
public `invoke()` return into a full trace.

## Input, data, and config validation

- Discover names with the appropriate list tool before passing them to info,
  echo, call, set, launch, or kill operations.
- Use exact service types and validated request syntax; do not interpolate raw
  user text into a shell-backed ROS 2 request.
- Use fully resolved ROS 1 parameter names. Store ROSA-owned memory under
  `/rosa/...` and confirm writes.
- Keep topic echoes, logs, graph rendering, and intermediate traces bounded.
  `read_log` requires a real directory/file, rejects non-positive line limits,
  and asks for a bounded slice when a file exceeds 200 lines.
- Use the calculation tools for angles, distances, and coordinates; document
  units and avoid manual geometry in action planning.

## Demo and GUI boundaries

The TurtleSim Docker demo is optional and requires Docker, a ROS image, network
access, host networking/display setup, and X11/XQuartz changes. Treat it as an
explicit integration project, not an installation smoke check. Do not run it
from a package troubleshooting path or grant display access automatically.
