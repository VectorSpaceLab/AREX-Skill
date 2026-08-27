# API reference

This reference distills the CoreNLP client source, tests, demos, and installed signature inspection for the installed package.

## Primary surfaces

| Area | Symbols | Notes |
| --- | --- | --- |
| Client lifecycle | `CoreNLPClient`, `StartServer`, `resolve_classpath`, `validate_corenlp_props` | Safe first pass is import/classpath/property validation. Live Java starts only when the client is allowed to start a server. |
| Install helpers | `install_corenlp`, `download_corenlp_models` | Download the Stanford CoreNLP distribution or language model jars. Do not confuse these with Stanza neural model downloads. |
| Protobuf access | `annotate(..., output_format="serialized")`, `update`, `stanza.protobuf.Document`, `to_text` | Serialized output is a `Document`; text-like formats return strings; JSON-like endpoints return dicts. |
| Pattern helpers | `tokensregex`, `semgrex`, `tregex`, `scenegraph`, `Morphology`, `Semgrex`, `Ssurgeon`, `Tsurgeon` | Some operate on raw text through the server; others operate on Stanza `Document` or tree objects directly. |

## CoreNLPClient

`CoreNLPClient` is the main Python wrapper around the Java Stanford CoreNLP server.

Important constructor defaults from the installed package:
- endpoint: `http://localhost:9000`
- timeout: `60000` ms
- threads: `5`
- output format: `serialized`
- memory: `5G`
- max char length: `100000`

Key behavior:
- `start_server=StartServer.FORCE_START` starts a local Java server.
- `StartServer.TRY_START` reuses an already-running server when possible.
- `StartServer.DONT_START` never launches Java and only talks to the configured endpoint.
- Boolean `start_server=True/False` is deprecated; prefer `StartServer` values.
- `properties` may be a language keyword, a properties file path, or a Python dict.
- Dict properties are written to a temporary `.props` file for server startup.
- `annotators` and `output_format` at call time override client defaults.

Installed signature snapshot from the prepared environment:
- `CoreNLPClient(start_server=StartServer.FORCE_START, endpoint='http://localhost:9000', timeout=60000, threads=5, annotators=None, pretokenized=False, output_format=None, properties=None, stdout=None, stderr=None, memory='5G', be_quiet=False, max_char_length=100000, preload=True, classpath=None, **kwargs)`
- `CoreNLPClient.annotate(self, text, annotators=None, output_format=None, properties=None, reset_default=None, **kwargs)`

Request precedence in `annotate`:
1. explicit `annotators` / `output_format` args
2. request `properties`
3. client defaults from construction
4. server defaults

Common return shapes:
- `annotate(..., output_format="serialized")` → `stanza.protobuf.Document`
- `annotate(..., output_format="json")` → JSON dict
- `annotate(..., output_format in {"text", "conllu", "conll", "xml"})` → string
- `tokensregex`, `semgrex`, `tregex`, `scenegraph` → JSON dict; `scenegraph` requires a recent CoreNLP server (4.5.5+)
- `update(doc, ...)` → `Document`

## Property and classpath helpers

### `resolve_classpath(classpath=None)`
- If `classpath` is `"$CLASSPATH"`, or `CORENLP_HOME` is exactly `"$CLASSPATH"`, it resolves from the environment `CLASSPATH` variable.
- Otherwise it prefers `classpath`, then `CORENLP_HOME`, then the default `~/stanza_corenlp` path.
- For a directory path, it appends `*` so the Java launcher sees the full jar set.
- If the resolved path does not exist, it raises `FileNotFoundError`.

### `validate_corenlp_props(properties=None, annotators=None, output_format=None)`
- Validates the output format against the supported set:
  `conll`, `conllu`, `json`, `serialized`, `text`, `xml`, `inlinexml`.
- If `properties` is a dict and contains `outputFormat`, that value is checked too.
- It is a basic guard, not a full CoreNLP schema validator.

### `read_corenlp_props` / `write_corenlp_props`
- `read_corenlp_props(path)` loads simple `key=value` pairs and ignores blank lines and comment lines.
- `write_corenlp_props(props_dict, file_path=None)` writes dicts to `.props` files and joins list values with commas.
- The client uses temporary props files internally when a dict is passed as `properties`.

### CoreNLP properties forms
- language keyword: `english`, `german`, `spanish`, `french`, `italian`, `hungarian`, `chinese`, `arabic`, and shorthands like `en`, `de`, `fr`, `es`, `it`, `hu`, `zh`, `ar`
- properties file path: a `.props` file or a CoreNLP distribution file on the classpath
- dict: handy for short inline configs and custom annotator/output format combinations

## Install helpers

### `install_corenlp(dir=..., url=..., version="main")`
- Downloads the CoreNLP zip, unpacks it, and flattens the extracted tree into `dir`.
- Warns if the destination directory already exists and is non-empty.
- This is for the Java CoreNLP distribution, not for Stanza neural models.

### `download_corenlp_models(model, version, dir=..., force=True)`
- Downloads a single Stanford CoreNLP model jar for the requested language/model.
- Supported models in the installed package include Arabic, Chinese, English-extra, English-kbp, French, German, Hungarian, Italian, and Spanish.
- The default destination comes from `CORENLP_HOME` or the package cache.

## Direct Java helpers

### `Morphology`
- `process_text(words, xpos_tags)` and `Morphology(...).process(words, xpos_tags)` talk to the Java morphology helper through protobuf.
- The helper expects PTB/XPOS tags, not UPOS.
- It is English-only in practice.

### `Semgrex`, `Ssurgeon`, `Tsurgeon`
- These are Java protobuf subprocess helpers that keep a Java process open for repeated requests.
- They use `JavaProtobufContext` and the `-multiple` protocol.
- They are suited to repeated graph/tree edits once a classpath is available.

## Distinguishing text vs document workflows

- `client.tokensregex(...)` and `client.semgrex(...)` operate on raw text through the CoreNLP server.
- `stanza.server.tokensregex.process_doc(...)` and `stanza.server.semgrex.process_doc(...)` operate on a Stanza `Document` and its graphs.
- `client.tregex(..., trees=...)` can work from tree objects directly.
- `stanza.server.ssurgeon.process_doc(...)` rewrites a Stanza `Document` and preserves dependency/MWT details when the response supports it.

Use this reference with [Pattern engines](./pattern-engines.md) and [Workflows](./workflows.md) when deciding whether a task is a safe Python check or a live Java server action.
