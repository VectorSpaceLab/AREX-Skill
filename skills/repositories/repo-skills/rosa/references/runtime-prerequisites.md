# ROSA runtime prerequisites

Read this reference before constructing an agent or selecting a ROS family.
It separates package installation from middleware, model, and robot-runtime
requirements.

## Package and Python

- Distribution: `jpl-rosa`.
- Import: `rosa`.
- Supported Python: `>=3.9,<4`.
- Base dependencies include LangChain core/community/openai integrations,
  Pydantic, NumPy, Pillow, Rich, Azure identity, and related runtime packages.
- Optional provider extras are `anthropic`, `ollama`, and `all`. Select the
  smallest extra that matches the model provider; do not install `all` merely
  to make an import check pass.

## ROS family

The `ROSA` constructor creates default tools and then imports the selected ROS
family. A top-level `import rosa` can succeed on a machine with no ROS, while
`ROSA(ros_version=1, ...)` needs ROS 1 Python modules and a reachable master,
and `ROSA(ros_version=2, ...)` needs `rclpy`, the `ros2` executable, a sourced
ROS 2 distribution, and a discoverable DDS graph.

- ROS 1 evidence targets Noetic or newer; source the chosen installation and
  confirm its master before claiming a live graph.
- ROS 2 evidence targets Humble, Iron, or Jazzy; source the chosen installation
  and check the daemon/domain/RMW context before claiming a live graph.
- ROS 1 and ROS 2 are alternative runtime families. Do not install or source
  both blindly in one shell, and do not infer that a missing ROS runtime means
  an empty graph.

## Model and credentials

Pass a LangChain chat model with tool-calling support. The tested provider
families are OpenAI, Azure OpenAI, Anthropic, and Ollama, but other
`BaseChatModel` implementations may work when they implement the needed tool
calling contract.

- OpenAI/Azure token accounting is available only for non-streaming supported
  models; streaming disables token display.
- Anthropic needs the package extra and its API key.
- Ollama needs the package extra, a reachable local Ollama service, and a model
  already available to that service.
- Never put keys in `RobotSystemPrompts`, tool arguments, reports, or shell
  history. Resolve them from the provider's supported environment/configuration
  mechanism at runtime.

## Robot and process safety

ROSA tools can observe and mutate a real graph. Before a mutation, confirm the
current entity, type, request, target, and expected side effect. `roslaunch`,
`rosnode_kill`, service calls, and parameter writes can alter or stop a robot.
The ROS 2 wrappers ultimately invoke validated ROS 2 command strings through a
subprocess shell, so treat service request text and entity names as untrusted
input until validated. Keep actions sequential and bounded.
