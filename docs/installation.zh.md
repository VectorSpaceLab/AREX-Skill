# 安装指南

要在 DisCo 中使用本仓库发布的 AREX-Skill Library，需要依次完成以下两步：

1. 安装 `disco` CLI。
2. 把 AREX-Skill Library 的公开 repository-skill collection 安装到 DisCo
   managed skill 目录。

把 portable Creator meta skills 安装到其他 Agent 是可选操作；DisCo 已经内置
这些 workflows。

## 安装 DisCo

可以选择以下任一种安装方式。curl 和 PowerShell installer 会在用户目录中
创建 managed installation，使用独立的 release 目录和稳定的 `disco` launcher。
如果当前没有 Node.js，或者 Node.js 版本低于 `22.19.0`，installer 会准备一个
经过校验的用户级 Node.js runtime。

### 推荐的 managed installer

在 macOS、Linux、WSL 或 Git Bash 中运行：

```bash
curl -fsSL https://github.com/VectorSpaceLab/AREX-Skill/releases/latest/download/install-disco.sh | sh
```

在 Windows PowerShell 中运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { irm https://github.com/VectorSpaceLab/AREX-Skill/releases/latest/download/install-disco.ps1 | iex }"
```

PowerShell installer 会检查 Git Bash、Cygwin、MSYS2 和 WSL。如果没有可用的
`bash.exe`，会尝试在用户环境中准备 Git for Windows。已有有效的 `shellPath`
设置会被保留。

managed installer 会把 release 状态保存到 Unix 下的
`~/.disco/agent/install/`，Windows 下保存到对应的用户 profile 目录。它不会
覆盖无关的 `disco` 命令，也不会删除用户的 settings、credentials、sessions、
skills 或 package 状态。

如果 installer 提示需要刷新 `PATH`，请启动一个新的 shell，然后验证：

```bash
disco --version
```

managed installation 可以直接运行 `disco update` 更新。只删除 installer 自己
创建的内容时，运行：

```bash
~/.disco/agent/install/install-disco.sh --uninstall
```

Windows 中运行：
`& "$env:USERPROFILE\.disco\agent\install\install-disco.ps1" -Uninstall`。

### 通过 package manager 安装

以下命令安装的是同一个 package 和同一个 `disco` executable：

```bash
# npm
npm install -g --ignore-scripts @arex-skill/disco

# pnpm
pnpm add -g --ignore-scripts @arex-skill/disco

# Bun
bun add -g --ignore-scripts @arex-skill/disco
```

Yarn global installation 仍然兼容，但不作为主要的公开入口：

```bash
yarn global add --ignore-scripts @arex-skill/disco
```

使用 package manager 安装时，应使用同一个 manager 更新或卸载：

```bash
npm update -g @arex-skill/disco
npm uninstall -g @arex-skill/disco

pnpm update -g @arex-skill/disco
pnpm remove -g @arex-skill/disco

bun update -g @arex-skill/disco
bun uninstall -g @arex-skill/disco
```

如果 runtime 能识别 package 的 global root 且路径可写，`disco update` 也可以
更新 package-manager installation。如果提示路径不可写或无法识别，请使用上面
对应的 manager 命令。package-manager installation 要求 Node.js `>=22.19.0`，
并且 Windows 上必须有可用的 bash shell。

### 手动 npm 安装

如果无法使用 managed installer，也可以直接从 npm 安装 DisCo CLI：

```bash
npm install -g --ignore-scripts @arex-skill/disco
disco
```

DisCo 要求 Node.js `>=22.19.0`，并基于
[Pi](https://github.com/earendil-works/pi) 的多模型提供商层构建。npm package
包含经过 DisCo 修改的 coding-agent 源码，并固定依赖
`@earendil-works/pi-agent-core`、`@earendil-works/pi-ai` 和
`@earendil-works/pi-tui`。它不依赖 `@earendil-works/pi-coding-agent`，不会
发现 `.pi` resources，也不会共享全局安装的 Pi dependency tree。

首次启动时通过 `/login` 配置至少一个模型提供商，也可以使用
`OPENAI_API_KEY`、`ANTHROPIC_API_KEY`、`GEMINI_API_KEY`、
`OPENROUTER_API_KEY` 或 `MISTRAL_API_KEY` 等环境变量。

### 从源码构建以进行本地开发

```bash
git clone https://github.com/VectorSpaceLab/AREX-Skill.git
cd AREX-Skill
# 如果通过 HTTP(S) 代理获取 model catalog 失败，可使用：NODE_USE_ENV_PROXY=1 bash scripts/build-from-source-link.sh
bash scripts/build-from-source-link.sh
```

该脚本会根据仓库内的 shrinkwrap 安装独立 package dependencies，构建 DisCo，
并把 `disco` 命令全局链接到本地开发版本。

## 安装已发布的 Repository Skill Collection

使用 DisCo 安装官方 collection 及其 router：

```bash
disco repo-skills install
```

该命令会 shallow checkout 官方仓库，只安装已发布的 runtime collection，并记
录 source commit。本机必须可以使用 Git。安装后，可以通过以下命令检查或更新
managed collection：

```bash
disco repo-skills status
disco repo-skills update
```

`status` 只检查本地状态，不会访问 GitHub；它会检查 managed digests、router
是否存在，以及当前 skill coverage。需要检查并应用最新官方 commit 时，运行
`update`。

更新只会替换官方 managed skill IDs；Creator 在本地创建或导入的 repo skills
会被保留。如果某个官方 skill 已被本地修改，或者与 unmanaged skill 冲突，更新
会停止。显式使用 `--force` 更新时，会先保留一份可恢复的备份。

## Router 行为与开关

DisCo 会注册 managed collection，但其中的 repository roots 和 focused
sub-skills 使用 `disable-model-invocation: true`，不会进入初始模型上下文。默认
情况下，`repo-skills-router` 保持可见，先把请求路由到一个实际场景，再指向同级
`repo-skills/` collection 中选定的 skill。

无需卸载 collection，即可关闭或恢复 router 的自动选择：

```bash
disco repo-skills router disable
disco repo-skills router enable
```

关闭后，router 不再参与模型的自动选择，但仍会注册，可以通过
`/skill:repo-skills-router` 显式调用。

**安装、更新或修改 router 设置后，请启动一个新的 Researcher 会话。**

## 手动安装兜底方案

```bash
git clone https://github.com/VectorSpaceLab/AREX-Skill.git
cd AREX-Skill
mkdir -p ~/.disco/agent/skills/repositories
cp -R \
  skills/repositories/repo-skills \
  skills/repositories/repo-skills-router \
  ~/.disco/agent/skills/repositories/
```

之后运行 `disco repo-skills install` 时，可以接管一份未修改的手动安装副本，并
保留额外的本地 skill IDs。

## 安装到其他 Agent 的 Portable Meta Skills（可选）

DisCo 已经内置 Creator workflows。如果需要在其他兼容 Agent 中运行这些
workflows，例如 Claude Code、Codex 或项目级 Agent，请参阅
[DisCo Meta Skills](disco-meta-skills.zh.md) 的完整清单和可移植安装说明。

## 延伸阅读

有关 router 行为、第三方 skill packages 和部署范围的详细说明，请参阅
[DisCo Workflows](disco-workflows.zh.md)、
[AREX-Skill Library 指南](../skills/README.md)和
[DisCo CLI README](../cli/README.md)。
