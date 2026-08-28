# 面向其他 Agent 的可移植 Meta Skills

DisCo 为 **Creator 模式**内置了一组 skill construction workflows。这些内容
也是 portable Agent Skills，因此不运行 DisCo CLI 的其他 agent 仍然可以遵循同
一套证据、审阅和交接流程。这条安装路径与
[Research Skills Library](../skills/README.md) 不同：library
面向 Researcher，提供执行研究任务的 operating skills；本文的 skills 用来创
建和维护这些 operating skills。

## 什么时候安装

当其他 agent 需要创建、验证、刷新、扩展或导出 skills，但无法安装 DisCo 时，
可以安装 portable meta skills。如果需要 mode-specific skill visibility、
`/creator` 和 `/researcher`、session 隔离、managed library、加锁导入或内置
tools，应直接安装 DisCo。

复制这些目录**不会**复现 DisCo 的 mode/session boundary；目标 agent 仍需要遵
循 skill 文本中的 role 和 approval 规则。

## 当前内置 Meta Skills

唯一 source of truth 是
`cli/packages/coding-agent/src/disco/skills/`。当前 Creator corpus 包含以下
15 个 skills：

| Skill | 用途 |
| --- | --- |
| `distill-ml-knowledge` | Creator 的通用入口：拥有共享 task/construction contract，并选择 direct、reuse-existing（单一或组合）或 design-reusable。 |
| `design-meta-skill` | 消费经过验证且会重复出现的 gap handoff，设计参数化 reusable meta-skill bundle，不重复路径判断。 |
| `prepare-repo-skill-env` | 为仓库创建或验证隔离的 Python inspection environment。 |
| `create-repo-skill` | 将仓库证据转换成自包含 operating skill。 |
| `verify-repo-skill` | 运行 usability、evidence、static、native-check 和 import-readiness gates。 |
| `refresh-repo-skill` | 根据 upstream drift 更新已有 repository skill。 |
| `extend-repo-skill` | 为已有 repository skill 增加新的 workflow area。 |
| `import-repo-skills-to-agent` | 把 managed operating skills 和 scoped router 导出到其他 agent。 |
| `create-paper-skills` | 生成并验证可复用论文复现技能的入口。 |
| `paper-skills-distiller` | 编排 paper source resolution、论文复现技能生成、recovery、分析和 refinement。 |
| `plan-paper-skill-modules` | 创建 paper profile、module plan 和 module documents。 |
| `create-paper-module-skill` | 把 module document 转换成经过验证的 module skill。 |
| `prepare-paper-recovery-env` | 记录 recovery 所需的 package、model、data 和 runtime evidence。 |
| `recover-paper-result` | 使用生成的 skills 运行有边界的 recovery experiment。 |
| `analyze-paper-recovery` | 将 recovery evidence 与 paper target 对照并返回 accept/refine/blocker 反馈。 |

这 15 个目录都声明 `metadata.disco-role: meta`。同级的
`repo-skills-router` 是 `operating` skill，不应作为本文安装的一部分复制。

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
`repo-skills-router/` 同级，并为实际导出的 skills 生成对应 router。不要把
repository skills 平铺到 managed root，也不要把它们的 routing metadata 交给
通用 operating-graph importer。

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
[Research Skills Library](../skills/README.md)。
