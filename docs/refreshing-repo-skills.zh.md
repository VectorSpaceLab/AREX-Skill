# 刷新 Repository Skills

Repository skill 描述的是某个上游仓库在特定 source baseline 下的操作知识。
由于上游代码、API、文档、示例、依赖和运行时行为会持续变化，已发布的 skill
应当被刷新，而不是永久当作固定快照。

当 skill 仍然覆盖同一个仓库，但现有指导可能已经过时时，使用 DisCo 的
`refresh-repo-skill` meta skill。如果请求是增加全新的工作流领域或更宽的能力，
应改用 `extend-repo-skill`。

## 快速开始

开始前需要准备：

- 一个包含 root `SKILL.md` 的现有 repository skill；
- 一个可作为证据的上游仓库当前 checkout；
- 至少配置了一个模型提供商的 DisCo；
- 一个允许写入的、位于 live managed skill 目录之外的 review/staging 目录。

启动交互式 Creator CLI：

```bash
disco --creator
```

在 DisCo 提示框中，提供现有 skill 路径和上游 checkout：

```text
/skill:refresh-repo-skill 根据 /path/to/upstream-repository 刷新 /path/to/AREX-Skill/skills/repositories/repo-skills/<skill-id> 中的现有 repo skill。保留仍然正确的 workflow，更新过时指导，运行验证并准备可贡献的结果，不要改变 skill identity。
```

需要一次性执行或脚本化运行时，可以使用 `-p`：

```bash
disco --creator -p "/skill:refresh-repo-skill 根据 /path/to/upstream-repository 刷新 /path/to/skill 中的现有 repo skill，保留正确指导，更新过时内容，运行验证并准备可贡献的结果。"
```

交互式形式是正常的 CLI 工作流；`-p` / `--print` 只是可选的非交互模式，适合
自动化脚本。

如果现有 skill 是
`~/.disco/agent/skills/repositories/repo-skills/` 下的 live managed copy，
应先创建外部工作副本再编辑。不要直接修改 live copy；只有在验证成功后，才审查
并批准精确的 overwrite/import。

## Refresh Workflow 的职责

`refresh-repo-skill` 按以下顺序工作：

1. 解析现有 skill、当前上游 checkout、上一份 provenance baseline 和 review artifact 目录。
2. 根据仓库证据审查现有 skill，区分仍然受支持的声明、过时或已删除的声明、新增相关行为和未解决未知项。
3. 在保留 skill 及 sub-skill identity 的前提下更新 runtime tree，除非用户明确要求更改 identity。
4. 根据刷新后的 source revision、package versions、dirty state 和仓库相对证据路径重建 `references/repo-provenance.md`。
5. 针对本次 refresh 使用的精确 source commit 解析并应用来源仓库 license 到 root 和所有 sub-skills。
6. 更新 usability cases，执行静态检查和可行的 live checks，并把 review artifacts 写到 runtime skill 之外。
7. 生成 routing handoff，并且只在所需 approval 或已授权的自动导入策略满足后，用 verified importer 替换 managed skill。

刷新应保留有价值的现有指导，但必须删除或改写当前仓库证据已经不再支持的内容。
它不是根据最新 README 进行的盲目再生成。

## 必须保持同步的内容

只有在整个 repository skill tree 及其发布元数据都经过审查后，refresh 才算完成。

### Runtime Skill Tree

更新所有受影响的公开 runtime 文件，而不只是 root `SKILL.md`：

- root `SKILL.md` 的 description、route、workflow、validation 和 troubleshooting；
- 所有受影响的 `sub-skills/**/SKILL.md`；
- `references/` 中的指令、API、配置、provenance 和来源证据；
- `scripts/` 中的 helper、check、command builder、converter 和 smoke test；
- runtime instructions 实际使用的公开 template 或小型 asset。

删除过时的源码路径、旧命令、旧配置 key、不再支持的 API、下载缓存、build output
和私有本地路径。上游 checkout 消失后，runtime 内容仍必须自包含。

### Provenance

用当前仓库状态刷新 `references/repo-provenance.md`。在可公开的范围内记录：

- 精确 source commit、branch 和 tag；
- clean/dirty 状态及仓库相对的 dirty paths；
- 相关 package 名称、版本和 import 名称；
- skill 使用的仓库相对证据路径；
- 安全的 remote，或在不应公开时使用 `omitted-private-or-unknown`。

不要把绝对本地路径、虚拟环境名称、Python executable 路径、cache、credentials
或私有 remote 写进公开 skill 文件。

### License Metadata

针对本次 refresh 的 canonical upstream repository 和精确 source commit 只解析一次
license。resolver 使用等价于以下命令的 GitHub CLI 语义：

```bash
gh api "repos/<owner>/<repo>/license?ref=<source-commit>" \
  --jq '.license.spdx_id // empty'
```

然后把同一个仓库级值写入 root 和每个 sub-skill 的 frontmatter 顶层 `license`：

```yaml
license: MIT
```

当 GitHub CLI 不存在、未认证、无法访问 API、返回 404 或没有可用结果时，写入：

```yaml
license: NO_LICENSE
```

GitHub 返回的 `NOASSERTION` 是允许的来源值，必须原样保留在 runtime tree 中。
`NO_LICENSE` 只表示本次查询没有获得可用结果，不表示已经确认上游仓库没有法律
许可。refresh 仍可以继续验证和 import，但最终报告和用户交接必须列出 repository、
source commit、status、reason，并要求用户在适当时手动补充 `NO_LICENSE`。不要让
不同 sub-agent 各自猜测 license 值。

