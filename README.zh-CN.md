<div align="center">
  <img src="assets/silverwolf-comfyui-sticker.png" width="360" alt="银狼操作彩色 ComfyUI 节点图贴纸">

  # Shenrui ComfyUI Toolkit

  **面向 Agent 的 ComfyUI 本地/远程执行工具与实战手册。**

  [English](README.md) · [Skill 入口](SKILL.md) · [本地指南](references/local.md) · [远程指南](references/remote-server.md)
</div>

> [!IMPORTANT]
> 这是非官方社区项目，与 ComfyUI、Nous Research、HoYoverse 或任何模型提供方均无隶属或背书关系。

## 当前能力

- 将生图任务分流到本机 ComfyUI 或已获授权的远程实例。
- 运行 API 格式工作流，支持参数注入、输入上传、进度监控和原始输出下载。
- 转换常见的编辑器保存格式工作流，以独立随机 Seed 进行受控批量执行。
- 以 ComfyUI history 的真实结果判断成功，不把拿到 `prompt_id` 当成完成。
- 保留原始输出，并防止服务端文件名造成目录穿越写入。
- 仓库中不固化本机路径、服务器名称、个人账号或凭据。

仓库目前刻意保持精简。后续会逐步扩展模型同步、工作流整理、图像/视频生成流程和不同模型的提示词改写经验。

## 环境要求

- Python 3.10+
- 可访问的 [ComfyUI](https://github.com/comfyanonymous/ComfyUI) 实例
- API 格式工作流，或兼容的编辑器保存格式工作流
- 可选：`requests`，用于上传和更稳健的 HTTP 处理
- 可选：`websocket-client`，用于 WebSocket 实时进度

仓库不包含任何凭据。连接参数应在运行时通过环境变量、你已有的 SSH 配置或适当的命令行参数提供。

## 作为 Agent Skill 安装

克隆仓库后，将它复制或软链接到 Agent 使用的 skills 目录。以 Hermes 为例：

```bash
git clone https://github.com/Shenrui-Ma/shenrui-comfyui-toolkit.git
mkdir -p ~/.hermes/skills/creative
ln -s "$(pwd)/shenrui-comfyui-toolkit" \
  ~/.hermes/skills/creative/shenrui-comfyui-toolkit
```

入口文件是 [`SKILL.md`](SKILL.md)。本仓库不会自动覆盖现有 ComfyUI 安装或已有 Skill。

## 快速开始

### 本地 ComfyUI

```bash
export COMFY_URL='http://127.0.0.1:8188'

python3 scripts/run_workflow.py \
  --host "$COMFY_URL" \
  --workflow /path/to/workflow_api.json \
  --args '{"prompt":"你的提示词","seed":-1}' \
  --output-dir ./outputs \
  --ws
```

### 远程 ComfyUI

只能连接你有权使用的实例。常见 SSH 转发方式如下：

```bash
export REMOTE_USER='your-user'
export REMOTE_HOST='your-host'
export LOCAL_PORT='8188'
export REMOTE_PORT='8188'

ssh -N \
  -L "127.0.0.1:${LOCAL_PORT}:127.0.0.1:${REMOTE_PORT}" \
  "${REMOTE_USER}@${REMOTE_HOST}"

export COMFY_URL="http://127.0.0.1:${LOCAL_PORT}"
```

然后继续用 `--host "$COMFY_URL"` 调用同一个 runner。预检和任务归属要求见[远程指南](references/remote-server.md)。

### 编辑器保存格式工作流

```bash
python3 scripts/run_saved_workflow_batch.py \
  --host "$COMFY_URL" \
  --workflow /path/to/saved_editor_workflow.json \
  --prompt '你的提示词' \
  --count 1 \
  --output-dir ./outputs
```

复杂工作流应先生成 1 张并核对参数，再扩大批量数量。

## 仓库结构

```text
.
├── SKILL.md                         # Agent 指令和路由规则
├── references/
│   ├── local.md                     # 本地 ComfyUI 流程
│   └── remote-server.md             # 获授权的远程执行流程
├── scripts/
│   ├── _common.py                   # 通用网络与安全辅助函数
│   ├── run_workflow.py              # API 格式工作流 runner
│   └── run_saved_workflow_batch.py  # 编辑器格式批量 runner
├── tests/                            # 回归测试
└── assets/                           # 仓库视觉素材
```

## 安全与隐私

- 禁止提交 API Key、密码、Cookie、SSH 私钥、非公开主机名和真实基础设施路径。
- 发布工作流 JSON 或生成图片前检查元数据；其中可能包含提示词、本机路径、模型名和输入文件名。
- 将第三方自定义节点和未知工作流视为可执行代码。
- 未确认任务归属和授权前，不终止远程进程，也不占用 GPU。
- 凭据优先放在环境变量中；命令行参数可能被 shell 历史或进程列表保留。

## 后续计划

- 模型盘点、校验和同步流程
- 可复现的精选生图工作流
- 图生视频与文生视频执行指南
- 不同模型系列之间的提示词改写经验
- 工作流依赖检查与恢复工具
- 在稳定目录结构下增加更多 Agent Skills

## 开发与验证

运行不依赖第三方库的回归测试：

```bash
python3 -B -m unittest discover -s tests -v
```

使用 `python3 -B` 调用两个 runner 的 `--help`，不会生成 Python 字节码缓存。

## 来源与许可证

部分通用 runner 代码改编自 [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) 中的 ComfyUI skill，贡献者信息见 [`NOTICE.md`](NOTICE.md)。仓库内的软件与文档采用 [MIT License](LICENSE)，第三方名称、商标和角色形象除外。

银狼贴纸是为本仓库生成的非官方同人素材。银狼与《崩坏：星穹铁道》的相关权利归各自权利人所有，该角色形象不适用本仓库的软件 MIT 许可。
