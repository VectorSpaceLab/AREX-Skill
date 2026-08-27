# ROS 2 troubleshooting

Use the returned tool object and the actual runtime environment as evidence.
Do not turn a mocked result into a claim about live ROS 2 middleware.

## Missing `rclpy` or `ros2`

`ros2.py` imports `rclpy.logging.get_logging_directory` at module import time.
If `rclpy` is unavailable, constructing ROSA's ROS 2 tool collection can fail
before any command runs with a `ModuleNotFoundError`. The ROS 2 Python package
and the `ros2` CLI must both be available in the same intended environment.
Installing only `jpl-rosa` does not install a ROS distro or middleware.

If the executable is absent or not on `PATH`, source the operator-selected ROS 2
distro and any workspace overlay in the process that launches ROSA, then verify
through `ros2_doctor()` and a list tool. Do not claim that nodes or topics are
missing because this host lacks them. The current inspection environment has no
`rclpy` and no `ros2`, so live commands were not run here.

The CI evidence covers a Humble container that sources its ROS environment before
running tests. README support names Humble, Iron, and Jazzy; that support claim
is not a substitute for checking the installed distro and package compatibility.

## Unsourced distro, overlay, or wrong ROS version

ROSA's `ros_version=2` selects the ROS 2 tool module but does not source a
system. A shell can contain Python dependencies while lacking ROS environment
variables, or can source a different distro/overlay than the nodes under test.
Record the selected distro, `ROS_DISTRO`, workspace overlay, Python interpreter,
and executable path through the deployment's normal diagnostics. Then run
`ros2_doctor()` and an unfiltered list sequentially.

Do not route a ROS 1 failure through this skill. For `rosnode`, `rostopic`,
`rosservice`, `rosparam`, or a ROS master/no-master error, use
[ros1-operations](../../ros1-operations/SKILL.md).

## DDS, domain, and daemon mismatch

Empty or inconsistent lists can result from a different `ROS_DOMAIN_ID`, RMW
implementation, network namespace, container boundary, firewall, stale daemon,
or an unsourced workspace. The wrappers do not expose a ROS 2 daemon-management
API: `daemon` is not in the `execute_ros_command` allowlist. Use
`ros2_doctor()`, then re-run the relevant list without filters and compare the
process environment with the publisher/service process. If an operator must
restart or repair a daemon, follow a separately approved deployment procedure;
do not smuggle `ros2 daemon ...` or a shell restart through this helper.

A successful doctor result is setup evidence, not proof that a particular node,
topic, or service exists. An empty list is an observation, not permission to
invent a name.

## Command validation and subprocess errors

The wrapper accepts only a first token of `ros2` and a second token of
`node`, `topic`, `service`, `param`, or `doctor`:

- `ros2` or another one-field command raises
  `ValueError("'<command>' is not a valid ROS2 command.")`.
- A non-`ros2` prefix raises the same message.
- `ros2 <other>` raises
  `ValueError("'ros2 <other>' is not a valid ros2 subcommand.")`.

These validation errors escape the wrapper; they are not returned as
`{"error": ...}` objects. Once the prefix is accepted, subprocess exceptions
are caught and returned through a `(False, str(exception))` tuple. The list
wrappers then put that string in a one-element list, while info/action wrappers
usually put it under an `error` key. Preserve the original string, including
messages such as `Command 'ros2 node list' returned non-zero exit status 1.`.

The validator does not parse every remaining argument. A valid category with
extra shell syntax can pass validation and reach `shell=True`; this is a source
safety limitation. Never suggest arbitrary command execution, redirection,
substitution, pipelines, launchers, or daemon control. Validate each entity,
option, and structured value before using the documented wrapper.

## Regex pattern and blacklist failures

Entity filters and node-specific parameter filters embed caller strings in
`re.match(f".*{value}.*", candidate)`. They are unescaped regex fragments, not
literal search strings. An invalid expression may raise `re.error`; a broad
expression can include unexpected entities. Blacklists remove matching values
and are applied by the wrapper, but they do not make a shell command safe.
Prefer simple, operator-approved patterns, report the filter, and use an
unfiltered list to recover from an unexpected empty result.

For all-node parameter listing, the parser filters node keys only; it does not
filter each parameter value. A node-specific listing filters the parameter lines.

