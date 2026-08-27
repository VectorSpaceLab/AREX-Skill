# Workflows

Use these recipes to keep CoreNLP work separated into safe checks and live Java actions.

## 1) Safe environment check

Use this when you only need to know whether the Python side of the integration is ready.

1. Run `python scripts/check_corenlp_client.py --help`.
2. Run the script without `--start-server` to check imports, Java discovery, classpath resolution, and property validation.
3. Add `--ping-endpoint http://host:port` only if you want a network reachability check against an existing server.

This path should not launch Java.

## 2) Validate request settings before a live call

Use this when you already know the output format and properties you want.

1. Pick one of the allowed output formats: `conll`, `conllu`, `json`, `serialized`, `text`, `xml`, `inlinexml`.
2. Decide whether `properties` is a language keyword, a properties file, or a dict.
3. Check the pair with `validate_corenlp_props(...)` or the bundled script before starting a client.
4. If the configuration is a dict, make sure any `outputFormat` entry matches the allowed set.

## 3) Reuse an existing CoreNLP server

Use this when CoreNLP is already running somewhere and you only need the client.

```python
from stanza.server import CoreNLPClient, StartServer

with CoreNLPClient(
    start_server=StartServer.DONT_START,
    endpoint="http://localhost:9000",
    annotators="tokenize,ssplit,pos",
) as client:
    ann = client.annotate("A small test.", output_format="json")
```

Guidance:
- Keep `start_server=DONT_START` so the client does not try to launch Java.
- Ping the endpoint first if you need a quicker fail.
- Catch `AnnotationException` and `TimeoutException` for unavailable or slow servers.

## 4) Start a local managed server

Use this when you own the Java process and want the client to manage it.

1. Confirm `java` is on `PATH`.
2. Confirm `CORENLP_HOME` or an explicit classpath resolves to a CoreNLP distribution.
3. Choose a local endpoint like `http://localhost:9000`.
4. Set `memory`, `threads`, `preload`, and `max_char_length` conservatively for the task.
5. Use the client in a context manager so it stops cleanly.

Good pattern:
- `StartServer.FORCE_START` for a guaranteed local launch.
- `StartServer.TRY_START` if you want to reuse an existing local server when one is already bound.

## 5) Use serialized protobuf output

Use this when downstream code needs a `Document`.

1. Request `output_format="serialized"`.
2. Receive a `stanza.protobuf.Document`.
3. Pass the document into doc-based helpers such as `stanza.server.semgrex.process_doc`, `stanza.server.ssurgeon.process_doc`, or `stanza.server.morphology`.

## 6) Run a pattern engine on a Stanza document

Use this when you already have a `Document` from Stanza's neural pipeline.

1. Parse text with `stanza.Pipeline`.
2. Run the relevant helper:
   - `semgrex.process_doc(doc, ...)`
   - `ssurgeon.process_doc(doc, ...)`
   - `tsurgeon.process_trees(trees, ...)`
   - `Morphology(...).process(words, tags)`
3. Decide whether to keep all sentences or only the matching ones.
4. Convert or print the result.

## 7) Install or refresh CoreNLP files

Use this only when the task explicitly needs the CoreNLP distribution or model jars.

1. Choose a directory and make sure it is writable.
2. Run `install_corenlp(...)` for the distribution zip or `download_corenlp_models(...)` for a language model jar.
3. Set `CORENLP_HOME` to the install directory when the install is not using the default cache.
4. Re-run the environment check before switching back to client work.

## Decision rule

- If you only need to inspect or validate the Python surface, stay in the safe check workflow.
- If a Java process must run, require an explicit server-start decision and a known classpath.
- If the task is really about Stanza model downloads or pipeline setup, hand it to the `pipelines-and-resources` sub-skill instead.
