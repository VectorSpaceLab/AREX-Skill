# DisCo Meta Skills

DisCo 为 **Creator 模式**内置了 15 个 skill construction workflows。这些是
Creator 专用的 meta skills，用于蒸馏、验证、维护和导出面向 Researcher 的
operating skills。它们同时也是 portable Agent Skills，因此不运行 DisCo CLI
的其他 agent 也可以遵循同一套证据、审阅和交接流程。

本文介绍的 corpus 与 [AREX-Skill
Library](../skills/README.md) 不同：后者面向 Researcher，提供执行研究任务的
operating skills；本文介绍的 skills 用来创建和维护它们。

## DisCo 支持的 Meta Skills

唯一 source of truth 是
`cli/packages/coding-agent/src/disco/skills/`。下面列出的 15 个根目录都声明
`metadata.disco-role: meta`，会在 Creator 模式中提供。

### 通用构建

| Skill | 用途 |
| --- | --- |
| `distill-ml-knowledge` | Creator 的通用入口：识别 source/task anchor，并驱动 scope、ground、construct、verify 四个阶段。 |
| `design-meta-skill` | 针对有证据支持、反复出现的构建缺口，设计并验证可复用的 meta-skill bundle。 |

### Repository Skills

| Skill | 用途 |
| --- | --- |
| `prepare-repo-skill-env` | 为仓库创建或验证隔离、具备 backend 感知能力的 Python inspection environment。 |
| `create-repo-skill` | 将仓库证据转换成自包含的 operating skill。 |
| `verify-repo-skill` | 运行 usability、evidence、static、native-check 和 import-readiness gates。 |
| `refresh-repo-skill` | 根据 upstream drift 更新已有 repository skill。 |
| `extend-repo-skill` | 为已有 repository skill 增加新的 workflow area 或更深的覆盖。 |
| `import-repo-skills-to-agent` | 将选定的 managed repository skills 和 scoped router 导出到其他 agent。 |

### Paper Skills

| Skill | 用途 |
| --- | --- |
| `create-paper-skills` | 生成并验证可复用论文复现 skills 的入口。 |
| `paper-skills-distiller` | 编排 paper source resolution、skill 生成、recovery、分析和 refinement。 |
| `plan-paper-skill-modules` | 创建 paper profile、module plan 和 module documents。 |
| `create-paper-module-skill` | 把 module document 转换成经过验证的 module skill。 |
| `prepare-paper-recovery-env` | 记录 recovery 所需的 package、model、data 和 runtime evidence。 |
| `recover-paper-result` | 使用生成的 skills 运行有边界的 recovery experiment。 |
| `analyze-paper-recovery` | 将 recovery evidence 与 paper target 对照并返回 accept/refine/blocker 反馈。 |

同级的 `repo-skills-router` 是 Researcher 模式用于渐进式路由的
`operating` skill，因此不属于这份 meta skills 清单，也不应作为 portable
Creator 安装的一部分复制。

## 在 DisCo 中使用 Meta Skills <a id="use-meta-skills-in-disco"></a>

使用 `disco --creator` 启动新的 Creator session，也可以通过 `--creator -p`
执行一次性请求。已经知道入口 skill 时，可以使用 `/skill:<name>` 显式调用。
Creator 也能根据自然语言请求自动选择入口，但显式调用更适合形成可复用、可审计
的命令。

大多数用户只需要直接调用下面这些 entry skills。Supporting skills 会由所选
workflow 自动加载，并不是需要用户手工逐项执行的 checklist。例如，
`create-repo-skill`、`refresh-repo-skill` 和 `extend-repo-skill` 会按需使用环境
准备和验证流程；`create-paper-skills` 则会把完整论文流程交给
`paper-skills-distiller` 编排。

### 蒸馏 ML 知识

当 source 类型或 construction strategy 还需要选择时，使用通用入口：

```bash
disco --creator -p "/skill:distill-ml-knowledge 识别 <source 或 task anchor>；完成 scope、ground、construct、verify。"
```

如果已有 repository 或 paper construction workflow 适用，该入口会优先复用；
只有证据表明存在反复出现的构建能力缺口时，才会转向 `design-meta-skill`。

