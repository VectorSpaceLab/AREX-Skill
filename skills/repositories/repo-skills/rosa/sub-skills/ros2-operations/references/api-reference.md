# ROS 2 API reference

These contracts are distilled from the ROSA ROS 2 wrapper and its mocked unit
tests. A successful mocked call proves wrapper behavior only; it does not prove
that a ROS 2 graph, daemon, DDS participant, or message exists at runtime.

## Command boundary: `execute_ros_command`

`execute_ros_command(command: str) -> tuple[bool, str]` is the common wrapper.
It splits the string with `command.split(" ")` and validates only the first two
space-delimited fields:

- Fewer than two fields raises
  `ValueError("'<command>' is not a valid ROS2 command.")`.
- A first field other than `ros2` raises the same error.
- The second field must be exactly one of `node`, `topic`, `service`, `param`,
  or `doctor`; otherwise it raises
  `ValueError("'ros2 <subcommand>' is not a valid ros2 subcommand.")`.
- For an accepted prefix it calls
  `subprocess.check_output(command, shell=True).decode()`.
- On success it returns `(True, decoded_stdout)`, preserving stdout including
  newlines.
- Any exception from the subprocess is caught and returned as
  `(False, str(exception))`. For example, a mocked
  `CalledProcessError(1, "ros2 node list")` produces an error containing
  `Command 'ros2 node list' returned non-zero exit status 1.`.

The category check is an allowlist, not a complete parser: extra tokens after a
valid category are not independently validated. The implementation still uses
`shell=True`; do not treat this function as a safe arbitrary shell runner and
do not pass unvalidated names, options, YAML, redirects, substitutions, or
metacharacters.

## List tools and shared filters

`ros2_node_list(pattern: str | None = None, blacklist: list[str] | None = None)`
returns `{"nodes": [...]}` after executing `ros2 node list`.

`ros2_topic_list(pattern: str | None = None, blacklist: list[str] | None = None)`
returns `{"topics": [...]}` after executing `ros2 topic list`.

`ros2_service_list(pattern: str | None = None, blacklist: list[str] | None = None)`
returns `{"services": [...]}` after executing `ros2 service list`.

All three use the same `get_entities` behavior:

- A command failure is represented as a one-element list containing the raw
  error string, for example `{"nodes": ["Invalid command"]}`.
- Successful output is split on newline, empty/whitespace-only entries are
  removed, and remaining strings are otherwise preserved.
- `pattern`, when supplied, is used as a regular expression fragment in
  `re.match(f".*{pattern}.*", entity)`, so it is a substring-style regex, not
  an exact match. It is not escaped; invalid regex syntax can raise.
- Each `blacklist` entry is applied with the same regex-fragment behavior and
  removes matching entries. Filtering is applied after splitting and before
  the empty-entry removal result is returned. A blacklist takes precedence over
  a matching inclusion pattern.

The lists are observations, not proof that a name remains available after the
call. Re-list before acting if the graph may have changed.

## Node and topic information

`ros2_node_info(nodes: list[str]) -> dict` executes one command per supplied
name, sequentially:

```text
ros2 node info <node_name>
```

For each name it returns either the raw output string or an error object:

```json
{
  "<node_name>": "<stdout>"
}
```

or

```json
{
  "<node_name>": {"error": "<subprocess error>"}
}
```

There is no entity-name validation or implicit list. Only pass names confirmed
by a recent node list, and do not assume a list containing an error is an empty
ROS graph.

`ros2_topic_info(topics: list[str]) -> dict` is analogous, executing:

```text
ros2 topic info <topic> --verbose
```

Its success and failure shapes are the same per-topic mapping. `--verbose` is
always appended by the wrapper.

## Bounded topic echo

`ros2_topic_echo(topic: str, count: int = 1, return_echoes: bool = False,
delay: float = 1.0, timeout: float = 1.0) -> dict` builds:

```text
ros2 topic echo <topic> --once --spin-time <timeout>
```

The wrapper validates `count` before executing anything:

- `count < 1` or `count > 10` returns exactly
  `{"error": "Count must be between 1 and 10."}`.
- For each requested message it invokes the command once, prints the raw
  output, and sleeps for `delay` seconds (including after the final iteration).
- A failed iteration returns immediately as `{"error": "<error>"}`.
- With `return_echoes=True`, success is
  `{"echoes": ["<stdout-1>", "<stdout-2>", ...]}`. Newlines are preserved.
- With `return_echoes=False`, success is `{"success": true}` and the printed
  output is not included in the returned object.

The source does not validate `delay` or `timeout`, and it does not pass a
Python subprocess timeout. Keep both bounded and non-negative in caller input;
a blocked command can therefore outlive the nominal spin time depending on the
CLI/process behavior. `--once` means each subprocess attempts one message, so
`count=3` is three sequential command invocations, not one unbounded stream.

## Services

`ros2_service_info(services: list[str]) -> dict` checks the type of each service
with:

```text
ros2 service type <service_name>
```

It returns a per-service raw output string on success or
`{"error": "<error>"}` on failure, under the service name:

```json
{"<service_name>": "<type stdout>"}
```

or

```json
{"<service_name>": {"error": "<error>"}}
```

The success value is raw stdout and can retain a trailing newline. Before using
it as `srv_type`, remove only surrounding CLI whitespace and validate that the
result is one expected ROS 2 service-type token (for example,
`std_srvs/srv/Empty`); do not forward raw output or a multi-token value into a
shell command.

