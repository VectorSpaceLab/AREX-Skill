# DisCo 工作流指南

本文档集中说明主 README 为保持简洁而省略的操作细节，包括模式边界、
Researcher 任务执行、Creator 技能构造流程、部署范围和跨 Agent 导出。使用公开
仓库技能集合前，请先按[主 README](../README.zh-CN.md#installation)安装 DisCo
和 repository collection。

## Agent 模式与会话

每个 DisCo 会话只属于一种 Agent 模式：

| 模式 | 可见技能 | 职责 |
| --- | --- | --- |
| **Researcher**（默认） | `operating` 与 `shared` 技能，包括没有声明 `metadata.disco-role` 的用户技能 | 使用经过路由的操作知识、代码、工具和实验完成机器学习研究任务。 |
| **Creator** | 声明为 `metadata.disco-role: meta` 或 `shared` 的技能 | 先从 `distill-ml-knowledge` 开始，选择 `direct`、`reuse-existing`（单一流程或组合）或 `design-reusable`，只有经过验证且会重复出现的构造能力缺口才交给 `design-meta-skill`。 |

非交互会话通过 `--agent-mode creator|researcher` 指定模式。在交互界面中，
`/creator` 与 `/researcher` 会先提示用户，再用干净上下文创建一个新会话。原
会话仍可通过 `/resume` 恢复并单独导出；新会话执行 `/export` 时，只会导出新
会话中的轨迹。

`--mode text|json|rpc` 选择的是输出协议，与 Agent 模式无关。如果用户用自然
语言提出了属于另一模式的请求，DisCo 会在执行前停止并建议切换模式，不会
隐式切换。

`shared` 只用于确实适合两种模式的 utilities。它不会授权 Creator 执行最终研究
任务，也不会授权 Researcher 执行 Creator 的构造工作。package 安装者可以用
`disco install <source> --for creator|researcher|both|default` 覆盖同一 package
全部资源的可见性；详见 [package 指南](../cli/docs/packages.md#mode-targeting)。

## Researcher 工作流

### 使用公开仓库技能集合

首次安装公开集合后，可以用同一组命令检查和更新：

```bash
disco repo-skills install
disco repo-skills status
disco repo-skills update
```

`status` 会离线检查已记录的 commit、托管内容、router 状态和 router coverage，
不会查询远端 HEAD；只有显式运行 `update` 才会检查远端更新。

updater 只修改官方托管的 skill ID，并保留 Creator 创建或手动导入的其他 repo
skills。官方 skill 的本地修改会被报告为 drift；必须显式使用 `--force` 才会在
保留备份后覆盖。

安装后直接描述具体的研究目标即可。例如，可以在受控条件下比较两套推理系统：

```bash
disco --agent-mode researcher -p "在这台机器上使用相同模型和工作负载评测 vLLM 与 SGLang。在相同硬件和显存约束下分别调优两套服务，报告各自经过验证的最佳吞吐量，并保留复现实验所需的命令和测量结果。"
```

对于与仓库知识相关的请求，DisCo 会读取 `repo-skills-router`，先打开一个或
两个可能相关的 area 页面，再比较匹配的 family 页面，最后读取
`vllm/SKILL.md`、`sglang/SKILL.md` 等被选中的技能。随后它会用常规的文件、
命令和实验工具执行并验证任务，而不会把所有仓库技能的描述和正文一次性放入
初始上下文。

router 默认参与自动 skill 选择。如果希望保留 collection，但不让 router 出现
在 model-visible skill discovery 中，可以运行：

```bash
disco repo-skills router disable
```

disabled router 仍然会注册，可以显式执行 `/skill:repo-skills-router`。使用
`disco repo-skills router enable` 可以恢复自动选择；两种修改都在新的
Researcher session 中生效。

已知具体技能名称时，也可以显式调用：

```bash
disco --agent-mode researcher -p "/skill:vllm 为 <模型与工作负载> 找出并验证吞吐量最高的 vLLM 配置"
```

### 使用经过审批的任务专用技能图

Creator 构造并导入任务专用的操作技能图后，调用交接记录中给出的入口技能：

```bash
disco --agent-mode researcher -p "/skill:<graph-entry> 在 <环境与预算限制> 内完成 <研究任务>，并使用 <评测器> 验证结果。"
```

Researcher 会渐进打开所需子图，并在执行过程中使用其中的方法、检查和故障
恢复措施。如果可见技能图无法提供必要知识，它会记录具体的能力缺口并建议
开启新的 Creator 会话，而不会在当前模式中直接编写技能。

交接记录还会说明完整技能图的部署位置：

- 只适用于某个任务、项目、私有数据集、评测器、基准实例或本地环境的产物，
  以及复用价值尚不明确的产物，应部署到 `<project-dir>/.agents/skills/`；
  DisCo 只会在该项目受信任后加载这些技能。
- 自包含、有来源证据支撑，并经过代表性跨项目验证的技能图，可以提议部署到
  `~/.disco/agent/skills/`。
- 同一个技能图不能拆分到两个部署范围中。

## Creator 工作流

需要构造、审阅、维护或导出技能时，启动 Creator：

```bash
disco --agent-mode creator
```

Creator 可以看到 meta 与 shared 技能。它会先判断现有构造流程能否覆盖当前任务的构造规格，
只要条件允许就优先复用或组合已有流程。

### 评估构造流程是否足够

先从 `distill-ml-knowledge` 开始处理普通的 ML knowledge distillation 请求。它
拥有通用 task/construction contract，检查一个可见流程或有边界的流程组合是否
充分，并选择 `direct`、`reuse-existing` 或 `design-reusable`。以仓库为知识源时，
通常通过 `reuse-existing` 使用 `create-repo-skill`；以论文为知识源时，通常复用
内置论文工作流。只有在知识源处理、证据选择、技能图结构、验证、环境或恢复上
存在有证据支撑且会重复出现的构造能力缺口时，才会把任务交给
`design-meta-skill`：

```bash
disco --agent-mode creator -p "/skill:distill-ml-knowledge 归一化 <任务与知识源锚点>；选择 direct、reuse-existing 或 design-reusable。"
```

新的元技能必须通过验证并得到用户明确批准，随后才会作为可复用的 Creator
基础能力导入 `~/.disco/agent/skills/<meta-skill-id>/`。之后使用具体的知识源
锚点调用它，构造任务所需的操作技能。这些操作技能还要按前述部署规则单独
评估复用性并取得导入批准。最后，Creator 会为新的 Researcher 会话写出交接
记录。

### 从仓库构造技能

根据源码证据创建并验证仓库专用技能：

```bash
disco --agent-mode creator -p "为 /path/to/repo 创建仓库技能。"
```

该流程会分析仓库结构，必要时准备或检查 Python 调研环境，编写运行时指导，
记录来源，再把草稿交给 `verify-repo-skill`。验证阶段会创建带断言的可用性用
例、运行内容级自我修订、在安全可行时检查上游原生示例或测试、执行静态质量
门禁，并写出覆盖率和审阅产物。完成这些步骤后，技能才会被视为可用。

若希望 Agent 自动决定抽取范围，并在验证通过后自动导入托管技能库，需要在
请求中明确授予这两项权限：

```bash
disco --agent-mode creator -p "为 /path/to/repo 创建仓库技能，自动决定抽取范围，并在验证通过后自动导入。"
```

### 构造论文复现技能

为了可重复地生成并验证用于论文复现的技能，先复制并填写内置运行配置，
再交给 DisCo：

```bash
cp cli/packages/coding-agent/src/disco/skills/create-paper-skills/assets/distiller-run-config-template.toml \
  /path/to/distiller_run_config.toml
disco --agent-mode creator -p "使用 Distiller 为该配置中的每项运行生成并验证用于论文复现的技能。config_path: /path/to/distiller_run_config.toml"
```

论文来源可以是本地 PDF 或文本文件、PDF 直链、arXiv 链接或编号，也可以是
论文标题。实现仓库是可选项，可以填写本地路径、Git URL、`none` 或
`unknown`。

Distiller 会把论文拆分为模块，创建并验证用于论文复现的模块级技能，准备有
明确边界的运行证据，在不读取原始实现仓库的前提下执行当前条件允许的最强
恢复实验，分析差距，并在必要时于 `iteration_budget` 内迭代。每次尝试的产物和
最终报告会写入 `<attempt_dir>/reports/final/`。默认的 `recovery_mode` 是
`hard`：缩减、代理、
玩具或回退实验只能作为诊断记录，除非显式选择 `soft` 模式，否则不能算作
成功恢复。

最终验证通过后，Creator 会为完整的论文复现技能图提出唯一部署范围，只在用户
批准后执行导入，并写出 Researcher 交接记录。生成的 `skills/` 目录在获批并
导入前始终只是暂存内容。

### 维护已有技能

如果已有技能内容正确，但需要覆盖新的工作流领域，可以扩展它：

```bash
disco --agent-mode creator -p "以 /path/to/repo 为证据，为 /path/to/repo/skills/example-skill 中的现有技能增加流式推理支持。"
```

当上游 API、配置、示例、依赖或运行时行为发生变化时，可以刷新技能：

```bash
disco --agent-mode creator -p "根据 /path/to/repo 的当前代码刷新 /path/to/repo/skills/example-skill 中的技能。"
```

刷新流程会保留仍然正确的现有指导，并根据当前源码基线更新过期内容。

### 把仓库技能导出到其他 Agent

当 Codex、Claude Code 或其他兼容 Agent 需要 DisCo 托管仓库集合中的部分技
能时，使用 `import-repo-skills-to-agent`。该流程会在目标技能目录中保持
`repo-skills/` 与 `repo-skills-router/` 同级。

把路由器以及 `vllm`、`sglang` 导入 Claude Code：

```bash
disco --agent-mode creator -p "/skill:import-repo-skills-to-agent import vllm and sglang to ~/.claude"
```

把相同技能导入 Codex 推荐的用户级技能目录：

```bash
disco --agent-mode creator -p "/skill:import-repo-skills-to-agent import vllm and sglang to ~/.agents"
```

导入后请重启目标 Agent。[Research Skills Library
说明](../skills/README.md)介绍了源码布局和 DisCo 安装
方式；[`import-repo-skills-to-agent`
工作流](../cli/packages/coding-agent/src/disco/skills/import-repo-skills-to-agent/SKILL.md)
则定义了目标目录布局、覆盖策略和路由器调用约定。

## 参考文档

- [架构说明](architecture.zh.md)
- [内置技能参考](../cli/packages/coding-agent/src/disco/skills/README.md)
- [Research Skills Library](../skills/README.md)
- [给其他 Agent 的 Meta Skills](meta-skills-for-other-agents.zh.md)
