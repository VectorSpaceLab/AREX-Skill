<p align="center">
  <img src="assets/hero.png" alt="AREX-Skill 将仓库和论文知识转化为可供 coding agent 使用的可执行技能，支持自主 ML 研究">
</p>



<h1 align="center">AREX-Skill</h1>

<p align="center">
  <strong>将 ML 知识转化为面向自主研究的可执行技能</strong>
</p>

<p align="center">
  <a href="skills/README.md"><img src="https://img.shields.io/badge/AREX--Skill_Library-5000%2B_skills-0E9B9B?style=for-the-badge" alt="AREX-Skill Library：5000+ skills"></a>
  <a href="docs/repository-catalog.md"><img src="https://img.shields.io/badge/ML_Repositories-1000-5865F2?style=for-the-badge" alt="1,000 个 ML 仓库"></a>
  <a href="https://www.npmjs.com/package/@arex-skill/disco"><img src="https://img.shields.io/badge/CLI-disco%20v0.2.0-D22128?style=for-the-badge&logo=npm&logoColor=white" alt="DisCo CLI v0.2.0"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-lightgrey?style=for-the-badge&logo=apache&logoColor=white" alt="License: Apache 2.0"></a>
  <a href="#documentation"><img src="https://img.shields.io/badge/Documentation-README-0E9B9B?style=for-the-badge" alt="文档"></a>
  <a href="#contributing"><img src="https://img.shields.io/badge/Contributing-guide-5865F2?style=for-the-badge" alt="参与贡献指南"></a>
</p>

<p align="center">
  <a href="README.md">English</a> · <b>简体中文</b>
</p>

<p align="center">
  <strong>一个开放技能库：从 1,000 个 ML 仓库中蒸馏出 5,000+ 个经过验证、可直接执行的技能</strong><br>
  <strong>无缝接入 Codex、Claude Code、Pi 等 coding agents</strong><br>
  <strong>推进覆盖 ML engineering、paper replication 等场景的 frontier autonomous research</strong>
</p>

## 🎬 Demo <a id="demo"></a>

通过一分钟了解 AREX-Skill：DisCo 将一个仓库蒸馏为经过验证、可执行的 skills；
router 从 5,000+ 个 skills 中将范围缩小到任务所需的一个分支；配备相关 skill 的
Agent 则可以完成没有 skill 时会陷入停滞的任务。

https://github.com/user-attachments/assets/9fa59284-4625-44ef-8b43-01c7b6a05cea

## 🧭 目录 <a id="table-of-contents"></a>