### 创建 Repository Skill

从本地仓库创建并验证 operating skill graph：

```bash
disco --creator -p "/skill:create-repo-skill 为 /absolute/path/to/repo 创建并验证 repository skill。"
```

只有当 Creator 可以自行决定 extraction scope，并在验证成功后无需再次询问即可
导入时，才在请求中加入 `自动决定并自动导入`。否则 scope 和 deployment 仍然需要
用户确认。

### 创建论文复现 Skills

在 AREX-Skill checkout 中复制通用 starter config，并至少填写
`workspace_root`、`paper_slug` 和 `paper_source`。可选的
`original_repo_source` 可以是本地路径、Git URL、`none` 或 `unknown`：

```bash
cp examples/creator/paper-to-skills/distiller-run-config.toml \
  /absolute/path/to/distiller-run-config.toml

disco --creator -p "/skill:create-paper-skills 使用 Distiller 为该配置中的每项运行生成并验证用于论文复现的 skills。config_path: /absolute/path/to/distiller-run-config.toml"
```

`paper_source` 可以是本地 PDF 或文本文件、PDF 直链、arXiv 链接或编号，也可以
是论文标题。`create-paper-skills` 会委托 `paper-skills-distiller` 编排 source
resolution、module planning、module-skill generation、有边界的 runtime
preparation、recovery、analysis 和 refinement。普通运行不需要手工逐个调用这些
supporting paper skills。

