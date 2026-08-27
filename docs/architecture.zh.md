# 架构说明

AREX-Skill 把已发布技能库与负责路由、使用、创建和维护它的 DisCo runtime
分开。

## 当前仓库快照

```text
AREX-Skill/
  README.md
  README.zh-CN.md
  CONTRIBUTING.md
  CONTRIBUTING_CN.md
  docs/
  skills/
    README.md
    repositories/
      repo-skills/
      repo-skills-router/
  scripts/
  cli/
```

当前 checkout 同时包含已发布的 skill library 和 DisCo TypeScript 源码树。
更广义的 library 边界是 `skills/`；当前 checkout 的
repository skill collection 位于 `skills/repositories/repo-skills/`，同级
还有 `skills/repositories/repo-skills-router/`。bundled 与 portable DisCo
workflows 的唯一 source of truth 位于
`cli/packages/coding-agent/src/disco/skills/`。

## 源码布局

DisCo 源码树位于 `cli/`：

```text
cli/
  package.json
  npm-shrinkwrap.json
  docs/
  examples/
  scripts/
  packages/
    coding-agent/
      UPSTREAM_SOURCE.md
      UPSTREAM_MANIFEST.json
      src/
      test/
```

源码树职责：

| 路径 | 职责 |
| --- | --- |
| `cli/package.json` | 唯一可发布的 npm package `@auto-ml-skills/disco`，暴露 `disco` CLI 和 SDK。 |
| `cli/packages/coding-agent/src` | DisCo copy 并修改的 Pi coding-agent runtime，包含 interactive/print modes、project trust、sessions、tools、skill discovery、workflow skills 和 dynamic orchestration。 |
| `cli/packages/coding-agent/test` | 从 upstream 保留的测试和 DisCo regression contracts。 |
| `cli/docs` 与 `cli/examples` | 随 npm package 发布的文档和示例。 |
| `cli/scripts` | asset copying、upstream provenance verification 和 package-content verification。 |

`cli/package.json` 是 standalone public package 的版本与发布入口。
`cli/packages/coding-agent/` 是带 provenance 的 source subtree，不是嵌套 npm
workspace。DisCo 不依赖 `@earendil-works/pi-coding-agent`；它自行维护 copied
coding-agent runtime，并把固定版本的 `@earendil-works/pi-agent-core`、
`@earendil-works/pi-ai` 和 `@earendil-works/pi-tui` 作为普通依赖。用户另行安装
的 Pi CLI 与全局 packages 不会进入 DisCo 的依赖或资源发现边界。

## 运行时任务执行

DisCo 是 research-first agent，而不只是 skill authoring tool。它使用现有
agent loop、file/command tools、软件实现和实验来端到端完成研究目标，也使用
同一执行循环处理独立的软件请求。Researcher 是默认 session role；Creator
是显式的 construction role。

Runtime skill discovery 包括：

- `~/.disco/agent/skills/` 下由 DisCo 管理的用户级 skills；
- `~/.agents/skills/` 下共享的用户级 skills；
- 项目获得信任后，`<project>/.disco/skills/` 以及当前项目或其上级目录中的
  `.agents/skills/`；
- 从 npm、git、HTTPS/SSH 或本地 packages 安装的 skills；
- bundled DisCo workflow skills。

managed library 可以包含数百个 repo skills，而不填满初始 model context。
repo-skill roots 使用 `disable-model-invocation: true`，因此仍会注册用于显式
`/skill:<name>` 调用，但不会出现在 model-visible skill list 中。
启动页 `Skills` 区域只报告这个 model-visible 集合，不展开全部已注册 skills；
显式 skill command completion 仍使用完整集合。`repo-skills-router` 默认保持
model-visible，并提供 area-family progressive disclosure：

1. 读取 router 并选择一个或两个可能相关的 taxonomy area。
2. 只读取相关 area 页面，再比较匹配的 family 页面。
3. 通过 `../repo-skills/<skill-id>/SKILL.md` 解析选中的 repository skill。
4. 只读取任务需要的 sub-skills、references 或 scripts。
5. 根据当前 checkout 和环境执行并验证任务。

`~/.disco/agent/skills/repositories/repo-skills-router/` 中的 live router 优先于 bundled
fallback template。它的 repository collection 是同级的
`~/.disco/agent/skills/repositories/repo-skills/`；updater 不会扫描 Creator meta skills 或
无关的 user skills。选中的指导需要根据 provenance、当前源码、installed
version 和实际 command results 做检查。

