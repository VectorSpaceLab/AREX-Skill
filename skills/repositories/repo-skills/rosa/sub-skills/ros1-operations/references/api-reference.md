# ROS 1 ROSA API reference

These are package-level LangChain tools exposed by ROSA's ROS 1 tool module.
The descriptions below follow the implementation and mocked tests, not the
traditional CLI output. All list arguments should contain a small set of names;
first discover names and then pass confirmed values. A tool error is data to
report and troubleshoot, not evidence that a name can be fabricated.

## Graph and entity discovery

### `rosgraph_get`

`rosgraph_get(node_pattern=".*", topic_pattern=".*", blacklist=None,
exclude_self_connections=True)` queries the ROS master's system state and
returns connected publisher/topic/subscriber triples. The response on success
has this shape:

```text
{
  "graph_convention": "Each tuple in the graph is of the form (publisher, topic, subscriber).",
  "nuance": "Disconnected nodes are not included in this graph.",
  "node_count": <unique publisher/subscriber node count>,
  "topic_count": <unique topic count>,
  "total_connections": <triple count>,
  "graph": [(publisher, topic, subscriber), ...]
}
```

Only topics present in both publisher and subscriber maps create triples.
`topic_pattern` is applied as a regular expression to the complete topic name.
`node_pattern` is applied as a regular expression to either endpoint; a triple
survives when either publisher or subscriber matches. `blacklist` is a list of
regex-like substrings checked against every triple entry and removes a triple
if any word matches any publisher, topic, or subscriber. Self-connections are
removed by default. Disconnected nodes are omitted. An empty result is
`{"error": "No results found for the specified parameters. Note that the
following have been excluded: [...]"}`. A master failure is returned as
`{"error": "Failed to get ROS graph: <exception>"}`.

Do not use this function to list nodes or topics: use `rosnode_list` and
`rostopic_list`. A graph larger than 50 triples still returns data, but includes
a warning that it is too large to render and that filtering is required; do not
attempt to render it.

### `rostopic_list` and `rosnode_list`

Both accept `(pattern=None, namespace=None, blacklist=None)` and return a
metadata dictionary:

```text
{"namespace": "/" or supplied namespace,
 "pattern": supplied pattern or ".*",
 "total": <count before namespace filtering>,
 "in_namespace": <count after namespace filtering>,
 "match_pattern": <count after regex filtering>,
 "topics": [...]}
```

`rosnode_list` uses `"nodes"` instead of `"topics"`. The topic universe is the
sorted union of publisher and subscriber names from `rostopic.get_topic_list()`;
the node universe comes from `rosnode.get_node_names()`. With no arguments,
these tools request all entities. For a non-root namespace, only names starting
with `namespace + "/"` survive. The root namespace `/` is special: all names
are treated as root names and are not filtered. The implementation does not
normalize a missing leading slash, so pass a resolved ROS namespace.

`pattern` is applied with `regex.match(".*" + pattern + ".*", name)`, making it
an unanchored containment-style regex even if the caller supplies a short
pattern. Invalid regexes or middleware errors become `{"error": "Failed to
get ROS topics/nodes: <exception>"}`. `blacklist` entries use the same
containment-style regex and are applied after the shared counts are computed;
the returned list is filtered, but `match_pattern` can therefore still reflect
items removed by the blacklist.

Empty stages use explanatory singleton strings instead of an empty list. If the
whole source universe is empty: `There are currently no <type>s available in
the system.` If the namespace stage is empty: `There are currently no <type>s
available using the '<namespace>' namespace.` If the regex stage is empty:
`There are currently no <type>s available matching the specified pattern.`

### `rostopic_info`

`rostopic_info(topics: List[str])` returns a dictionary keyed by each requested
topic. Each value is:

```text
{"topic": <requested name>,
 "type": <parsed Type line or None>,
 "publishers": [<names parsed after Publishers:>, ...],
 "subscribers": [<names parsed after Subscribers:>, ...]}
```

It parses `rostopic.get_info_text`; keep the topic list small. This is a
read-only metadata lookup and should precede echoing an unfamiliar topic.

### `rostopic_echo`

`rostopic_echo(topic: str, count: int, return_echoes=False, delay=1.0,
timeout=1.0)` resolves the message class, waits for up to `count` messages,
and returns:

```text
{"topic": <topic>, "requested_count": <count>, "actual_count": <number stored>}
```

