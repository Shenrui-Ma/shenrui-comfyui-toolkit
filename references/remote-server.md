# 远程服务器 ComfyUI 生图分支

## 适用条件

- ComfyUI、模型和计算设备位于其他机器。
- Agent 已获得一个可访问的 HTTP(S) 地址；或者经授权通过 SSH 建立本地端口转发。
- 连接信息由使用者在运行时提供，不写入 Skill。

## 1. 设置通用变量

直接访问远程服务时：

```bash
export COMFY_URL='https://comfy.example.invalid'
```

通过 SSH 本地转发时：

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

不要把上述变量的实际值提交到 Skill、版本库或公开日志。

## 2. 验证目标实例

```bash
curl -fsS --max-time 5 "${COMFY_URL}/system_stats" | python3 -m json.tool
curl -fsS --max-time 5 "${COMFY_URL}/queue" | python3 -m json.tool
curl -fsS --max-time 10 "${COMFY_URL}/object_info" >/tmp/comfy_object_info.json
```

检查：

- 响应确实来自 ComfyUI；
- 设备和版本符合预期；
- 队列状态明确；
- 工作流所需节点存在。

若使用远程 Shell，可在授权范围内查看自己的进程和设备状态：

```bash
ssh "${REMOTE_USER}@${REMOTE_HOST}" '
  ps -u "$USER" -f | grep -E "ComfyUI|main.py|comfy launch" | grep -v grep || true
  nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv
'
```

只操作已确认归属且获授权的进程和设备。

## 3. 获取保存工作流

若服务提供保存工作流 API，可直接使用。若接口被禁用，可在授权范围内通过远程文件系统读取：

```bash
export REMOTE_WORKFLOW_DIR='/path/to/ComfyUI/user/default/workflows'

ssh "${REMOTE_USER}@${REMOTE_HOST}" \
  "find '${REMOTE_WORKFLOW_DIR}' -type f -name '*.json' -maxdepth 3 -print"
```

复制选定工作流：

```bash
scp "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_WORKFLOW_DIR}/WORKFLOW.json" \
  /tmp/WORKFLOW.json
```

- 使用通用路径占位符，不在公共 Skill 中写真实服务器目录。
- 若存在同名文件，保留相对路径和修改时间，避免选错版本。
- 工作流内容本身也可能包含私有路径或提示词；公开前单独脱敏。

## 4. 预检模型、节点和输入

- 在 `/object_info` 中检查所有自定义节点 class type。
- 检查 checkpoint、LoRA、VAE、ControlNet 等资源是否被目标实例识别。
- 本地参考图必须先上传到远程 ComfyUI，不能把本机路径直接写入远程工作流。
- 编辑器 JSON 转 API 时，linked widget 也会消耗 `widgets_values`；先单张核对 Seed、尺寸和提示词对应的节点。

## 5. 执行

API 工作流：

```bash
python3 scripts/run_workflow.py \
  --host "$COMFY_URL" \
  --workflow /tmp/workflow_api.json \
  --args '{"prompt":"原始提示词","seed":-1}' \
  --output-dir ./remote-outputs \
  --ws
```

编辑器保存工作流：

```bash
python3 scripts/run_saved_workflow_batch.py \
  --host "$COMFY_URL" \
  --workflow /tmp/WORKFLOW.json \
  --prompt '原始提示词' \
  --count 1 \
  --output-dir ./remote-outputs
```

先生成 1 张验证，正确后再批量；每张使用新的随机 Seed。

## 6. 监控、下载和溯源

- 保存 `prompt_id`、Seed、工作流文件名和输出文件名。
- 主动轮询 `/history/{prompt_id}`；按任务进展而不是单纯耗时判断停滞。
- 优先通过 `/view` 下载原始输出。
- 如经远程文件系统复制，分别计算远端与本地 SHA-256 并比对。
- 对外报告时隐藏主机名、账号、真实目录和认证信息。

通用哈希示例：

```bash
ssh "${REMOTE_USER}@${REMOTE_HOST}" 'sha256sum /path/to/output/OUTPUT.png'
shasum -a 256 ./remote-outputs/OUTPUT.png
```

## 7. 失败处理

- 端点不可用：检查地址、转发进程、远程监听端口和 ComfyUI 进程。
- `/prompt` 返回 400：按响应中的节点 ID 和字段错误修复工作流，不盲目重启。
- 设备繁忙：等待或切换已获授权的空闲设备；不碰归属不明的任务。
- 已确认无进展：保存错误、Prompt ID 和工作流版本后再恢复，不裁剪输出或冒充成功。

## 8. 完成检查

- [ ] 目标端点和实例已验证
- [ ] 工作流来源和版本明确
- [ ] 节点、模型和输入均存在
- [ ] 每张 Seed 独立
- [ ] Prompt ID 全部完成
- [ ] 原始文件已下载并机械验证
- [ ] 对外输出不含私有连接信息
- [ ] 交付完成