`disco repo-skills install` 与 `disco repo-skills update` 按 skill ID 管理官方
collection。manager 在 `~/.disco/agent/repo-skills-library.json` 中记录官方 commit
和摘要，在 DisCo agent directory 内维护 shallow source cache，并在 fetch 前检查
cache 保存的 origin；不属于官方 manifest 的 Creator/user skill ID 会被保留。
`status` 不联网，会检查托管摘要、router 是否存在以及 live skill coverage。source
preparation 在共享 repo import lock 之外完成；进入该锁后会重新读取 live state，
再用支持 rollback 的 staged skill tree 和 router 完成替换。

`disco repo-skills router disable` 只会在 live router 中加入
`disable-model-invocation: true`，从而关闭模型自动选择，但继续允许显式执行
`/skill:repo-skills-router`。router updater 会在单 skill import 和整个 collection
update 后保留该 live policy；canonical library output 和导出给其他 agent 的 router
默认仍保持 model-visible。

### Creator 与 Researcher 边界

每个 DisCo session 只有一个 role。Creator 加载标记为
`metadata.disco-role: meta` 的 skills 和显式跨模式的 `shared` utilities，包括
`distill-ml-knowledge`、
`design-meta-skill` 以及 repository/paper construction workflows。
Researcher 加载 `operating` skills 和 `shared` utilities，包括 router、导入的
repository graphs 和 task-related operating skills。缺少 role metadata 的 skill 被视为
user/third-party operating skill，只在 Researcher 中可用；显式非法 role 在
两种 role 中都排除。role filtering 发生在 name collision、command
registration 和 prompt construction 之前。`shared` 的可见性不会放宽任一模式的
任务边界；bundled construction artifacts 与 generated operating artifacts 仍
分别严格使用 `meta` 和 `operating`。

Creator 首先从 `distill-ml-knowledge` 开始。它拥有通用的 task/construction
词汇，评估可见的单一流程与有边界的组合，并选择 `direct`、
`reuse-existing` 或 `design-reusable`。只有有证据证明会重复出现的构造能力缺口
才进入 `design-meta-skill`；后者消费准确的 routing handoff，不再重复充分性或
路径判断。入口在选择前只记录轻量 routing contract；选中的 direct 或
reusable-bundle 分支再负责自己的 exact construction specification。通过审批的
新 meta skill 是可复用的 Creator 基础能力，安装到
`~/.disco/agent/skills/<meta-skill-id>/`。它以后生成的 operating graph 需要
单独评估复用性、提出目标路径并获得导入批准，随后才能在新的 Researcher
session 中使用。

`/creator` 和 `/researcher` 是 interactive context boundaries。确认跨 role
切换后，DisCo 会持久化旧 session、创建干净的新 session、重建 prompt 和
role-filtered registry；旧轨迹仍可通过 `/resume` 找回。`/export` 只导出当前
session，不会合并另一 role 的消息。非交互和 RPC 客户端使用
`--agent-mode creator|researcher` 选择初始 role；它与
`--mode text|json|rpc` 相互独立。如果请求属于另一 role，DisCo 会在执行前拒
绝该操作并明确建议切换，不会隐式改变 role。

其他 skill packages 使用 DisCo 的 package manager。package 可以在
`disco` manifest key 下声明资源，也可以继续使用 legacy `pi` key，或者使用约
定的 `skills/`、`extensions/`、`prompts/` 和 `themes/` 目录。
`disco install <source>` 会持久化 package，使启用的资源在后续运行中被发现。

`disco install <source> --for creator|researcher|both` 仍只安装一份 package，
但会把 extensions、skills、prompts 和 themes 的运行时 activation 限定到所选
模式；`--for default` 删除这个 installer override。package policy 优先于 skill
frontmatter，并把 package skills 映射成 effective `meta`、`operating` 或
`shared` role。package resolution 本身保持 mode-neutral，供 `disco config`
检查全部资源；resource loader 会在 extension execution、skill collision 和
prompt/theme loading 之前完成模式过滤。

## Skill 生成流程

