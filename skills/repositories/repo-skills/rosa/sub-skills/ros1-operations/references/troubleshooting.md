# ROS 1 troubleshooting

Treat errors and empty results as observations. Do not fill an unavailable ROS
system with guessed names or claim live verification from mocked tests.

## Missing Python modules or ROS master

- `ros1.py` imports `rosgraph`, `rosmsg`, `rosnode`, `rosparam`, `rospkg`,
  `rospy`, `rosservice`, and `rostopic` at module load. If the package reports
  `ModuleNotFoundError`, the ROS 1 tool family cannot be used in that process.
  The current inspection environment is intentionally missing these modules;
  this skill therefore has source and mocked-test evidence only, not live ROS
  verification. Install/use a compatible ROS 1 Noetic-or-newer runtime through
  the deployment owner rather than pretending a Python-only substitute is live.
- If list tools return `Failed to get ROS ...` or `rosgraph_get` returns
  `Failed to get ROS graph: ...`, check that the ROS 1 environment is sourced,
  the expected ROS master URI is reachable, and the current process can use the
  ROS Python packages. Do not conclude “no nodes” from a transport/import
  error.
- The repository's Noetic CI job sources its ROS environment before running
  tests. That proves the intended test environment, not availability in every
  user process.

## Empty systems and namespaces

- A successful list with `total: 0` and the explanatory no-entity string means
  the tool observed an empty source universe. A namespace or pattern message
  means the source had entities but the selected filter matched none. Keep
  those cases distinct from a tool error.
- `namespace` defaults to root (`/`) in list tools. The implementation treats
  `/` specially and includes all absolute names. A non-root namespace keeps only
  names beginning with `namespace + "/"`; passing `namespace="robot"` does not
  normalize it for you. Reuse an exact resolved namespace from discovery.
- Counts describe stages: `total` is before namespace filtering,
  `in_namespace` after namespace filtering, and `match_pattern` after pattern
  filtering. Blacklist filtering happens after those counts, so a returned list
  may be shorter than `match_pattern`.
- If a namespace result is unexpectedly empty, retry once with the default root
  list (one tool call at a time), then report whether the entity is outside the
  requested namespace. Do not change ROS names to make a match.

## Regex and blacklist behavior

- List patterns are Python/`regex` regular expressions embedded in a
  containment-style match. A short pattern such as `camera` can match a name
  containing that text; anchors and special characters still have regex
  meaning. `rosgraph_get` applies its node pattern to endpoints and topic
  pattern to topics. Package/service/parameter/log blacklists use similar
  regex-like matching but their exact wrapping differs; narrow and escape
  patterns when names contain regex metacharacters.
- An invalid regex can be surfaced as a wrapped list error or an unwrapped
  service/package failure, depending on the tool. Simplify or correct the
  pattern; do not retry an unknown pattern repeatedly.
- A blacklist can remove every result and can also hide the selected target.
  Record the blacklist in the explanation, temporarily narrow it only with
  authorization, and never bypass a safety or privacy blacklist merely to get
  a result.

## Graph size, self-connections, and disconnected entities

- `rosgraph_get` only creates edges for topics that have both publishers and
  subscribers. It omits disconnected nodes and topics by design; use list and
  info tools for inventory.
- With `exclude_self_connections=True` (the default), a node publishing and
  subscribing to the same topic is removed. Set it false only when that edge is
  specifically relevant.
- More than 50 graph triples yields a `warning` that the graph is too large to
  display/render. Do not render or dump it. Filter by a confirmed node/topic
  regex, blacklist noise, or ask which subsystem the user wants before making
  another sequential call.
- An empty graph error can mean no connections, filters that excluded all
  triples, self-connections only, or an unavailable master. Check list-tool
  results and the error text before diagnosing.

## Topic echo limits and timeouts

- Resolve the message class first. `Failed to get message class for topic ...`
  means the topic is unavailable or its type cannot be loaded; rediscover and
  inspect it before retrying.
- Keep `count` within the documented 1--100 range, use finite `timeout`, and
  use a small delay. A topic that publishes slowly may produce a partial result
  when `rospy.wait_for_message` times out. The tool returns `requested_count`
  and `actual_count` and stops without a dedicated timeout field.