`ros2_service_call(service_name: str, srv_type: str, request: str) -> dict`
constructs a shell command with the request surrounded by double quotes:

```text
ros2 service call <service_name> <srv_type> "<request>"
```

It returns `{"response": "<stdout>"}` on success or
`{"error": "<error>"}` on failure. The wrapper does not discover or validate
the type and does not parse YAML itself. First call service list and type
inspection, normalize and validate the returned type token, then validate the
request against that type. Because the request is shell-interpolated, reject
embedded quotes, `$`, backticks, semicolons, redirects, newlines, and other
shell syntax rather than improvising shell escaping; never forward arbitrary
user text as a request. If a legitimate request cannot be represented safely by
this wrapper, do not call it through this API.

## Parameters

`ros2_param_list(node_name: str | None = None, pattern: str | None = None,
blacklist: list[str] | None = None) -> dict` has two distinct parsers.

With a node name it executes `ros2 param list <node_name>`. Successful output
is split on newline and nonempty entries are returned without stripping their
remaining whitespace:

```json
{"<node_name>": ["param1", "param2"]}
```

`pattern` and `blacklist` use the same unescaped substring-style regex matching
as entity lists, but are applied to parameter entries in this node-specific
path. A command failure is `{"error": "<error>"}`.

Without a node name it executes `ros2 param list` and parses the expected
indented form:

```text
/node_a
  parameter_a
  parameter_b
/node_b
  parameter_c
```

A line beginning at column zero with `/` starts a node key; every other
nonblank line is stripped and appended to the current node. The result is:

```json
{
  "/node_a": ["parameter_a", "parameter_b"],
  "/node_b": ["parameter_c"]
}
```

In the all-node path, `pattern` and `blacklist` filter **node keys**, not the
individual parameter lists. A malformed output with a nonblank parameter line
before any slash-prefixed node can fail in the source parser; a slash-prefixed
parameter-like line is interpreted as a new node. A command failure remains
`{"error": "<error>"}`.

`ros2_param_get(node_name: str, param_name: str) -> dict` executes
`ros2 param get <node_name> <param_name>` and returns
`{"<param_name>": "<stdout>"}` or `{"error": "<error>"}`.

`ros2_param_set(node_name: str, param_name: str, param_value: str) -> dict`
executes `ros2 param set <node_name> <param_name> <param_value>` and has the
same success/error shape as `ros2_param_get`. The value is appended raw; the
wrapper does not quote, type-check, or serialize it. Treat this as a mutation
and validate the target, expected type, and value before calling.

## Doctor

`ros2_doctor() -> dict` executes exactly `ros2 doctor` and returns
`{"results": "<stdout>"}` on success or `{"error": "<error>"}` on failure.
Use it to surface setup/discovery issues, but do not treat a successful doctor
run as proof that a requested entity exists.

## ROS 2 log discovery and reading

`ros2_log_directories()` is a helper, not a LangChain `@tool` in the source. It
calls `rclpy.logging.get_logging_directory()`, prints the selected path, and
returns `{"default": "<log_dir>"}`. `roslog_list(min_size: int = 2048,
blacklist: list[str] | None = None) -> dict` calls that helper and then:

- skips an empty directory value;
- lists direct children only, keeping regular files whose names end in `.log`;
- applies blacklist regex fragments to the **full path**;
- keeps files whose size is strictly greater than `min_size` (not equal);
- formats each file as `{ "<f.replace(log_dir, '')>": "<size> KB" }` or
  `"<size> MB"`, rounded to two decimal places. The key is a raw string
  replacement result and commonly begins with `/`; it is not guaranteed to be
  a safe relative filename.
- returns one entry per directory with `directory`, `total` (qualifying files),
  and `files`, wrapped in `{"total": <number of directories>, "logs": [...]}`.

It prints intermediate paths. Directory/list/stat errors are not converted to
an error object by this wrapper and may propagate. Use a discovered directory
rather than guessing one.

The shared `read_log(log_file_directory: str, log_filename: str,
level_filter: Literal["ERROR", "INFO", "DEBUG", "WARNING", "CRITICAL",
"FATAL", "TRACE"] | None = None, num_lines: int | None = None) -> dict` tool
then reads one file:

- `num_lines` below 1 returns
  `{"error": "Invalid `num_lines` argument. It must be a positive integer."}`.
- A missing directory returns
  `{"error": "The log directory '<directory>' does not exist. You should first use your tools to get the correct log directory."}`.
  A missing file returns
  `{"error": "The log file '<filename>' does not exist in the log directory '<directory>'."}`.
  A path that is not a file returns
  `{"error": "The path '<os.path.join(directory, filename)>' is not a file."}`.
- Lines are numbered from one and stripped, for example
  `line 2: ERROR: message`. `total_lines` counts all lines before slicing.
- `num_lines` selects the most recent lines. After slicing, more than 200 lines
  returns an error asking the caller to use `num_lines`; use a positive value
  no greater than 200 for bounded reads.
- `level_filter` is applied after slicing as a case-insensitive substring test.
- A normal result contains `log_filename`, `log_file_directory`,
  `level_filter`, `requested_num_lines`, `total_lines`, `lines_returned`, and
  `lines`. An empty file succeeds with `lines: []`.

The source joins the supplied directory and filename with `os.path.join` and
performs no sandbox or path-traversal check. An absolute filename overrides the
directory under normal `os.path.join` semantics, which matters because
`roslog_list` commonly returns a leading-slash replacement key. Pass only a
trusted, discovered log directory and a validated relative filename; do not
blindly feed the raw key back as an absolute filename.
