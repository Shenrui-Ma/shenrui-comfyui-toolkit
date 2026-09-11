---
name: shenrui-comfyui-toolkit
description: Use when generating images through ComfyUI. Route the task to either a local ComfyUI instance or a remote ComfyUI service, preserve the requested workflow and parameters, monitor real execution, download original outputs, and verify delivery.
version: 0.1.0
author: [Shenrui Ma, kshitijk4poor, alt-glitch, purzbeats]
license: MIT
---

# Shenrui ComfyUI Toolkit：本地与远程生图

## 目标

使用现有 ComfyUI 工作流完成真实生图，并根据运行位置分流：

- **本地 ComfyUI**：ComfyUI 与执行 Agent 在同一台机器。
- **远程 ComfyUI**：模型和工作流位于其他机器，通过可访问的 HTTP(S) 地址或 SSH 本地端口转发调用。

本 Skill 是可公开分享的通用版本，不应写入任何个人或组织专属信息、非公开地址、服务器别名、专用目录、账号或认证信息。

## 安全规则

1. 凭据只能通过环境变量、系统钥匙串或已有认证配置读取；禁止把密码、Token、API Key、私钥和连接串写入 Skill、日志或输出文件。
2. 文档示例只使用 `REMOTE_HOST`、`REMOTE_USER`、`COMFY_URL`、`/path/to/...` 等占位符。
3. 不输出完整环境变量，不复制认证文件，不将私有服务器信息固化为默认值。
4. 远程进程与 GPU 只在确认归属和授权后操作；不终止归属不明的任务。

## 生成规则

1. 用户明确指定工作流、模型、采样器、尺寸、提示词或参考图时保持原样；未经要求不改写。
2. 批量生图每张使用独立随机种子。
3. 提交后主动轮询直到成功或失败；`prompt_id` 不是完成证明。
4. 下载并交付 ComfyUI 原始输出，优先 PNG；不得擅自转成 JPEG。
5. 只做机械验证：格式、尺寸、字节数、哈希、Prompt ID、Seed 和最终输出节点；不以视觉模型代替用户验收。
6. 优先交付工作流最终 `SaveImage` 输出；存在后处理时不得误发中间预览。
7. 批量结果放入独立本地文件夹；单张需要发送时，先复制到平台允许的媒体目录。
8. 报告真实报错并继续排查；禁止伪造成功或用其他模型冒充输出。

## 路由

### 本地分支

适用于 ComfyUI 与 Agent 在同一台机器。读取：

- `references/local.md`

### 远程分支

适用于 ComfyUI 位于其他机器。使用者先提供或配置可访问的 `COMFY_URL`；如使用 SSH 转发，由使用者提供 `REMOTE_USER`、`REMOTE_HOST` 和端口。读取：

- `references/remote-server.md`

## 通用执行流程

1. 确认工作流、提示词、参考图、数量、尺寸和输出目录。先查 `workflows/index.json`，按模型家族和生成模式选图；记录实际commit及文件哈希。若来自 Recipes，保持该配方已锁定的参数和版本，不自动更新或替换其工作流。
2. 判断工作流格式：
   - API 格式：顶层通常是节点 ID 映射，使用 `scripts/run_workflow.py`。
   - 编辑器格式：顶层通常含 `nodes`、`links`，使用 `scripts/run_saved_workflow_batch.py`。
3. 请求 `${COMFY_URL}/system_stats`、`${COMFY_URL}/queue`，必要时请求 `${COMFY_URL}/object_info`。
4. 确认自定义节点和模型存在；缺少依赖时不要直接排队。
5. 仅替换用户要求变化的字段；每次生成新的整数 Seed。
6. POST `/prompt`，记录 `prompt_id` 和 Seed。
7. 轮询 `/history/{prompt_id}`，以真实完成状态和输出列表为准。
8. 通过 `/view` 下载输出，保留原始文件和子目录信息。
9. 验证每个文件可解码、尺寸、格式、字节数和 SHA-256。
10. 按用户要求交付；批量结果默认给文件夹路径，避免一次发送过多媒体。

## 快速示例

先设置目标地址：

```bash
export COMFY_URL='http://127.0.0.1:8188'
```

API 格式工作流：

```bash
python3 scripts/run_workflow.py \
  --host "$COMFY_URL" \
  --workflow /path/to/workflow_api.json \
  --args '{"prompt":"用户原始提示词","seed":-1}' \
  --output-dir ./outputs \
  --ws
```

编辑器格式工作流：

```bash
python3 scripts/run_saved_workflow_batch.py \
  --host "$COMFY_URL" \
  --workflow /path/to/saved_editor_workflow.json \
  --prompt '用户原始提示词' \
  --count 1 \
  --output-dir ./outputs
```

复杂编辑器工作流的自动转换必须先运行 1 张并核对节点参数，不能未经验证直接批量。

## 成功标准

- ComfyUI history 显示成功；
- 输出数量与请求一致；
- 文件是可解码的原始输出；
- Prompt ID 与 Seed 已记录；
- 本地或远程来源明确，但报告中不泄露私有连接信息；
- 用户要求发送时，平台返回真实发送成功结果。

## 常见坑

- HTTP 端点可连接不代表目标实例、模型和 GPU 就是预期对象，必须检查 `/system_stats`。
- 远程保存工作流列表接口可能被禁用；可在授权范围内通过远程文件系统读取。
- 编辑器 JSON 中 linked widget 仍可能消耗 `widgets_values`，索引错位会使 Seed、尺寸等参数串位。
- `randomize` 是控制标记，不是合法 Seed；提交前必须生成整数 Seed。
- 队列为空不等于任务成功；必须查询 `/history/{prompt_id}`。
- 媒体路径必须位于发送平台允许的目录；批量文件优先以目录或压缩包交付。
- 不在队列非空时重启 ComfyUI，不操作归属不明的进程。
