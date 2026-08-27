# Built-in Tools

smolagents provides built-in `Tool` subclasses for common agent tasks. Import them from `smolagents` or `smolagents.default_tools` depending on application style.

## Default Toolbox Behavior

Agents can be constructed with `add_base_tools=True` to add base tools. The mapping includes the Python interpreter, DuckDuckGo search, and webpage visiting tools. `FinalAnswerTool` is added by agents as the `final_answer` tool unless replaced.

For `ToolCallingAgent`, `add_base_tools=True` can add a `python_interpreter` tool because JSON tool-calling agents do not otherwise execute Python code. For `CodeAgent`, Python code execution is part of the agent paradigm; execution and import restrictions belong to the execution-and-safety sub-skill.

## Tool Catalog

| Tool | Name | Inputs | Output | Dependencies and notes |
| --- | --- | --- | --- | --- |
| `FinalAnswerTool` | `final_answer` | `answer: any` | `any` | Used to terminate workflows and return the final answer. Can be subclassed to customize final-answer behavior. |
| `UserInputTool` | `user_input` | `question: string` | `string` | Calls `input(...)`; use only in interactive contexts where blocking for user input is acceptable. |
| `PythonInterpreterTool` | `python_interpreter` | `code: string` | `string` | Evaluates Python code with configured authorized imports and timeout; route security questions to execution-and-safety. |
| `DuckDuckGoSearchTool` | `web_search` | `query: string` | `string` | Requires `ddgs`; supports `max_results`, `rate_limit`, and DDGS kwargs; can fail on no results or network issues. |
| `VisitWebpageTool` | `visit_webpage` | `url: string` | `string` | Requires `requests` and `markdownify`; fetches URL, converts HTML to Markdown, truncates long content. |
| `GoogleSearchTool` | `web_search` | `query: string`, optional `filter_year: integer` | `string` | Requires provider credentials such as SerpAPI or Serper; shares the `web_search` name with other search tools, so avoid collisions. |
| `WebSearchTool` / API search variants | usually `web_search` | `query: string` | search results | Provider-specific API search; check required credentials and package extras. |
| `WikipediaSearchTool` | `wikipedia_search` | `query: string` | `string` | Requires `wikipedia-api`; requires a meaningful user agent. |
| `SpeechToTextTool` | `transcriber` | `audio: audio` | `string` | Pipeline tool backed by Transformers; requires Transformers/Torch-related extras and model resources. |

## Common Usage

```python
from smolagents import CodeAgent, DuckDuckGoSearchTool, InferenceClientModel, VisitWebpageTool

agent = CodeAgent(
    tools=[DuckDuckGoSearchTool(max_results=3), VisitWebpageTool(max_output_length=12000)],
    model=InferenceClientModel(),
)
```

For interactive tools:

```python
from smolagents import ToolCallingAgent, UserInputTool

agent = ToolCallingAgent(tools=[UserInputTool()], model=model)
```

For a custom final answer tool:

```python
from smolagents.default_tools import FinalAnswerTool

class CheckedFinalAnswerTool(FinalAnswerTool):
    def forward(self, answer):
        if not answer:
            raise ValueError("Final answer cannot be empty.")
        return answer

agent.tools["final_answer"] = CheckedFinalAnswerTool()
```

## Dependency Notes

Install only the optional packages needed by the chosen tools:

- `DuckDuckGoSearchTool`: `ddgs`.
- `VisitWebpageTool`: `requests` and `markdownify`.
- `WikipediaSearchTool`: `wikipedia-api`.
- `SpeechToTextTool` and other `PipelineTool` subclasses: Transformers, Torch, Accelerate, and model-specific resources.
- MCP integrations: MCP and MCP adapter extras.
- LangChain conversion: LangChain plus provider-specific packages such as search provider SDKs.
- Hub and Space loading: Hugging Face Hub and, for Spaces, Gradio client dependencies.

## Name Collisions

Several search tools use `name = "web_search"`. Since `agent.tools` is keyed by name, adding two `web_search` implementations means one overwrites the other. Rename subclasses when multiple search providers must coexist:

```python
from smolagents import DuckDuckGoSearchTool

class FastDuckDuckGoSearchTool(DuckDuckGoSearchTool):
    name = "fast_web_search"
```

## Output Handling

Built-in tools generally return strings except final-answer and multimodal/pipeline tools. If passing built-ins to `ToolCallingAgent`, make sure the model provider supports the tool schema and return modality. If passing tools to `CodeAgent`, descriptions should make clear whether the returned string is Markdown, search snippets, Python stdout, or an error message.