使用 starter 的默认输出路径时，生成的 skills 位于
`<workspace_root>/<paper_slug>/skills/`，最终报告位于
`<workspace_root>/<paper_slug>/distillation/reports/final/`。昂贵的 recovery 和
最终 deployment 仍然遵循配置与 workflow 中定义的 approval boundary。输入契约
和完整 lifecycle 见 [Paper-to-Skills 示例](../examples/README.md#paper-to-skills)
与 [DisCo 工作流指南](disco-workflows.zh.md#构造论文复现技能)。

### 刷新或扩展 Repository Skill

当上游代码、API、文档、配置、依赖或行为已经变化，现有 skill 可能过期时，使用
`refresh-repo-skill`：

```bash
disco --creator -p "/skill:refresh-repo-skill 根据 /absolute/path/to/repo 的当前内容刷新 /absolute/path/to/existing-skill。"
```

当现有 skill 仍然正确，但需要增加新能力或更深覆盖时，使用
`extend-repo-skill`：

```bash
disco --creator -p "/skill:extend-repo-skill 以 /absolute/path/to/repo 为证据，为 /absolute/path/to/existing-skill 增加 streaming inference 覆盖。"
```

两个 workflow 都会保留仍然正确的既有指导、重新运行验证，并把 deployment 或
overwrite 保持为明确的 approval boundary。

### 将 Repository Skills 导出到其他 Agent

把 DisCo managed collection 中选定的 skills 连同 scoped router 导出到 Codex
推荐的用户级 skill 目录：

```bash
disco --creator -p "/skill:import-repo-skills-to-agent import vllm and sglang to ~/.agents"
```

Claude Code 使用 `~/.claude`。该 workflow 会解析准确的 skill IDs，在替换目标
已有内容前请求确认，对合并后的 collection 进行 staging 和验证，并在 transaction
失败时恢复原目标。

## 什么时候在 DisCo 之外安装

DisCo 已经内置这些 workflow。当其他兼容 agent 需要创建、验证、刷新、扩展或
导出 skills，但无法运行 DisCo CLI 时，可以安装 portable meta skills。如果需
要 mode-specific skill visibility、`/creator` 和 `/researcher`、session 隔离、
managed library、加锁导入或内置 tools，应直接安装 DisCo。

复制这些目录**不会**复现 DisCo 的 mode/session boundary；目标 agent 仍需要遵
循 skill 文本中的 role 和 approval 规则。

## 安装到 Codex

当前 Codex 用户级 Skills 的推荐目录是 `~/.agents/skills`。下面的命令只复制
15 个 meta-skill 目录，不复制 router、1,000 个仓库技能图及其生成的 sub-skills
或任何 README：

```bash
git clone https://github.com/VectorSpaceLab/AREX-Skill.git
cd AREX-Skill
mkdir -p ~/.agents/skills
for skill in \
  analyze-paper-recovery \
  create-paper-module-skill \
  create-paper-skills \
  create-repo-skill \
  distill-ml-knowledge \
  design-meta-skill \
  extend-repo-skill \
  import-repo-skills-to-agent \
  paper-skills-distiller \
  plan-paper-skill-modules \
  prepare-paper-recovery-env \
  prepare-repo-skill-env \
  recover-paper-result \
  refresh-repo-skill \
  verify-repo-skill; do
  cp -R "cli/packages/coding-agent/src/disco/skills/$skill" ~/.agents/skills/
done
```

如果要安装到项目级 Codex，把 `~/.agents/skills` 替换成
`<project>/.agents/skills`。旧版 Codex 仍可能识别用户指定的
`~/.codex/skills`，但新建或迁移时不再把它作为推荐目录。

## 安装到 Claude Code

Claude Code 的用户级 Skills 目录是 `~/.claude/skills`：

```bash
mkdir -p ~/.claude/skills
for skill in \
  analyze-paper-recovery \
  create-paper-module-skill \
  create-paper-skills \
  create-repo-skill \
  distill-ml-knowledge \
  design-meta-skill \
  extend-repo-skill \
  import-repo-skills-to-agent \
  paper-skills-distiller \
  plan-paper-skill-modules \
  prepare-paper-recovery-env \
  prepare-repo-skill-env \
  recover-paper-result \
  refresh-repo-skill \
  verify-repo-skill; do
  cp -R "cli/packages/coding-agent/src/disco/skills/$skill" ~/.claude/skills/
done
```

复制前应检查目标目录。`cp -R` 会覆盖同名内容；目标已有本地修改时，应先复
制到临时目录并比较。卸载时只删除上面列出的目录，不要删除共享的
`agents/openai.yaml`、router 或其他 user skills。

## 调整部署路径

这些 workflow 中写明的是 DisCo 的 live destinations：managed Creator skills
和可复用 operating skills 位于 `~/.disco/agent/skills/`，与项目绑定的
operating graphs 位于 `<project-dir>/.agents/skills/`。如果生成的 skill 应由
目标 agent 而不是 DisCo 管理，需要把 managed destination 映射到该 agent 的
用户级 skills root：Codex 使用 `~/.agents/skills/`，Claude Code 使用
`~/.claude/skills/`。与项目绑定或复用价值不确定的 operating graph 仍应留在
项目目录中；一个 graph 只能使用一个 scope。导入前必须让用户确认准确目标和
所有覆盖操作。

Repository graphs 仍然是特殊情况。优先使用
`import-repo-skills-to-agent`，由它保持 `repo-skills/` 与
`repo-skills-router/` 同级。其 bundled transactional helper 会合并准确的
repository 与 assignment records，重新生成根 `repository-index.jsonl` 和 scoped
router，校验 staging 与最终安装结果，并在失败时恢复原目标。中断后应使用 helper
报告的准确事务路径继续执行。不要把 repository skills 平铺到 managed root、手工
合并 router Markdown，也不要把它们的 routing metadata 交给通用
operating-graph importer。

## 复制不会提供什么

Portable meta skills 不会安装 DisCo 的 TypeScript runtime、tools、
`metadata.disco-role` filtering、mode-specific prompts、自动导入协调或
session manager。它们也不会让其他 agent 在运行 construction workflow 时自动
隐藏 operating skills。如果 bundled transaction helpers 适用于目标布局，仍
需显式调用。目标 agent 支持 role 区分时，应把 operating skills 和 meta skills
放在不同目录；对于昂贵 setup、生成 skill 的导入或覆盖操作，仍要按 workflow
要求请求用户批准。

如需完整的 Creator/Researcher 隔离，请安装
[`disco` CLI](../cli/README.md)，再单独安装
[AREX-Skill Library](../skills/README.md)。