## Topic echo count, timeout, and output size

`ros2_topic_echo` returns exactly `{"error": "Count must be between 1 and 10."}`
for counts outside 1–10, without invoking the command. Count is the source's
only explicit bound. Keep `delay` and `timeout` small, non-negative, and
validated because the source does not validate them. `timeout` becomes
`--spin-time` in the CLI command, but `check_output` has no Python timeout;
process or middleware behavior can still cause a long wait. A command failure
returns `{"error": "<error>"}` and stops the loop. With `return_echoes=False`,
outputs are printed but only `{"success": true}` is returned; with it enabled,
all raw outputs are collected, so use a small count.

A missing or transient topic is not evidence that the graph is empty. Re-list,
inspect topic info, check doctor/domain configuration, and retry only as a
bounded sequential diagnostic.

## Parameter parser and set edge cases

For `ros2_param_list(node_name=<node>)`, output is split on newlines and empty
strings are removed without stripping other whitespace. For `ros2_param_list()`
the parser expects slash-prefixed node headers at column zero and indented
parameter lines. A nonblank line before the first header can trigger a source
parser failure; a line beginning with `/` is treated as a new node. Malformed
CLI formatting therefore needs correction or a node-specific query, not a
confident interpretation.

`ros2_param_get` and `ros2_param_set` return the parameter name mapped to raw
stdout on success, or `{"error": "<error>"}` on failure. `set` does not parse
YAML or type-check the value and appends it raw to a shell command. Confirm the
node and parameter from discovery, inspect the current value, validate the
expected type and representation, and obtain mutation confirmation before a
write. Do not use shell syntax as a quoting workaround.

## Service type, request, and call failures

`ros2_service_call` trusts the supplied `srv_type` and request. It does not call
`ros2 service type` automatically and wraps the request in double quotes before
shell execution. Always list the service and inspect its type first. Type
inspection returns raw stdout, potentially with trailing whitespace; normalize
it and require one expected `package_name/srv/TypeName` token before use. Then
validate nested request YAML against that type. Quotes, backslashes, `$`,
backticks, semicolons, newlines, redirects, and other shell-significant text can
change what the shell executes or make the call fail. Reject such input rather
than improvising shell escaping; never pass arbitrary user text and never use a
raw `execute_ros_command` call to bypass the sequence. If the wrapper cannot
represent a legitimate request safely, do not make the call through this API.

A successful call has `{"response": "<stdout>"}`. A subprocess failure has
`{"error": "<error>"}`. A type mismatch, unavailable service, malformed
request, or DDS problem can all appear as the latter; use the prior list/type
observations and the exact error to distinguish them.

## Log directory, file, and size behavior

`roslog_list` obtains the directory from `rclpy` rather than a user-supplied
ROS variable. It scans only direct regular `.log` files, applies a full-path
regex blacklist, and keeps files strictly larger than `min_size` (default
2048 bytes). Its top-level `total` is the number of directories with qualifying
files, not the total file count. Files that are exactly at the threshold are
excluded. Missing/inaccessible directories or stat failures can propagate
because the wrapper does not convert them to structured errors.

Use the returned directory and file path, then call `read_log` with a bounded
`num_lines` value. Its exact validation/error forms include:

```text
Invalid `num_lines` argument. It must be a positive integer.
The log directory '<directory>' does not exist. You should first use your tools to get the correct log directory.
The log file '<filename>' does not exist in the log directory '<directory>'.
The path '<directory>/<filename>' is not a file.
The log file '<filename>' has more than 200 lines. Please use the `num_lines` argument to read a subset of the log file at a time.
```

The source numbers and strips each line, applies `num_lines` before the
case-insensitive substring `level_filter`, and returns metadata plus the
filtered lines. A non-positive `num_lines` is rejected before path checks. The
source does not sandbox `log_filename`; use only a trusted filename returned by
log discovery and do not use path traversal.

## Evidence and verification limit

Mocked wrapper checks verify command validation, list filters, echo bounds, and
node/parameter output shapes; separate log checks use controlled filesystem
fixtures. This evidence confirms package-level contracts but does not exercise
a live DDS graph. No ROS 2 launcher is bundled because a reusable shell wrapper
would amplify the package implementation's shell-interpolation risk.