- The implementation only increments/stores the count when
  `return_echoes=True`; therefore `actual_count: 0` with `return_echoes=False`
  is not proof that no messages arrived. With echoes enabled, at most ten are
  returned and `truncated` says whether more were collected.
- Do not request large echo payloads. If a caller needs a sample, one or a few
  messages with `return_echoes=True` is safer than a large count.

## Services, types, and arguments

- The default `rosservice_list` intentionally filters `/rosout`, `/rosapi`,
  logger-like names, and names containing `param`. A missing expected service
  may be excluded rather than absent; change the relevant exclusion flag only
  when the user asks for that family.
- Inspect `rosservice_info` and, when needed, `rossrv_info` before a call. The
  call wrapper passes `args` directly to `rosservice.call_service` and performs
  no request-field validation. A type/arity/serialization exception should be
  reported; do not retry a potentially mutating request with guessed values.
- An empty `args` list is valid only for a service whose request is empty. For a
  request with fields, construct values from the actual service definition and
  confirm the side effect. `rosservice_info` returns the underlying headers,
  not a normalized custom schema.

## Parameters and ROSA namespace

- `rosparam_get` requires fully resolved names and does not support wildcards.
  Start with `rosparam_list`, then copy exact names. Underlying lookup failures
  are not wrapped per item, so use small batches.
- For agent memory/configuration, call `rosparam_set` with
  `is_rosa_param=True`; a name without `/rosa` is rewritten under `/rosa/`.
  This avoids taking ownership of another node's parameter. For a robot-owned
  parameter, use `False` only with a confirmed target and explicit approval.
- The set API takes `value: str`; the underlying ROS library determines how the
  value is stored. Read it back when safe. A sentence beginning `Failed to set`
  is a failed operation, not a request to keep retrying blindly.

## Packages, launch, and shell risk

- `rospkg_list` excludes names ending in `msgs` by default and uses counts that
  describe pre/post filtering stages. Set `ignore_msgs=False` for message
  package discovery. If a package cannot be resolved, use `rospkg_roots` and
  the runtime package path to diagnose sourcing, then rediscover.
- `roslaunch_list` reports per-package errors and lists regular files in a
  package's `launch/` directory; it does not parse or validate launch content.
  A package with no launch directory can have a successful zero-file record.
- `roslaunch` uses `os.system` with interpolated package/file text. It can block,
  start many processes, and accept shell-sensitive input. Treat it as an
  external high-risk mutation: only use names returned by discovery, never
  paste arbitrary shell fragments, obtain confirmation, invoke it alone, and
  verify nodes afterward. A normal success sentence does not prove the shell
  command returned zero because the wrapper does not inspect the status.
- The Docker/X11 TurtleSim demo is reference-only and is not a safe diagnostic
  or runtime dependency. Do not launch it while diagnosing package-level API
  behavior.

## Logs and bounded reads

- `roslog_list` examines the default ROS log directory, its `latest` child, and
  `ROS_LOG_DIR` when set. It includes only `.log` regular files strictly larger
  than `min_size` (default 2048 bytes). A result with `total: 0` can mean no
  qualifying files, not necessarily no logs. Lower the threshold only when
  needed and permitted.
- Discover the directory and relative filename first. `read_log` rejects a
  missing directory, missing file, and non-file path. It rejects `num_lines < 1`
  and refuses to return more than 200 selected lines; request a positive small
  recent slice instead. It prefixes each returned line with its source line
  number.
- `level_filter` is a case-insensitive substring filter applied after the
  200-line guard. If it returns no lines, the level may be absent; it does not
  imply the log file is empty. `total_lines` describes the whole file while
  `lines_returned` describes the filtered response.

## Mutations and confirmation

- Never call a service, set a non-ROSA parameter, launch a file, or kill a node
  from an inferred name. List first and inspect the exact target.
- `roslaunch` and `rosnode_kill` have external process effects and require the
  strongest confirmation. For kill, report both `successesfully_killed` and
  `failed_to_kill`; follow with `rosnode_list`. For launch, expect blocking or
  multiple new nodes and verify after control returns.
- All calls remain sequential. If a prior tool has no result, was interrupted,
  or returned an error, diagnose or repeat the necessary read-only discovery
  call before any next action.