### Routing 与 Catalog

将刷新后的 capability scope 与之前的 routing baseline 对照：

- capability scope 基本不变时保留现有 area-family assignments；
- coverage、taxonomy 或 capability scope 变化时创建新的 routing handoff；
- routing decision 变化时更新 `references/repo-routing-metadata.json` 及相关结构化记录；
- 通过 verified importer 或 updater 重建 repository router 和 indexes；
- published collection 变化时更新 `docs/imported-repo-skills.md` 及其他生成 catalog view。

不要手工编辑生成的 router Markdown，也不要只在 prose 中静默改变 skill classification。
刷新后的 skill、provenance、routing metadata 和 catalog output 必须保持一致。

### Review 与 Verification Artifacts

只检查用的 artifact 必须放在 runtime skill 之外。默认结构可以是：

```text
<upstream-repository>/skills/tests/<skill-id>/
├── test-cases/
└── reports/
```

review package 应包含 staleness audit、verification report、license-resolution report、
human-review notes、publication checklist，以及适用时的最终 routing handoff。runtime
tree 只保留未来 agent 使用该 skill 所需的文件。

## 验证清单

提交 refresh 供发布前，确认：

- root 和 sub-skills 的 frontmatter 有效，并使用相同的顶层 `license`；
- `references/repo-provenance.md` 反映刷新后的 source commit；
- 每个 Markdown link 都指向存在的 runtime 文件；
- 公开命令、API、配置 key、示例和 troubleshooting 与当前源码证据一致；
- 至少一个 usability case 覆盖刷新后的行为；
- 至少一个 regression-sensitive case 确认仍支持的旧 workflow；
- 在可行时运行安全的 native examples、tests、CLI help、imports 或 smoke checks；
- runtime tree 没有泄漏本地 checkout、credentials、cache、build output 或临时文件；
- routing metadata、生成 router view、repository indexes 和 catalog 条目一致；
- 所有 `NO_LICENSE` warning 和 accepted unknown 都出现在最终报告中；
- verified runtime tree 仍处于 staging，直到精确的 import/overwrite 获得批准。

对于 managed DisCo import，使用结构化 `verify-repo-skill` importer。它会替换获得批准
的精确 skill，并在共享 import lock 下重建同级 router。不要手工组合 copy、overwrite
和 router-update 命令。

## Pull Request 要求

公开贡献应把验证后的 runtime tree 放到：

```text
skills/repositories/repo-skills/<skill-id>/
```

refresh PR 应说明发生了什么变化，并提供足够证据让 reviewer 可以复现或审计。至少包括：

- **Skill identity：** `skill-id`、repository identity，以及受影响的 root/sub-skills；
- **上游 baseline：** repository URL、旧 source commit/tag、新 source commit/tag、branch 和 refresh date；
- **变更摘要：** 删除的过时声明、更新的指导、新增 workflow、移除的行为和有意保留的内容；
- **生产方式：** DisCo `refresh-repo-skill`、手工编辑或复制 workflow skills；多轮时逐一说明；
- **模型信息：** model、provider、reasoning/thinking level，以及多模型时每个模型的角色；
- **验证：** 实际命令、tests、imports、CLI checks、native examples、usability prompts 和 review steps；
- **环境限制：** skipped checks、不可用凭据、可选依赖、硬件限制、网络限制和已知未知项；
- **Routing 影响：** area-family assignments 是否保留或改变、原因，以及 router/indexes/catalog 是否重建；
- **License 结果：** license 值或 `NO_LICENSE`、精确 source commit、查询状态、失败原因，以及 root/sub-skills 使用同一值的确认；
- **Review artifacts：** staleness audit、verification report、license report、usability cases 和最终 handoff 的路径。

简洁的 PR 摘要可以使用：

```markdown
## Refresh Summary

- skill: <skill-id>
- upstream repository: <owner>/<repo>
- previous source commit: <old-commit>
- refreshed source commit: <new-commit>
- refreshed areas: <areas>
- routing: retained | reclassified
- license: <value>

## Verification

- commands/checks: <list or report path>
- usability cases: <path>
- known gaps: <none or details>
- review artifacts: <path>
```

## 常见错误

- 只更新 root `SKILL.md`，却留下过时的 sub-skills 或 references；
- source baseline 已变化，但继续保留旧 provenance commit；
- 没有针对精确 source commit 重新查询 license；
- 把 `NO_LICENSE` 当成法律结论，或不在最终报告中说明；
- 手工编辑生成 router Markdown，而不是更新结构化 routing metadata 后重建；
- 把 test cases、reports 或 benchmark notes 放入 runtime skill；
- 上游发生 drift 时错误使用 `extend-repo-skill`；
- 未验证的 working tree 直接导入 live managed directory。

## 相关文档

- [`refresh-repo-skill`](../cli/packages/coding-agent/src/disco/skills/refresh-repo-skill/SKILL.md)：内置 workflow contract 和 references；
- [`DisCo Workflows`](disco-workflows.zh.md)：Creator/Researcher workflow 上下文；
- [`贡献指南`](../CONTRIBUTING_CN.md)：仓库级贡献规则；
- [`Imported Repo Skills Catalog`](imported-repo-skills.md)：已发布 repository graphs 及其上游 baseline。