DisCo 目前内置了针对 package/repo 与 paper 的专门构造流程。
`distill-ml-knowledge` 是 Creator 的 canonical entry point，负责归一化任务、
评估单一流程和组合流程的覆盖情况，并选择 `direct`、`reuse-existing` 或
`design-reusable`。`design-meta-skill` 消费经过验证且会重复出现的 gap handoff
并设计 reusable bundle，不会重新分类请求。所有
bundled workflow skills 的源码都位于 `cli/packages/coding-agent/src/disco/skills/`。

### 软件包/仓库流程

从高层看，DisCo 的 repo-skill pipeline 是：

1. 在 Creator mode 先从 `distill-ml-knowledge` 开始，判断请求应该走
   `direct`、`reuse-existing` 还是 `design-reusable`。
2. 将 source 分类为 package/repository、paper 或 task-specific gap。
3. 分析 source structure 并确认 scope。
4. 准备最小 inspection environment。
5. 从 source、docs、examples、tests、metadata 和 live package inspection 收集证据。
6. 规划顶层 skill 和 sub-skill 结构。
7. 生成并集成自包含 runtime guidance。
8. 运行内置 verification workflow。
9. 把获批的 repo graph 导入
   `~/.disco/agent/skills/repositories/repo-skills/<skill-id>/`。
10. 按固定 area-family taxonomy 完成分类，写入外部 routing decision 和最小 v2
    metadata，并在 import lock 内重建受影响的 area/family router views。

create flow 不把 verification 当作可选收尾步骤。`create-repo-skill` 会在
skill 准备导入或发布前，把集成后的 draft 交给 `verify-repo-skill`。

### 验证门禁

`verify-repo-skill` 负责 created、refreshed 或 extended repo skills 的最终质
量门禁。它把 check-only artifacts 写在 runtime skill directory 之外，通常位
于：

```text
<repository>/skills/tests/<skill-id>/
  test-cases/
  reports/
```

verification stage 覆盖：

- 生成 assertion-backed usability cases；
- 基于选定 source scope 和 generated skill tree 运行 content-level self-refine；
- 在安全且可用时检查代表性的原仓库 native examples/tests；
- 对 links、self-containment、provenance、routing metadata、本地路径泄漏和
  frontmatter shape 运行 static quality gates；
- 写出 final coverage、review、publication 和 handoff reports；
- 检查 import readiness，并在批准或 auto-authorized 时锁定导入 DisCo
  managed repository collection。

runtime skill directories 不应包含 usability cases、eval notes、verification
reports、human-review notes、publication checklists 或 prompt samples。这些
内容属于 review/test artifact directory。

### 论文流程

paper-to-skill flow 用于生成并验证可复用的论文复现技能。它是由任务描述选择的
Creator workflow。当前源码树包含：

```text
cli/packages/coding-agent/src/disco/skills/
  create-paper-skills/
  paper-skills-distiller/
  plan-paper-skill-modules/
  create-paper-module-skill/
  prepare-paper-recovery-env/
  recover-paper-result/
  analyze-paper-recovery/
```

该流程会解析 paper source，可选地把 implementation repository 作为
pre-recovery evidence，随后对论文做 modularization，创建并验证用于论文复现的
module-level skills，准备有边界的 runtime evidence，在不读取原始 implementation
repo 的情况下运行 recovery experiment，分析差距，在配置的 `iteration_budget` 内
必要时 refine，并写出 attempt artifacts 和 final reports。重复运行时默认使
用基于 bundled `distiller-run-config-template.toml` 的 TOML run config。batch
configs 会在 workspace-level `paper2skills_runs/` 区域 normalize 成 JSON，
然后为每个选中的 paper/run 创建独立的 run root、source acquisition record、
generated-skills root 和 attempt directory。

run config normalization 会记录 `paper_slug`、`paper_source`、
`original_repo_source`、`repo_discovery_mode`、`recovery_target`、
`recovery_mode`、`runtime_constraints`、`iteration_budget` 和
`generated_skills_root` 等字段。新运行默认使用 `recovery_mode: hard` 和
`iteration_budget: 10`；`hard` mode 不会把 reduced、proxy、toy、
smaller-model 或 fallback recovery 接受为成功结果，而 `soft` mode 只有在明
确声明 proxy、具备 executable evidence 并通过 mechanism checks 时才可接受。

run root 也会在需要时记录 source acquisition，通常位于
`source/source_resolution.json`。每个 paper attempt 遵循类似下面的 artifact
contract：

