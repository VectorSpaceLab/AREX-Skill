---
name: corenlp-client
description: "Operate Stanza's CoreNLP client, Java server lifecycle, pattern
  engines, and CoreNLP install helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

Use this sub-skill when a task involves Java Stanford CoreNLP through Stanza's Python wrapper.

Covers:
- `CoreNLPClient`, `StartServer`, local server startup, external server connections, `endpoint`, `timeout`, `threads`, `memory`, `preload`, and `classpath` handling.
- `annotators`, CoreNLP properties, output formats, serialized protobuf annotations, `update`, `tokensregex`, `semgrex`, `tregex`, and `scenegraph` requests.
- Document/tree pattern helpers: TokensRegex, Semgrex, Tregex, Ssurgeon, Tsurgeon, and the English morphology helper.
- CoreNLP distribution/model-jar helpers: `install_corenlp`, `download_corenlp_models`, and `resolve_classpath`.

Start safely:
- Run `python scripts/check_corenlp_client.py --help` to inspect the diagnostic helper.
- By default that script checks Python imports, Java discovery, classpath/`CORENLP_HOME`, and output-property validation without starting a server.
- It only starts a Java CoreNLP server when `--start-server` is explicitly provided.

Detailed references:
- [API reference](./references/api-reference.md)
- [Pattern engines](./references/pattern-engines.md)
- [Workflows](./references/workflows.md)
- [Troubleshooting](./references/troubleshooting.md)

Boundaries:
- Do not bundle Stanford CoreNLP jars or model jars in this skill.
- Route Stanza neural pipeline/model downloads and ordinary `Pipeline` resource setup to the `pipelines-and-resources` sub-skill.
- Route browser, notebook, and UI visualization work to the `visualization-and-demos` sub-skill.
