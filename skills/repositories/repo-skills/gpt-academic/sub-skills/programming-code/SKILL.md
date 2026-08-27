---
name: programming-code
description: "Operate GPT Academic source-code analysis, notebook, Markdown
  translation, and Python docstring workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Programming and Code

Use this sub-skill when a GPT Academic task is about understanding, documenting, translating, or summarizing source code or technical Markdown.

## Trigger phrases

Read this sub-skill for “解析整个Python项目”, “analyze this repo/codebase”, “explain the source code”, “add docstrings”, “注释Python项目”, “批量生成函数注释”, “Jupyter Notebook分析”, “README translation”, “Markdown翻译”, “custom file patterns”, or “too many source files”.

## First decisions

1. Identify the input: server-local folder, uploaded archive, GitHub/Markdown URL, notebook file, or single code snippet.
2. Pick the plugin by language or output: source-code architecture, docstrings/comments, notebook report, Markdown translation.
3. For large trees, plan file patterns before running expensive LLM calls:

```bash
python sub-skills/programming-code/scripts/plan_code_analysis.py <source-tree> --max-files 512
```

4. Ask before destructive transformations such as adding docstrings to source files. Prefer a copy or clean version-control state.

## Route map

| User goal | GPT Academic workflow | Read next |
| --- | --- | --- |
| analyze a code project | language-specific `解析整个*项目` plugin | `references/workflows.md`, `references/file-patterns.md` |
| manually choose source file suffixes | `解析项目源代码（手动指定和筛选源代码文件类型）` | `references/file-patterns.md` |
| add Python docstrings/comments | `注释Python项目` or `批量生成函数注释` | `references/workflows.md`, `references/troubleshooting.md` |
| analyze notebooks | `解析Jupyter Notebook文件` | `references/workflows.md` |
| translate README/Markdown | `翻译README或MD`, `Markdown翻译（指定翻译成何种语言）` | `references/workflows.md` |
| execute generated code or shell commands | not this sub-skill | route to `../agent-tooling/SKILL.md` |

## Boundaries

- Paper PDFs, LaTeX papers, Word docs, and scholarly documents belong to `../academic-docs/SKILL.md`.
- Natural-language plugin dispatch, Code Interpreter execution, and shell automation belong to `../agent-tooling/SKILL.md`.
- Provider setup, normal chat, and RAG belong to `../conversation/SKILL.md`.
- Media artifacts and Manim animation belong to `../multimodal-media/SKILL.md` unless the task is just analyzing source code for those artifacts.