When `return_echoes=True`, it adds `"echoes": <at most 10 received messages>`
and `"truncated": <whether stored messages exceeded 10>`. The implementation
only appends messages when `return_echoes` is true, so `actual_count` is zero
when echoes are not requested even if waits succeeded. A timeout or ROS
interrupt stops the loop and returns the partial count; the tool does not add a
separate timeout error. If the topic class cannot be resolved it returns
`{"error": "Failed to get message class for topic '<topic>'"}`. The source
docstring specifies a valid count range of 1--100; keep calls in that range,
use finite timeout, and do not request large payloads.

## Nodes

### `rosnode_info`

`rosnode_info(nodes: List[str])` calls ROS node-info description for each
confirmed node and returns `{node_name: <description with newlines replaced by
spaces>}`. It is read-only and should follow `rosnode_list`.

### `rosnode_kill` — high-risk mutation

`rosnode_kill(node_names: List[str])` invokes `rosnode.kill_nodes` for every
provided name. An empty list returns
`{"error": "Please provide the name(s) of the ROS node to kill."}`. On success
it returns `{"successesfully_killed": [<successes>], "failed_to_kill":
[<failures>]}` (the misspelled key is the actual API). Exceptions return
`{"error": "Failed to kill ROS node(s): <exception>"}`. This can stop robot
behavior and should never be called from an inferred or guessed node name:
confirm the discovered name, describe the consequence, obtain authorization,
then call it one tool call at a time and verify with `rosnode_list`.

## Services and types

### `rosservice_list`

`rosservice_list(node=None, namespace=None, include_nodes=False,
regex_pattern=None, exclude_logging=True, exclude_rosapi=True,
exclude_parameters=True, exclude_pattern=None, blacklist=None)` returns the
filtered result of `rosservice.get_service_list(node, namespace,
include_nodes)`. By default it removes names beginning `/rosout`, names
containing `logger`, names beginning `/rosapi`, and names containing `param`.
This means the default list is intentionally not exhaustive. Set the exclusion
flags false only when the task calls for those service families.

When `include_nodes=False`, the result is normally a list of service names;
when true, the underlying ROS library can return `[service_name, [node]]`-style
entries. The implementation's later default exclusion, regex, and blacklist
filters assume string entries and call `startswith`/regex on each item, so
`include_nodes=True` can fail when those filters are active; treat it as an
implementation edge case and use the default string form unless node metadata
is specifically required and the returned shape is known to work. With string
entries, `exclude_pattern` removes entries matching `regex.match(".*" +
pattern, entry)`; `regex_pattern` keeps entries matching that same
containment-style expression. `blacklist` removes entries when any blacklist
pattern matches. Invalid regex or service-library errors are not wrapped by
this function, so report the tool failure. Use `node` or `namespace` only when
the scope is known.

### `rosservice_info`

`rosservice_info(services: List[str])` returns `{service_name: headers}`. For
each service it obtains a URI and then `rosservice.get_service_headers`; the
value is whatever header mapping/text the ROS library returns. Inspect this
before a call to determine the endpoint/type context and keep the list small.

### `rosservice_call` — mutation/side-effect boundary

`rosservice_call(service: str, args=None)` normalizes a falsey `args` to an
empty list, calls `rosservice.call_service(service, args)`, and returns the
raw response on success. Any exception becomes
`{"error": "Failed to call service '<service>': <exception>"}`. The wrapper
does not validate or coerce arguments. Discover the service, inspect its
metadata, inspect the corresponding type with `rossrv_info` when necessary,
construct arguments matching the request fields, explain side effects, and
obtain confirmation before invoking an unknown or mutating service.

### `rosmsg_info` and `rossrv_info`

`rosmsg_info(msg_type: List[str])` returns `{type_name:
rosmsg.get_msg_text(type_name)}`. `rossrv_info(srv_type: List[str], raw=False)`
returns `{type_name: rosmsg.get_srv_text(type_name, raw=raw)}`. `raw=False` is
the default and requests the normalized service text; `raw=True` retains
comments and whitespace. These are read-only type lookups. Use confirmed type
names from topic/service information rather than inventing package/type names.

## Parameters

### `rosparam_list`

`rosparam_list(namespace="/", blacklist=None)` returns
`{"namespace": <namespace>, "total": <filtered count>, "ros_params":
[<parameter names>]}`. It calls `rosparam.list_params(namespace)`, then removes
blacklisted names using containment-style regex. A failure returns
`{"error": "Failed to get ROS parameters: <exception>"}`. The default is the
root namespace `/`.

### `rosparam_get`

`rosparam_get(params: List[str])` returns `{fully_resolved_name: value}` for
each requested name by calling `rosparam.get_param`. Names must be fully
resolved; wildcards are not supported. The wrapper does not catch individual
lookup failures, so keep the list small and troubleshoot the first missing
parameter before retrying.