```text
run_manifest.json
run_config.normalized.json   # 使用 config 时推荐存在
paper_profile.md
module_plan.json
modules/
generated_skills_validation/
reports/
  generated-skills/
  verification/
  final/
    final_report.md
    final_report.json
environment/
  runtime_handoff.json
  logs/command_log.json
recovery/
  experiment_plan.md
  experiment_validation.json
  source_manifest.json
  recovery_result.json
  logs/
    experiment_command_log.json
    generated_skill_invocations.json
analysis/
  analysis_report.json
  feedback.md
final_validation.json
```

paper recovery 的 source boundary 比 modularization 更严格：optional
implementation repository 可以用于 module planning 和 module-skill creation，
但 recovery 只能使用 paper、module docs、generated skills、runtime handoff、
data 和 general package documentation。recovery result 必须由 executable
command logs 支撑，并且 attempt 需要证明 generated module skills 被调用、
导入或 cross-check，而不是被一次性的 handwritten recovery script 绕过。

当一次运行通过最终验证后，Creator 会以完整 module graph 为单位评估 project
或 managed 部署范围，列出所有 live targets，并只在用户批准后导入。所有
modules 必须留在同一 scope。流程随后写出 `researcher-handoff.md`；生成的
`skills/` 目录仍只是 staging 与审阅输入，不会自动成为 live skills。

### 内置工作流 Skills

package/repo workflow skills 包括：

| Workflow Skill | 作用 |
| --- | --- |
| `prepare-repo-skill-env` | 在 extraction scope 已知后创建或验证 scoped Python inspection environment。 |
| `create-repo-skill` | 分析 source evidence，规划并生成 runtime skill，然后交给 verification。 |
| `verify-repo-skill` | 负责 assertion-backed usability cases、content self-refine、native checks、static gates、reports 和 import readiness。 |
| `refresh-repo-skill` | 根据 upstream source 变化更新已有 repo skill，然后验证。 |
| `extend-repo-skill` | 为已有 skill 增加更深覆盖，然后验证。 |
| `import-repo-skills-to-agent` | 把 DisCo-managed skills 和 scoped router 导出到 Codex、Claude Code 或其他 agent target。 |

`repo-skills-router` 虽然与这些 meta skills 一起打包，但它不是 Creator
workflow，而是 Researcher 可见的 `operating` skill，负责提供渐进路由入口。

paper workflow skills 包括：

| Workflow Skill | 作用 |
| --- | --- |
| `create-paper-skills` | Creator mode 下生成并验证论文复现技能的入口。 |
| `paper-skills-distiller` | 编排 source resolution、modularization、论文复现技能创建、recovery、analysis、refinement 和 final reports。 |
| `plan-paper-skill-modules` | 创建 paper profile、module plan 和 module docs。 |
| `create-paper-module-skill` | 把 module docs 转换成 generated module skills 和 validation checks。 |
| `prepare-paper-recovery-env` | 记录有边界的 package、model、GPU、dataset、command-log 和 runtime handoff evidence。 |
| `recover-paper-result` | 使用 generated skills 运行有边界的 recovery experiment，并保存 executable command 与 generated-skill invocation evidence。 |
| `analyze-paper-recovery` | 对比 recovery evidence、paper target、experiment gate、source boundary 和 mechanism checks，返回 accept/refine feedback。 |

## 运行时 Skill 形态

runtime skill 使用 progressive disclosure：

```text
SKILL.md                         # agent 首先读取的文件
references/                      # 支撑证据和较长说明
sub-skills/<area>/SKILL.md       # 更深入的任务级指导
scripts/                         # 用于 checks/preflight 的小工具
```

`SKILL.md` 应该单独可用，并且只在任务需要更多细节时路由到更深页面。references
和 scripts 如果需要被使用，应在 skill 文本中链接出来。

generated repo skills 预期包含：

- `references/repo-provenance.md`，记录 source commit、package version、
  dirty state 和 evidence paths；
- `references/repo-routing-metadata.json`，用于 managed router placement；
- repo-skill root 和 sub-skill frontmatter 中的
  `disable-model-invocation: true`，让兼容的 agent 把批量 repo skills 放在 routing
  entry point 后面；
- canonical/export router 保持 enabled，而 DisCo live router 遵循用户设置的
  `repo-skills router enable|disable` policy；
