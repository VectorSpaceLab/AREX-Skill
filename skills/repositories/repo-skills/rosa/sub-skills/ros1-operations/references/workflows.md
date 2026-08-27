# ROS 1 operating workflows

These are tool-selection procedures, not commands to paste into a source
checkout. ROSA invokes the package-level tools after its ROS 1 tool set is
constructed. Every step is one tool call; wait for its result before making the
next call. Middleware prerequisites must be satisfied first.

## Universal discovery-first sequence

1. Confirm that the request is ROS 1. If it names ROS 2, `ros2`, DDS, or a ROS
   2 distro, route to [ros2-operations](../../ros2-operations/SKILL.md) instead of
   translating names between APIs.
2. For a general status/action request, call `rosnode_list()` and then
   `rostopic_list()` with no filters. For a service request, call
   `rosservice_list()` as a separate follow-up. Do not start with a guessed
   `/node`, `/topic`, or `/service`.
3. Narrow a list only after the broad result is known: use a confirmed
   namespace, a valid regex pattern, or a blacklist that intentionally removes
   noise. A list result containing an explanatory “no ... available” string is
   not an entity name.
4. Before `rostopic_echo`, `rosservice_call`, `rosparam_set`, `roslaunch`, or
   `rosnode_kill`, inspect the selected object or package. Before a service
   call, inspect its service information and request/response definition when
   the arguments are not already unambiguous. Before launch, enumerate package
   files with `roslaunch_list`.
5. For any external or state-changing action, state the target and effect,
   obtain confirmation unless the user gave clear authorization, invoke only
   that tool, and report its actual response. Re-list/re-read to verify when
   the operation has an observable graph or parameter effect.

Never make parallel ROSA calls. This is required even for apparently
independent list calls and is especially important for launch, service, and
node actions.

## Nodes and topics

### Inventory and inspect

- Start with `rosnode_list()` and `rostopic_list()`. Use their default `/`
  namespace for the common case; do not add a namespace merely because the
  entity names begin with `/`.
- For a known robot scope, pass the exact resolved non-root namespace (for
  example, a namespace already returned by discovery). Remember that the
  implementation retains names only when they start with `namespace + "/"`;
  `/` is special and includes all names.
- Use `rosnode_info([confirmed_node])` for node publications/subscriptions and
  `rostopic_info([confirmed_topic])` for the topic type and endpoint names.
  Keep each list small.
- Use `rosgraph_get` only after the list calls when the question is about
  connectivity. Filter by node/topic regex or blacklist if needed. Do not use
  it to answer “what nodes/topics exist,” because it omits disconnected
  entities.

### Bounded observation

After `rostopic_list` and `rostopic_info` confirm the topic, call
`rostopic_echo` with a small count (1--100), finite timeout, and an appropriate
delay. Request `return_echoes=True` only when the caller needs the actual
messages, because the response retains at most ten. Interpret `actual_count`
as the number stored by the implementation; with `return_echoes=False` it will
remain zero even when waits may have succeeded. A partial count indicates a
timeout or ROS interrupt may have ended the loop.

## Graph filtering

For a connected-graph question:

1. List nodes and topics first to establish available names.
2. Call `rosgraph_get` with `node_pattern` and/or `topic_pattern` only when the
   unfiltered graph would be too broad. The patterns are regular expressions;
   the implementation wraps the node pattern in a match against each endpoint
   and applies the topic pattern to the topic name.
3. Add a blacklist for known noise or sensitive names. It applies to every
   triple entry, not only node names.
4. Keep `exclude_self_connections=True` unless the user explicitly needs
   self-publishing/subscribing edges.
5. If the response includes the >50-connection warning, do not render it.
   Recommend narrower node/topic filters and make another single graph call.
   An error means no connected matching triples (or master failure), not that
   all nodes/topics are absent.

## Services and calls

1. Call `rosservice_list()` and retain only a service name from the returned
   list. The default deliberately omits `/rosout`, `/rosapi`, logger-like, and
   parameter-related services. Change exclusions only for an explicit need.
2. Call `rosservice_info([service])` to inspect endpoint metadata. If the
   request fields/types are not clear, use the confirmed service type with
   `rossrv_info([type])` before building arguments.
3. Explain whether the call is read-only or can alter robot/system state.
   Validate each argument against the service definition; the wrapper passes
   the list through without local validation.
4. Obtain confirmation for consequential calls, then call
   `rosservice_call(service, args)` alone. Report the raw response or explicit
   error. Do not retry a mutating call blindly.

## Parameters

1. Call `rosparam_list(namespace="/")`, or use a confirmed scope. Apply a
   blacklist when the parameter set contains unrelated or sensitive entries.
2. Pass only fully resolved names from the list to `rosparam_get`; never use
   wildcards. Read a small set and report missing-name errors explicitly.
3. For agent-owned state, call `rosparam_set` with `is_rosa_param=True`. The
   wrapper prefixes `/rosa/` when needed. Use a fully resolved non-`/rosa`
   name with `is_rosa_param=False` only after confirming ownership and getting
   authorization.
4. State the exact string value and target. After a successful write, call
   `rosparam_get` on the resolved name to verify if the parameter is safe to
   read back. The set wrapper returns a sentence even though ROS parameter
   typing/coercion is handled by the underlying library.

## Packages and launch files

1. Use `rospkg_list()` to discover package names. The default excludes package
   names ending in `msgs`; disable `ignore_msgs` when message packages matter.
   Use a regex or blacklist only after identifying the relevant package family.
2. Call `rospkg_info([confirmed_package])` for its path, dependencies, and
   available truthy manifest fields. Use `rospkg_roots()` when diagnosing
   package-path resolution.
3. Call `roslaunch_list([confirmed_package])` and inspect the returned launch
   filenames. A missing launch directory is a valid zero-file result; a package
   lookup failure is an error to troubleshoot.
4. `roslaunch` is an external, high-risk shell-backed action. It can block and
   can start multiple processes. Use only a confirmed package and filename,
   never interpolate arbitrary user text, explain side effects, obtain
   confirmation, invoke it alone, and verify the new graph with list tools.
   There is no bundled launch script that makes it safe.

## Logs

1. Call `roslog_list()` to discover log directories and files. Increase
   `min_size` to reduce noise or use a blacklist for known irrelevant paths.
   The returned file keys are relative to each directory record.
2. Select a directory and file from that response. Use the shared `read_log`
   tool with a positive `num_lines` for a bounded recent slice; add a
   case-insensitive `level_filter` such as `ERROR` only after selecting a
   manageable slice. Read no more than 200 selected lines at a time.
3. If the file path or directory is absent, rediscover instead of guessing.
   Report empty log directories separately from a missing ROS master or missing
   ROS log environment.

## Safe node shutdown

1. List nodes and choose only an exact, confirmed node name.
2. Call `rosnode_info([node])` to understand the target and its connections.
3. Explain that `rosnode_kill` can interrupt robot behavior and ask for
   explicit confirmation unless the user already authorized killing that exact
   node.
4. Call `rosnode_kill([node])` as the only action, report both success and
   failure lists, then call `rosnode_list` to verify whether it disappeared.
   Do not claim a node was killed because the tool was requested; trust only the
   returned lists and follow-up observation.
