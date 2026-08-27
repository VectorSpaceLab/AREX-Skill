# Troubleshooting

Use this when a CoreNLP client or helper fails before or during a Java call.

## Missing Java

Symptoms:
- `java` is not found
- `CoreNLPClient` fails with a `FileNotFoundError` or a Java launch error

Checks:
- `python scripts/check_corenlp_client.py` should report the Java executable if one is available.
- `java -version` should succeed in the same shell.

Recovery:
- Install a JRE/JDK and put `java` on `PATH`.
- Re-run the diagnostic script before attempting to start a server.

## Missing `CORENLP_HOME`

Symptoms:
- `resolve_classpath()` raises `FileNotFoundError`
- the client cannot find the CoreNLP distribution

Checks:
- Verify whether `CORENLP_HOME` is set.
- If you do not set it, the resolver falls back to the default cache path and then to `~/stanza_corenlp`.

Recovery:
- Set `CORENLP_HOME` to the CoreNLP distribution directory.
- Or pass an explicit `classpath` argument.
- If you intentionally want the environment variable route, make sure the directory exists before starting Java.

## `classpath` / `$CLASSPATH`

Symptoms:
- Java starts but CoreNLP classes are still not visible
- the client cannot resolve jars from the distribution

Checks:
- Confirm whether `classpath` was passed directly.
- Confirm whether `CORENLP_HOME` or `CLASSPATH` points at the intended jar directory.
- Remember that `resolve_classpath` expands a directory into a wildcard classpath.

Recovery:
- Use a concrete CoreNLP install directory or pass `classpath="$CLASSPATH"` only when the environment variable already contains the right jars.
- Do not mix an empty `CLASSPATH` with a missing CoreNLP install.

## Port collisions

Symptoms:
- server start fails on the configured port
- `PermanentlyFailedException` reports that the port is already in use

Checks:
- Another server may already be bound to the same host:port.
- `TRY_START` may connect to an existing server instead of launching a new one.

Recovery:
- Pick a different port.
- Use `StartServer.DONT_START` if you only want to connect to an already-running server.
- Use `StartServer.FORCE_START` only when you intend to own the port.

## Startup timeout

Symptoms:
- `Timed out waiting for service to come alive.`
- CoreNLP starts but does not answer `/ping` quickly enough

Checks:
- Large `preload` sets can slow startup.
- Small `memory` values can delay or prevent startup.
- Very large annotator pipelines can make the first ping slow.

Recovery:
- Increase the client `timeout`.
- Lower `preload` or disable it for the diagnostic pass.
- Increase `memory` and retry.

## Invalid output format or properties

Symptoms:
- `ValueError` from `validate_corenlp_props`
- CoreNLP rejects the request because `outputFormat` or properties are malformed

Checks:
- Valid output formats are: `conll`, `conllu`, `json`, `serialized`, `text`, `xml`, `inlinexml`.
- If `properties` is a dict, inspect the `outputFormat` entry too.
- If `properties` is a string, make sure it is either a supported language keyword or a path to a properties file.

Recovery:
- Run `python scripts/check_corenlp_client.py` with the intended `--output-format` and property source.
- Fix the request before starting Java so the failure stays in the safe check path.

## External server unavailable

Symptoms:
- `StartServer.DONT_START` or `start_server=False` returns `AnnotationException`
- the endpoint ping or annotate request times out

Checks:
- The endpoint may not be running.
- A firewall, reverse proxy, or wrong port may block the request.

Recovery:
- Ping the endpoint first.
- Confirm the URL matches the live server.
- Use `DONT_START` only when you expect an external server to be alive.

## Memory and threads

Symptoms:
- server startup is slow
- the JVM fails under load
- responses time out on larger inputs

Checks:
- `memory`, `threads`, and `max_char_length` are all client-side server-launch parameters.
- Large `annotators` or `preload` sets increase startup cost.

Recovery:
- Raise `memory` for large workloads.
- Reduce `threads` only if the host is oversubscribed.
- Lower `max_char_length` for quick smoke tests.

## Legacy `stanza.server.main` import error

Symptoms:
- importing or running the legacy module raises `ModuleNotFoundError: corenlp`

Cause:
- That legacy entry point imports a compatibility module that is not part of the modern client-first surface.

Recovery:
- Prefer `stanza.server.CoreNLPClient` and the bundled diagnostic script.
- Only use the legacy entry point in an environment where the compatibility alias is already installed.

## When to stop and switch tasks

If the problem is really about:
- downloading Stanza neural models or pipeline resources, switch to `pipelines-and-resources`
- notebook, browser, or demo rendering, switch to `visualization-and-demos`
- core Java distribution installation issues, stay in this sub-skill