- 当未来使用依赖相关细节时，使用 bundled references 或 scripts，而不是链接
  到原始 checkout。

## 路由器

repo-skills router 是 skill library 的生成/维护索引：

```text
skills/
  repositories/
    repo-skills/
      <repo-skill-id>/
    repo-skills-router/
      SKILL.md
      references/
        areas/
        families/
        index/
        maintenance.md
```

它不是单个 skill 的替代品。它提供第一轮选择地图，再从精确的 family 页面把
agent 指向候选 repository skill root。

## 部署范围与托管库

新设计的 meta skill 与它以后生成的 operating graph 是两个独立的部署决策。
meta skill 经过验证并获得明确批准后，固定安装到以下 Creator managed 路径：

```text
~/.disco/agent/skills/<meta-skill-id>/
```

普通 operating graph 必须且只能选择下面一个 live scope：

| Scope | 路径 | 选择规则 |
| --- | --- | --- |
| Project | `<project-dir>/.agents/skills/<skill-id>/` | 用于依赖单个任务、当前 checkout、私有数据集、评测器、某次 benchmark、本地约定或运行环境的产物。无法确认复用价值时也默认选择这里。只有项目被信任后，Researcher 才会加载。 |
| Managed | `~/.disco/agent/skills/<skill-id>/` | 只用于自包含、有 provenance 支撑、不依赖临时任务状态、经过代表性使用验证，并且预期能跨项目或研究任务复用的产物。 |

同一个 graph 的所有 roots 和 sub-skills 必须位于同一 scope。导入前，Creator
需要展示复用性证据、所有目标路径、graph 入口、验证结果、未解决问题、路径冲
突、覆盖状态及 shadowing 影响。通用 graph importer 会在同一个加锁事务中导
入全部 roots，并在失败时回滚整个 graph；覆盖已有 skill 始终需要单独批准。

Repository graph 是高复用 managed scope 的特殊情况。它不使用通用 importer，
而是保持下面的 canonical layout：

```text
~/.disco/agent/skills/
  <meta-skill>/               # 仅 Creator 可见
  <reusable-operating-skill>/ # 仅 Researcher 可见
  repositories/
    repo-skills/
      <repo-skill-id>/
    repo-skills-router/
```

repository import transaction 会复制 runtime graph，验证
`references/repo-routing-metadata.json`，并在持有共享 import lock 时重建同级
router。router update 必须由 structured metadata 生成，不能在导入时手工编辑
Markdown。DisCo 会自动发现 managed root，让隐藏 repo skills 不进入初始上下
文；router enabled 时自动做渐进选择，disabled 时也可以显式调用。只有导出到其他
runtime 时，才使用
`import-repo-skills-to-agent` 把 managed skills 和 scoped router 写入
`~/.agents/skills/`、`~/.claude/skills/` 或用户显式指定的 legacy
`~/.codex/skills/`。

导出到 Codex 时，import workflow 还会在目标侧为非 router repo skills 写入
`agents/openai.yaml`，设置 `policy.allow_implicit_invocation: false`，因为
Codex 不使用 `disable-model-invocation` frontmatter 字段表达这个 policy。

## 唯一事实来源

source-of-truth 规则：

- 更广义的 library 位于 `skills/`；repository skills 位于
  `skills/repositories/repo-skills/`，router 位于同级的
  `skills/repositories/repo-skills-router/`。
- Bundled 与 portable external-agent workflow skills 只有一个 source of
  truth：`cli/packages/coding-agent/src/disco/skills/`。
- 在该 source directory 中编辑 workflow skills，然后 rebuild DisCo；不要维护
  第二份需要手工同步的 mirror。
- Verification 和 review artifacts 位于 runtime skill directories 之外，通常
  在被检查仓库的 `skills/tests/<skill-id>/` 下。
- 与项目绑定或复用价值不确定的 operating graphs 部署到受信任项目的
  `.agents/skills/`；只有证据充分的跨项目可复用 graph 才进入
  `~/.disco/agent/skills/` 顶层。Repository graphs 继续使用专用的嵌套
  collection 与同级 router。
- 不要把生成的 `dist/` resources 当作 source of truth 手工编辑。
- 文档需要明确某个功能属于 runtime skill library、bundled workflow source，
  还是 DisCo CLI runtime。