- [动态](#news)
- [为什么需要 AREX-Skill](#why-arex-skill)
- [技能库概览](#library-at-a-glance)
- [自主研究 Benchmark 结果](#auto-research-benchmark-results)
- [AREX-Skill 如何构建](#how-arex-skill-is-built)
- [快速开始](#quick-start)
- [使用示例](#usage-examples)
- [文档](#documentation)
- [参与贡献](#contributing)
- [致谢](#acknowledgement)
- [许可证](#license)
- [引用](#citation)

## 📣 动态 <a id="news"></a>

- **2026-08-27**：技能库达到 **1,000 个仓库和 5,000+ 个技能**，并完成了覆盖已发布仓库技能集合的路由器重建。
- **2026-08-03**：AREX-Skill 发布，包含 DisCo 的 Creator 和 Researcher 工作流，以及首个覆盖 170 多个常用仓库的技能库版本。

## 💡 为什么需要 AREX-Skill <a id="why-arex-skill"></a>

研究知识非常丰富，但大部分内容仍然是写给人类阅读的。论文解释方法及其有效原因；仓库包含可以运行的实现；博客和 examples 记录实践技巧与失败模式。Agent 仍然需要自己搜索这些来源、判断哪些内容适用、拼装工作流、补齐缺失步骤、调试，并判断结果是否可信。

AREX-Skill 将这层缺失的**操作知识（operating knowledge）**转化为 Agent 可以使用的接口。AREX Skill 不只是仓库摘要，而是明确记录某项能力何时适用、应该运行什么、如何验证，以及实验失败后如何恢复。

一个 AREX Skill 是一个自包含、面向 Agent 的操作知识单元。它使用开放的
[Agent Skills 格式](https://github.com/agentskills/agentskills)作为可移植的
封装约定，并在此基础上补充 Agent 执行任务所需的操作上下文：能力何时适用、应该运行什么、如何验证，以及实验失败后如何恢复。每个 skill 都以
`SKILL.md` 为核心，并可按需附带 `references/` 和 `scripts/` 资源：

```text
skill/
├── SKILL.md       # 范围、路由、工作流和验证
├── references/    # 聚焦说明与来源 provenance
└── scripts/       # 可执行辅助工具、诊断和检查
```

当一个仓库包含多种能力时，这些 skills 会进一步组合成 repository skill graph。Router 先将请求缩小到 area、family、repository 和 workflow，Agent 再只加载当前任务需要的分支。这种 progressive disclosure 设计可以保持初始上下文聚焦，同时保留对更深层 instructions 和 helpers 的访问。运行时模型和路由细节见[技能库指南](skills/README.md)与[架构指南](docs/architecture.zh.md)。

### Skill 如何参与自主研究任务

一个 research agent 通常遵循以下模式：

1. **从具体研究目标开始。**
2. **将请求路由到相关的 skill graph。**
3. **只加载所需的 `SKILL.md` 分支**，并根据需要继续加载关联的 skills。
4. **运行推荐的 procedures 和 scripts**，在执行过程中使用 skill 提供的 checks 和 recovery guidance。
5. **根据相关检查项和目标指标验证结果。** 如果执行失败，则遵循恢复指导进行迭代并重新验证。

最终产物不只是一个答案，而是一个可以检查和复现的实验或实现。

## 📊 技能库概览 <a id="library-at-a-glance"></a>

<p align="center">
  <img src="assets/library.png" alt="AREX-Skill 技能库覆盖 20 个研究领域和 178 个 package families">
</p>

<p align="center">
  <strong>20 个研究领域 · 178 个 package families · 1,000 个仓库 · 5,000+ 个已验证技能</strong>
</p>

AREX-Skill Library 覆盖 ML engineering、LLM、计算机视觉、数据科学、科学计算、模型部署、训练基础设施、机器人、生成媒体、生物医学 AI 等方向。可以通过[仓库目录](docs/repository-catalog.md)浏览完整的 area 和 package-family inventory，也可以通过[已导入技能目录](docs/imported-repo-skills.md)查看上游仓库和 source baseline。

Library 的 repository-skill router 会在 Agent 加载具体 graph 分支前先缩小请求范围。Repo skills 会随着上游变化进行维护；source commit、验证步骤和 refresh 要求见[刷新 Repo Skills](docs/refreshing-repo-skills.zh.md)。

## 📈 自主研究 Benchmark 结果 <a id="auto-research-benchmark-results"></a>

我们固定 Agent setup、harness 和 execution budget，只改变 Agent 是否拥有 AREX 蒸馏的 skills。

<p align="center">
  <img
    src="assets/results.png"
    width="82%"
    alt="Codex 与 Codex + AREX-Skill 在 MLE-bench、PaperBench、FrontierCS 和 PassNet 上的 Benchmark 结果对比"
  >
</p>

<p align="center">
  <em>Codex + AREX-Skill 在涵盖四类自主研究场景的 Benchmark 中取得了更好的结果。</em>
</p>

| Benchmark | 场景 | 指标 | Codex | Codex + AREX-Skill | 提升 |
| --- | --- | --- | ---: | ---: | ---: |
| **MLE-bench** | ML engineering（75 个 Kaggle competitions） | Any Medal rate (%) | 31.11 | **72.89** | **+134.3%** |
| **PaperBench** | Paper replication（20 篇论文） | Replication score | 29.45 | **39.59** | **+34.4%** |
| **FrontierCS** | Algorithm optimization（188 个 Agent Track tasks） | Score | 70.63 | **77.14** | **+9.2%** |
| **PassNet** | Compiler pass optimization（200 个样本） | AS Score | 1.343 | **1.531** | **+14.0%** |

三个结论：

- **操作知识确实重要。** AREX-Skill 增加了可复用的 procedures、checks 和 recovery paths，但没有改变底层 Agent workflow。
- **任务越难，优势越明显。** Skills 帮助 Agent 避免昂贵的无引导试错，并从接近失败的状态中恢复。
- **预算被花在更有效的地方。** 相关 skill graph 能帮助 Agent 更早进入有效解空间，把更多预算用于实验和验证。

完整技术报告即将发布。在报告公开前，上表是当前评测结果的简洁汇总。

## ⚗️ AREX-Skill 如何构建 <a id="how-arex-skill-is-built"></a>

AREX-Skill Library 由 DisCo Creator 通过四阶段的 skill distillation workflow 构建：从 anchor 界定 capabilities，基于 admissible evidence 进行 grounding，构建 candidate skill graph，并在发布前完成 verify 和 refine。Anchor 可以是 task-agnostic distillation 的 source，也可以是 task-oriented distillation 的 problem；支持性证据、validation checks 和 unresolved gaps 会保留在 construction record 中。

<p align="center">
  <img
    src="assets/method.png"
    width="100%"
    alt="四阶段的 skill distillation 流程：界定能力、构建证据、构建 skill graph，以及验证和完善"
  >
</p>

构建生命周期见 [DisCo Workflows](docs/disco-workflows.zh.md)；Creator workflow 和 portable installation 见 [DisCo Meta Skills](docs/disco-meta-skills.zh.md)。

## 🚀 快速开始 <a id="quick-start"></a>

### 1. 安装 DisCo

DisCo 要求 Node.js >=22.19.0：

```bash
npm install -g @arex-skill/disco
```

首次运行时通过 /login 配置模型提供商，也可以使用 OPENAI_API_KEY、ANTHROPIC_API_KEY 或 GEMINI_API_KEY 等环境变量。提供商配置和源码构建方式见[安装指南](docs/installation.zh.md)。

### 2. 安装技能库并启动 Researcher 模式

```bash
disco repo-skills install
disco
```

DisCo 的默认 **Researcher mode** 原生支持加载和路由 AREX-Skill Library。在提示框中尝试一个具体任务：

```text
使用已安装的 skills，在这台机器上以相同模型、工作负载和硬件约束比较 vLLM 与 SGLang。报告经过验证的吞吐量，并保留复现实验所需的命令和测量结果。
```

Router 会选择相关 repository skills，Agent 只会渐进式加载当前任务需要的 instructions。

### 3. 将选定的 skills 导入其他 coding agent

DisCo 可以把选定的 repository skills 和 scoped router 导出到兼容的 coding agents。导入 Codex 推荐的用户级 skills 目录：

```bash
disco --creator -p "/skill:import-repo-skills-to-agent import vllm and sglang to ~/.agents"
```

导入 Claude Code 时使用它的用户级 skills 目录：

```bash
disco --creator -p "/skill:import-repo-skills-to-agent import vllm and sglang to ~/.claude"
```

导入后重启目标 Agent，使其重新加载 skills。目标目录、覆盖处理、portable Creator workflows 和其他 Agent 的使用方式见 [DisCo Meta Skills](docs/disco-meta-skills.zh.md) 与 [DisCo Workflows](docs/disco-workflows.zh.md)。

### 创建或刷新 skills

DisCo Creator 也可以构建 repository / paper skills、验证它们，并依据新的上游证据刷新已有 repository skills。为了保持 Quick Start 简洁，相关内容放在文档中：

- [DisCo Meta Skills](docs/disco-meta-skills.zh.md) — 选择并使用 Creator meta skills；
- [DisCo Workflows](docs/disco-workflows.zh.md) — 构建、验证和导出；
- [Refreshing Repo Skills](docs/refreshing-repo-skills.zh.md) — 维护和 refresh checklist。

## 🖼️ 使用示例 <a id="usage-examples"></a>

AREX-Skill Library 可以支持许多 ML workflow。下面是两个具有代表性的 repository-skill 场景。

### 高吞吐推理

[vLLM](skills/repositories/repo-skills/vllm/) 和 [SGLang](skills/repositories/repo-skills/sglang/) skills 可以指导一个受控的 serving 对比：

```text
在相同模型和工作负载下比较 vLLM 与 SGLang。在相同硬件和显存约束下
分别调优，报告经过验证的吞吐量，并保留复现实验所需的命令和测量结果。
```

### 蛋白质结构建模

[AlphaFold2](skills/repositories/repo-skills/alphafold2/) skills 可以为蛋白质结构建模工作流提供操作指导：

```text
使用已安装的 AlphaFold2 skills 设置并验证这个蛋白质结构建模工作流。
先从一个很小的 synthetic input 开始，检查 sequence/MSA 的形状和依赖，
运行相关的模型路径，并报告复现结果所需的命令和检查项。不要把未经训练
的输出当作科学预测。
```

完整的端到端 session 导出见 [examples 目录](examples/README.md)。

更多 repository capabilities：

[FAISS](skills/repositories/repo-skills/faiss/) ·
[Unsloth](skills/repositories/repo-skills/unsloth/) ·
[Diffusers](skills/repositories/repo-skills/diffusers/) ·
[LeRobot](skills/repositories/repo-skills/lerobot/) ·
[AlphaFold2](skills/repositories/repo-skills/alphafold2/) ·
[完整仓库目录](docs/repository-catalog.md)。

## 📚 文档 <a id="documentation"></a>

| 文档 | 适合用于… |
| --- | --- |
| [安装指南](docs/installation.zh.md) | 安装 DisCo、配置提供商、安装或更新技能库，或从源码构建。 |
| [DisCo 工作流指南](docs/disco-workflows.zh.md) | 运行 Researcher / Creator workflows、验证 graph 和导出 skills。 |
| [DisCo Meta Skills](docs/disco-meta-skills.zh.md) | 创建 repository / paper skills，以及安装 portable Creator workflows。 |
| [刷新 Repository Skills](docs/refreshing-repo-skills.zh.md) | 根据上游变化刷新 skill，并更新 provenance、routing 和 catalog 数据。 |
| [AREX-Skill Library（英文）](skills/README.md) | 理解 runtime collection、router、repository graphs 和 managed installation。 |
| [仓库目录（英文）](docs/repository-catalog.md) | 按 area 和 package family 浏览完整技能集合。 |
| [文档索引（英文）](docs/README.md) | 查看全部文档，并选择下一步阅读内容。 |

## 🤝 参与贡献 <a id="contributing"></a>

欢迎三类贡献：

1. **新增 repository skills。** 在 skills/repositories/repo-skills/<skill-id>/ 下提交经过验证的 graph；当路由或覆盖范围变化时，同步更新 router 和公开 catalog。
2. **刷新或扩展已有 skills。** 使用最新的上游证据，保留 provenance 和 license metadata，并提供支持本次变更的验证步骤。
3. **改进 DisCo 及其 workflows。** 在 cli/ 及相关项目文档中贡献 CLI、runtime、bundled skill 和文档修改。

Skill pull request 应说明上游 source commit、使用的 model 和 provider、相关 reasoning level、生产 workflow、验证命令、已知缺口，以及 router 或 catalog 是否需要更新。完整要求见[贡献指南](CONTRIBUTING_CN.md)，英文版本见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 🙏 致谢 <a id="acknowledgement"></a>

DisCo 的 CLI 和 Agent runtime 构建在
[earendil-works/pi](https://github.com/earendil-works/pi) 的基础之上。Pi 是一个开源
AI Agent 工具包，提供统一的 LLM API、Agent loop、终端 UI 和 coding-agent CLI。

AREX-Skill 同样离不开 GitHub 开源社区的支持。技能库中的 repository skills
得以建立，是因为众多研究者和工程师向社区开源了高质量的 ML、Agent、数据、
生物/化学、视觉和基础设施项目。

## 📄 许可证 <a id="license"></a>

除非文件或组件另有说明，仓库级 AREX-Skill 材料采用 Apache License 2.0。

> ⚠️ **AREX-Skill Library 中的每个 skill 都有自己的许可证。** 使用、复制、修改或再分发某个 skill 前，必须检查该 skill 的 SKILL.md 中的 license metadata。对于该 skill 而言，其独立许可证才是权威依据，不会被本仓库的 Apache-2.0 许可证替代。

[cli/](cli/) 下独立发布的 DisCo npm package 使用自身的 [MIT License](cli/LICENSE)，上游署名见 [cli/THIRD_PARTY_NOTICES.md](cli/THIRD_PARTY_NOTICES.md)。

## 📝 引用 <a id="citation"></a>

TBA
