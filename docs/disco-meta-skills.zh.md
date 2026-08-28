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
