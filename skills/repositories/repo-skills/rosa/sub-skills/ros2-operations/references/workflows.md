# ROS 2 workflows

These are tool-first operating procedures. They deliberately avoid hard-coded
entity names: replace each angle-bracket placeholder only with a value returned
by a preceding discovery step.

## Establish the runtime first

1. Select `ROSA(ros_version=2, ...)` through the parent
   [agent-core route](../../agent-core/SKILL.md). Confirm the intended ROS 2 distro
   (Humble, Iron, or Jazzy) and source that distro in the process environment
   before constructing or invoking ROSA. ROSA does not source `/opt/ros/...`
   or configure a shell on your behalf.
2. Confirm that the process has the intended `ROS_DOMAIN_ID`, RMW implementation,
   workspace overlays, and permissions. A shell that is sourced for one distro
   or domain can see a different graph from another shell.
3. Run `ros2_doctor()` as the first bounded observation when setup, discovery,
   or a command error is uncertain. Record its returned `results` or `error`;
   do not infer a graph from the doctor result.
4. If ROSA construction itself fails with missing `rclpy`, or the helper cannot
   find `ros2`, stop and follow [troubleshooting](troubleshooting.md). Do not
   compensate by issuing arbitrary shell commands through
   `execute_ros_command`.

The current Creator inspection environment lacks both `rclpy` and `ros2`. The
procedures below are runtime guidance, not a live verification claim.

## Inspect the graph before using a name

Execute each tool in a separate turn and wait for its result. A safe general
sequence is:

1. `ros2_node_list()` for current nodes.
2. `ros2_topic_list()` for current topics.
3. `ros2_service_list()` for current services.
4. Use `ros2_node_info(nodes=[<confirmed-node>])` only for a node returned by
   step 1.
5. Use `ros2_topic_info(topics=[<confirmed-topic>])` only for a topic returned
   by step 2. The wrapper requests verbose information.
6. Use `ros2_service_info(services=[<confirmed-service>])` to discover the type
   before considering a call.

Patterns and blacklists are useful for narrowing a large list, but they are
unescaped regular-expression fragments. Prefer a narrow, validated pattern and
report the filter used. An empty result means “nothing matched this observation”
not “the ROS system has no entities.” If a list returns an error value, use the
error to correct the environment or command and retry once; never silently
replace it with a fabricated entity.

## Read a bounded topic sample

1. List topics and confirm the requested topic is present.
2. Optionally inspect it with `ros2_topic_info` to confirm publishers and type.
3. Call `ros2_topic_echo(topic=<confirmed-topic>, count=<1..10>,
   return_echoes=<needed>, timeout=<small-positive>, delay=<bounded>)`.
4. Keep `return_echoes=True` only when the bounded response is needed. The
   wrapper starts one `--once` subprocess per message and sleeps after each
   iteration, so larger counts and delays add up.
5. Treat `{"error": ...}` as an observation that the command or topic failed;
   do not report a message as received unless the result contains the actual
   echo or a success from the tool.

For a health check, use one message and a short, explicitly bounded timeout.
For a diagnostic sample, use only as many messages as the user needs and never
exceed the source limit of ten.

## Inspect and change a parameter

1. List parameters with `ros2_param_list(node_name=<confirmed-node>)` after
   confirming the node. If the target is unknown, use `ros2_param_list()` and
   identify the node key from its parsed output.
2. Apply `pattern` or `blacklist` only after understanding whether the node-
   specific or all-node parser is being used. In the all-node form these filters
   select node keys, not parameter values.
3. Use `ros2_param_get(node_name=<confirmed-node>, param_name=<confirmed-param>)`
   and inspect the returned value and error state.
4. Before a write, confirm the exact node, parameter, intended type, and new
   value with the operator. Then call
   `ros2_param_set(node_name=<confirmed-node>, param_name=<confirmed-param>,
   param_value=<validated-value>)` once, sequentially.
5. Re-list or get the parameter after the write to observe the result. The
   source appends `param_value` raw to a shell command; do not pass untrusted
   YAML, spaces, substitutions, or shell syntax.

Use the `/rosa` namespace for ROSA's own memory parameters if a separate
workflow asks ROSA to persist state, as required by the repository prompts.
Do not use that namespace to hide an operator's requested mutation.

## Call a service safely

1. List services and confirm the exact service name.
2. Run `ros2_service_info(services=[<confirmed-service>])`. Its success value is
   raw stdout, so strip surrounding CLI whitespace and validate exactly one ROS
   2 type token such as `package_name/srv/TypeName`; reject extra tokens or shell
   syntax.
3. Validate the request structure against that type. For nested ROS 2 request
   YAML, preserve the expected field names and types and reject ambiguous or
   shell-significant text.
4. Ask for confirmation before a call that resets, moves, changes, or otherwise
   mutates a system. Then call
   `ros2_service_call(service_name=<confirmed-service>, srv_type=<confirmed-type>,
   request=<validated-request>)` in its own sequential step.
5. Report the returned `response` or `error` exactly enough for the operator to
   distinguish a service response from a subprocess failure.

The helper surrounds `request` with double quotes and invokes a shell. It is
not a YAML or shell escaping layer. Never “test” a request by adding shell
syntax, and never use `execute_ros_command` to bypass the service wrapper. If a
legitimate request requires shell-significant content that this wrapper cannot
represent safely, stop instead of improvising an escape; a separately reviewed
non-shell custom integration belongs in
[tool-customization](../../tool-customization/SKILL.md).

## Diagnose discovery, DDS, and domain problems

Use this bounded sequence when lists are unexpectedly empty or inconsistent:

1. Run `ros2_doctor()` and retain the result.
2. Re-run one relevant list tool, such as `ros2_node_list()` or
   `ros2_topic_list()`, without a pattern or blacklist.
3. Compare the process's sourced distro, workspace overlay, `ROS_DOMAIN_ID`,
   RMW setting, and network/container boundary with the producing nodes. Do not
   claim an entity is absent until this comparison is complete.
4. If the evidence points to a stale or mismatched ROS 2 daemon, use the
   deployment's documented ROS 2 daemon-recovery procedure outside this
   helper, then repeat doctor and lists. `daemon` is not one of the helper's
   allowed command categories, and this skill does not provide an arbitrary
   restart launcher.
5. Keep each observation sequential so the reported environment corresponds to
   the same discovery attempt.

## Inspect logs without guessing paths

1. Call `roslog_list(min_size=<validated-size>, blacklist=<validated-patterns>)`
   to discover the default ROS 2 log directory and qualifying `.log` files.
   The default threshold is 2048 bytes and the comparison is strictly greater.
2. Select a returned directory and file entry; do not invent a path or scan an
   unrelated directory. The file key is produced by a raw string replacement
   and commonly begins with `/`. Normalize it to the validated relative
   filename before passing it to `read_log`; an absolute filename would cause
   `os.path.join` to ignore the discovered directory.
3. Call the shared `read_log` tool with that directory and validated filename.
   Use `num_lines` between 1 and 200 for a bounded tail, then optionally apply
   a level filter such as `ERROR`.
4. If a file is larger than 200 lines, request a smaller tail rather than
   reading the whole file. Treat missing directories, missing files, and
   non-file paths as tool errors, not as empty logs.
5. Preserve the returned line numbers and metadata when reporting findings.

Log discovery and reading are filesystem observations, not proof that a ROS
node is currently alive. Do not expose credentials or copy sensitive log
contents into an unrelated command.
