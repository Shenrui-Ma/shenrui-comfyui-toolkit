# 本地 ComfyUI 生图分支

## 适用条件

- ComfyUI 与 Agent 在同一台机器。
- 常用地址为 `http://127.0.0.1:8188`。
- `lsof` 显示端口由本机 ComfyUI/Python 监听，而不是 SSH 转发。

## 1. 服务预检

```bash
curl -fsS http://127.0.0.1:8188/system_stats | python3 -m json.tool
curl -fsS http://127.0.0.1:8188/queue | python3 -m json.tool
curl -fsS http://127.0.0.1:8188/object_info >/tmp/comfy_object_info.json
```

检查：

- 服务返回 JSON；
- GPU/后端信息与当前机器一致；
- 队列状态明确；
- 工作流用到的节点在 `object_info` 中存在。

如果端点不可用，先定位本机 ComfyUI 安装目录和启动命令。不得用一个空壳 HTTP 服务冒充 ComfyUI。

## 2. 准备输入

- 工作流优先使用已验证过的 API JSON。
- 若只有编辑器保存 JSON，先执行单张转换测试。
- 参考图可使用 runner 的上传参数，或复制到本机 ComfyUI `input/`。
- 用户指定的提示词、尺寸、模型和采样参数不擅自修改。

## 3. 执行

API 工作流：

```bash
python3 scripts/run_workflow.py \
  --host http://127.0.0.1:8188 \
  --workflow /absolute/path/workflow_api.json \
  --args '{"prompt":"原始提示词","seed":-1}' \
  --output-dir /absolute/path/output \
  --ws
```

编辑器保存工作流：

```bash
python3 scripts/run_saved_workflow_batch.py \
  --host http://127.0.0.1:8188 \
  --workflow /absolute/path/editor_workflow.json \
  --prompt '原始提示词' \
  --count 1 \
  --output-dir /absolute/path/output
```

批量时每张使用新 Seed。先测试 1 张，通过后再扩大数量。

## 4. 监控与失败处理

- 记录 `/prompt` 返回的 `prompt_id`。
- 以 `/history/{prompt_id}` 中的真实状态和输出列表为准。
- 若校验失败，读取 ComfyUI 返回的节点 ID、class type 和字段错误，修正对应节点，不要盲目重试。
- 若显存不足，先检查自己的队列和进程；未经允许不使用 `novram`、CPU VAE 等改变工作质量的规避方案。
- 队列非空时不重启；先等现有任务完成或按用户指示处理。

## 5. 输出与交付

1. 将该批次输出放在独立目录，例如：

```text
~/Downloads/comfyui-batch-YYYYMMDD-HHMMSS/
```

2. 每张做机械校验：

```bash
file output.png
sips -g pixelWidth -g pixelHeight output.png
shasum -a 256 output.png
```

3. 单张需要发送时，复制原始 PNG 到 Hermes 允许的媒体目录，例如：

```text
~/.hermes/cache/images/
```

4. 批量默认只告知本地目录，不逐张刷 Telegram；除非用户明确要求全部发送。

## 6. 本地完成检查

- [ ] 服务确实是本机 ComfyUI
- [ ] 工作流和节点预检通过
- [ ] 每张 Seed 独立
- [ ] 所有 Prompt ID 已完成
- [ ] 输出数量正确且可解码
- [ ] 原始 PNG 已保存/发送
