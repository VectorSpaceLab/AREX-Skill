# OWL Public API Reference

Read this file when the task requires exact exported names or signatures rather
than route selection.

## `owl.utils` exports

The package's utility initializer exports:

- `extract_pattern(content: str, pattern: str) -> Optional[str]`: returns the
  stripped text between matching `<pattern>...</pattern>` tags or `None`.
- `OwlRolePlaying` and `OwlGAIARolePlaying`: OWL variants of CAMEL role-playing;
  they accept keyword arguments and create or reconcile user/assistant agents.
- `run_society(society, round_limit: int = 15) -> Tuple[str, List[dict], dict]`.
- `arun_society(society, round_limit: int = 15) -> Tuple[str, List[dict], dict]`.
- `DocumentProcessingToolkit(cache_dir: Optional[str] = None, model: Optional[BaseModelBackend] = None)`.
- `GAIABenchmark(data_dir: str, save_to: str, processes: int = 1)`.

`DocumentProcessingToolkit.extract_document_content(document_path: str)`
returns `Tuple[bool, str]` in its annotation, although direct JSON/XML paths
can return structured values inside the tuple. `GAIABenchmark.run` and its
scoring methods are detailed in the GAIA sub-skill.

## Example composition names

The documented examples use `camel.models.ModelFactory`,
`camel.agents.ChatAgent`, `camel.societies.Workforce`, `camel.tasks.Task`,
`camel.toolkits.FunctionTool`, `CodeExecutionToolkit`, `ExcelToolkit`,
`SearchToolkit`, `BrowserToolkit`, `FileToolkit`, and OWL's
`DocumentProcessingToolkit`. Exact model enum names can change with the CAMEL
version; inspect the installed release before copying a model constant.

## Runtime observations

The inspected package metadata identifies distribution `owl` version `0.0.1`,
requires Python `>=3.10,<3.13`, and pins `camel-ai[owl]==0.2.84`. The runtime
inspection required an MCP 1.x line (`mcp<2`) for CAMEL's `FastMCP` import; a
successful metadata resolution alone is not a sufficient compatibility check.