### `rosparam_set` — mutation

`rosparam_set(param: str, value: str, is_rosa_param: bool)` writes the supplied
string value with `rosparam.set_param` and returns a sentence:
`Set parameter '<resolved-name>' to '<value>'.` On failure it returns
`Failed to set parameter '<resolved-name>' to '<value>': <exception>. Try again!`.
When `is_rosa_param=True` and the name does not already start with `/rosa`, the
wrapper prefixes `/rosa/` and collapses a duplicate slash. Use this namespace
for agent-owned memory/configuration to avoid colliding with robot nodes. A
non-ROSA parameter write requires a confirmed fully resolved name, a stated
value, and explicit authorization; read it back with `rosparam_get` to verify
when appropriate.

## Packages and launch files

### `rospkg_list`, `rospkg_info`, `rospkg_roots`

`rospkg_list(package_pattern=".*", ignore_msgs=True, blacklist=None)` obtains
all package names from `rospkg.RosPack().list()`. It returns:

```text
{"total": <count before ignore_msgs>,
 "msg_pkg_count": <count removed because name ends with 'msgs'>,
 "match_pattern": <count after ignore/regex/blacklist>,
 "packages": [<sorted names>]
}
```

The default excludes package names ending in `msgs`; set `ignore_msgs=False`
when those packages matter. A non-default `package_pattern` keeps names
matching `regex.match(".*" + pattern, name)`; blacklist uses the same
containment-style expression. The counts are implementation metadata, so
`total` can exceed the returned package count.

`rospkg_info(packages: List[str])` returns a dictionary keyed by package name.
Each value always includes `path` and `dependencies`, then includes every
truthy public manifest slot from `rospkg`'s package manifest. Unknown package
errors are not wrapped. `rospkg_roots()` returns the raw list from
`rospkg.get_ros_package_path()`.

### `roslaunch_list`

`roslaunch_list(packages: List[str])` discovers files in each confirmed
package's `launch/` directory and returns:

```text
{"results": {
  "package": {"directory": <package path>, "total": <file count>,
               "launch_files": [<filenames>]}
 }, "errors": [<per-package error strings>]}
```

If every package lookup fails it returns
`{"error": "Failed to get ROS launch files for all specified packages.",
"details": [...]}`. It lists all regular files in the launch directory; no
content or safety validation is performed. Use it to enumerate candidates
before any launch.

### `roslaunch` — external high-risk action

`roslaunch(package: str, launch_file: str)` calls the host shell through
`os.system(f"roslaunch {package} {launch_file}")` and then normally reports
`Launched ROS launch file '<launch_file>' in package '<package>'.` The wrapper's
`try/except` does not turn a nonzero `os.system` status into an error, and the
launch may block while processes run. Treat package/file values as trusted,
confirmed data only; never pass user-controlled shell fragments or guessed
paths. Enumerate package and launch files first, explain that this can start
multiple processes and change the robot, obtain confirmation, call it alone,
and verify the resulting node graph. There is no bundled safe launch script.

## Logs

### `roslog_list`

`roslog_list(min_size=2048, blacklist=None)` inspects the directories returned
by `get_roslog_directories()`: the default `rospkg.get_log_dir()`, its `latest`
subdirectory, and `ROS_LOG_DIR` when set. For each existing/non-empty directory
it considers regular `.log` files, removes blacklisted paths, and includes only
files whose size is strictly greater than `min_size` bytes. The response is:

```text
{"total": <number of directory records>,
 "logs": [{"directory": <dir>, "total": <file count>,
            "files": [{"/relative.log": "3.0 KB"}, ...]}, ...]}
```

File sizes are formatted in KB below 1 MiB and MB at or above 1 MiB. `total`
is directory-record count, not total file count. Use discovered directory and
relative filename with the shared `read_log` tool; do not guess log paths.

### Shared `read_log`

`read_log(log_file_directory, log_filename, level_filter=None, num_lines=None)`
is in ROSA's shared log tool, not `ros1.py`. The directory and joined file must
exist and be a regular file. `num_lines`, when supplied, must be positive and
selects the most recent lines. Lines are returned as `line N: <content>` and
include `total_lines`, `lines_returned`, the requested filter/count, and the
file identity. If the selected slice contains more than 200 lines, the tool
returns an error asking for a smaller `num_lines`; a filter is applied after
that size guard. `level_filter` is case-insensitive substring matching. Invalid
paths, non-files, negative/zero counts, and oversized reads are explicit errors.
