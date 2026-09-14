# H3 独立环境：安装与只读验收

MiniMax H3 视频推理所需的整套环境——ComfyUI Core、H3 自定义节点、Python/CUDA 依赖闭包、模型权重、兼容补丁。**这个目录是可复用的环境定义，不属于任何单个模板**；模板通过自己的 `workflow.lock.json` 引用这里的图与版本。

**验收边界：安装计划、源码补丁和 CPU 侧测试已检查，完整干净 Linux 安装与 GPU 推理未验。任何“装成功”的结论都只指命令返回成功，不代表这套续接能跑。**

## 0. 环境是独立的，不要改建用户已有的环境

这是本环境最重要的一条约束，因为**为一个模板改了环境，往往会打断用户其他的 ComfyUI 任务**。

- `install.py` 只接受**不存在**的 `--target` 目录；已有的 ComfyUI、共享 `site-packages` 永远不是安装目标。
- 新建目录里会写入 `.h3-isolated-install` 标记和它自己的 `.venv`；补丁工具只认这个标记，**不会**去改共享安装。
- 启动的是独立实例，用独立端口。不要为了这个环境去重启、覆盖或改动用户正在用的实例。
- 需要复用它时，让新模板引用同一个 `--target`，而不是再装一套。

模型权重是唯一可以共用的部分：如果用户机器上已有同哈希的权重，直接复用，不要重下（见第 5 节的核查规则）。

## 1. 目标机器、依赖与许可

- Linux **x86_64，CPython 3.10，glibc >= 2.35**（例如 Ubuntu 22.04 级别）；不支持在 macOS/MPS、Windows、ARM 或 ROCm 上安装。脚本可在其他平台打印计划，不表示目标兼容。
- 需要已有 NVIDIA 驱动、`nvidia-smi`、`git`、`ffmpeg`、`ffprobe`，以及能创建 venv 的 Python 3.10。下载模型另需 `curl` 和 `python3`。这些系统工具不由安装脚本安装。
- 锁定 PyTorch `2.5.1+cu121`、torchvision `0.20.1+cu121`、torchaudio `2.5.1+cu121`、Triton `3.1.0`、comfy-kitchen `0.2.26`。锁内有全部 86 个 Python 包的公开 wheel URL、版本与 SHA-256，不是只列直接依赖。
- 观察过的服务是 A100 80GB PCIe，驱动 `535.129.03`。这不是最低显存/驱动承诺；其他 GPU、内存容量和片段尺寸未校准，安装前自行核对 CUDA 12.1 兼容性、空闲显存、RAM 和磁盘。
- 四个 H3 模型共 `42,470,585,471` 字节（约 39.55 GiB）。另留 wheels、pip 缓存、源码、latent、视频输出和下载临时文件的空间；该数值不是整套环境磁盘预算。
- 先读 `vendor/model-licenses/MiniMax-H3-LICENSE` 与 `NOTICE`。H3 是带地域及商业限制的社区许可，**不是 OSI 开源许可**；Qwen 衍生文本编码器另涉 Apache-2.0 来源。不能用 Apache 许可覆盖 H3 转换权重的条款。
- 不安装私有 `HermesH3Continuation`、`HermesH3MemoryEfficientSage`，不启用 `--use-sage-attention`。采用 Core / PyTorch 默认注意力。

## 2. 核实命令接口

以下命令只显示帮助：

```bash
python3 scripts/install.py --help
python3 scripts/apply_patches.py --help
python3 scripts/model_commands.py --help
python3 scripts/preflight.py --help
```

```text
usage: install.py [-h] --target TARGET [--python PYTHON]
usage: apply_patches.py [-h] --root ROOT [--apply]
usage: model_commands.py [-h] --comfy-root COMFY_ROOT
usage: preflight.py [-h] [--comfy-root COMFY_ROOT] [--python-site PYTHON_SITE]
                    [--url URL] [--object-info OBJECT_INFO]
                    [--inventory INVENTORY] [--verify-model-hashes]
                    [--platform PLATFORM] [--architecture ARCHITECTURE]
                    [--workflow-lock WORKFLOW_LOCK]
```

`install.py` 和 `model_commands.py` **只向 stdout 打印 shell 计划，不执行安装、下载或启动服务**。`apply_patches.py` 无 `--apply` 时只读。`preflight.py` 不导入 torch、不提交 prompt，网络仅 GET `/object_info` 和 `/system_stats`。

## 3. 在目标 Linux 上生成、审核、显式执行安装计划

把本目录放在目标 Linux 机器上，再从它的根目录生成计划。计划内嵌环境与目标的绝对路径，**不能把在另一台机器打印的计划原样执行**。`DEST` 必须是**不存在**的新目录，且父目录可写。

```bash
ENVIRONMENT="$PWD"
DEST="$HOME/h3-isolated-env"
python3 scripts/install.py --target "$DEST" --python python3.10 > install-plan.sh
bash -n install-plan.sh
```

打开 `install-plan.sh` 审阅后，只在批准安装的目标 Linux 上执行：

```bash
bash install-plan.sh
```

计划会检查 OS、架构、Python 和 glibc，拒绝已有目标或目标符号链接；创建 `.h3-isolated-install` 标记与 `DEST/.venv`；固定 checkout：

| 组件 | revision | 安装位置（相对 DEST） |
|---|---|---|
| ComfyUI Core | `6f7cd7fceaaf60d2669b554936394a7412c6fde5` | `ComfyUI` |
| H3 Motion Context | `f80e36bc1d7887a143b12e6645313fd6b9cd2aee` | `ComfyUI/custom_nodes/H3MotionContextOfficial` |

安装计划实际使用以下命令，不采用浮动 `pip install -r requirements.txt`：

```bash
"$DEST/.venv/bin/python" -m pip install --only-binary=:all: --no-deps --require-hashes \
  -r "$ENVIRONMENT/vendor/python/requirements-direct-linux-py310.lock.txt"
"$DEST/.venv/bin/python" -m pip check
```

direct 锁为全闭包的精确 wheel URL，不是“只有直接依赖”。`--no-deps` 依赖已锁全闭包，所以 **pip check 必须成功**。若下载、wheel 兼容、哈希或 pip check 失败，停止并保存错误，不移除哈希、不安装最新版、不污染共享 site-packages。

锁内 `runtime_dependency_conflicts` 记录了已有服务的 workflow-template 辅助包版本缺失/冲突；新锁修正这些辅助包，但不声称原服务全局 pip-check clean。当前收尾没有在目标 Linux 实际跑过 pip check。

## 4. 两个 hash-gated 补丁

安装计划在 pip check 后已调用以下两步；手动复核时仍只指向本次新建的独立 `DEST`：

```bash
"$DEST/.venv/bin/python" "$ENVIRONMENT/scripts/apply_patches.py" --root "$DEST" --apply
"$DEST/.venv/bin/python" "$ENVIRONMENT/scripts/apply_patches.py" --root "$DEST"
```

- `vendor/motion-context/payload-before-audio.patch`：把 payload patch 移出可选音频 gate。完整上游包仍需保留注册入口、`patch_layout.py`、`patch_payload.py` 等文件，不能只复制 `nodes.py`。
- `vendor/comfy-kitchen/output-index-int64.patch`：两处输出索引均在 stride 乘法**之前**提升到 int64；乘法后强转不能挽回溢出。保留 Apache 修改声明、上游与修改后源码及许可证。它不修复任意 tail-store race，也不证明所有 H3 形状的 GPU 正确性。

helper 会核对独立标记、路径范围、原文件 before/after SHA-256 与 vendored 修改后 SHA-256；两个文件先全部验证才写入，不强补未知源码。`--apply` 成功报告 `verified_patched`，再次只读应报告两项 `already_patched`。无 `--apply` 时 `patch_available` 只表示可以补，**不代表已经补好**。不要给共享安装伪造标记绕过保护。

## 5. 模型命令与逐文件校验

所有公开 URL、不可变 revision、字节数与 SHA-256 来自 `dependencies.lock.json`；不靠名称搜索任意同名文件。

**下载前先核查已有模型。** 检查目标环境的模型目录、配置的共享路径和可复用缓存，按锁核验文件完整性与版本。已齐全且可用时直接复用，不重复提醒下载或空间占用；仅在确认缺失后，下载前列出缺失项、需下载的数据量和预计新增磁盘占用，只计算缺失项。检查失败或路径不可访问时说明尚未核实，**不能当作模型缺失**。

| 用途 / loader | ComfyUI 下的目标 |
|---|---|
| H3 INT8 / UNETLoader | `models/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors` |
| 文本编码器 / CLIPLoader | `models/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` |
| 音频 VAE / VAELoader | `models/vae/minimax_h3_audio_vae_fp32.safetensors` |
| 视频 VAE / VAELoader | `models/vae/minimax_h3_video_vae_fp16.safetensors` |

只打印、审核，不下载：

```bash
python3 "$ENVIRONMENT/scripts/model_commands.py" --comfy-root "$DEST/ComfyUI" > model-plan.sh
bash -n model-plan.sh
```

只有使用者已读许可、确认适用地域/用途并批准下载后才执行：

```bash
I_ACCEPT_MINIMAX_H3_LICENSE=yes bash model-plan.sh
```

脚本检查该显式接受变量；HTTPS curl 续传到 `.part`，验证字节数和 SHA-256 后才重命名，目标已存在时只验证而不覆盖。哈希错误应停止并调查，不删除校验步骤。不要用 `python -O` 或 `PYTHONOPTIMIZE` 禁用计划里的 assert 校验。许可接受变量不是法律资格验证。本环境收尾未下载这些权重。

## 6. 启动自己的新实例

安装、pip check、补丁和模型校验完成后，选择**未占用**的 loopback 端口，另开终端显式启动新实例：

```bash
cd "$DEST/ComfyUI"
"$DEST/.venv/bin/python" main.py --listen 127.0.0.1 --port 8188
```

该启动行来自安装计划；本次未实际启动或重启服务。正常加载安装且启用的节点，不加全禁用/白名单参数，**不改动用户其他实例**。检查启动日志中的 import error；节点不存在可能是包缺失、被禁用、导入失败或注册/API 不兼容，不能一律称为“未安装”。H3 图所需 22 类节点中 21 类是 Core，只有 `MiniMaxH3MotionContext` 来自公开自定义包。

## 7. 只读 preflight 与验收标准

用环境自己的 Python（不要用控制端 Python 版本代替目标环境版本）：

```bash
"$DEST/.venv/bin/python" "$ENVIRONMENT/scripts/preflight.py" \
  --comfy-root "$DEST/ComfyUI" \
  --python-site "$DEST/.venv/lib/python3.10/site-packages" \
  --url http://127.0.0.1:8188 \
  --verify-model-hashes
```

此命令会读取锁内选定的源码哈希、Python 包元数据、INT8 源码、模型大小/完整 SHA-256，以及实时节点/schema。模型哈希检查会读取全部约 42 GB；省略 `--verify-model-hashes` 不能证明权重字节身份。它不是完整 git 工作树审计，也不执行 CUDA kernel。

**检查某个模板的图能否在这个实例上跑**，把该模板的锁交给它：

```bash
"$DEST/.venv/bin/python" "$ENVIRONMENT/scripts/preflight.py" \
  --comfy-root "$DEST/ComfyUI" --url http://127.0.0.1:8188 \
  --workflow-lock /path/to/<template>/references/workflow.lock.json
```

不给 `--workflow-lock` 时只做环境检查，`graphs` 记为 `skipped`，并在 `pending` 里说明模板图未检查。

没有服务时可做离线静态检查：

```bash
python3 scripts/preflight.py --object-info vendor/audit/object-info.contract.json
```

在非 Linux 控制端仅检查“目标计划 + 实时 schema”可显式写：

```bash
python3 scripts/preflight.py --url http://127.0.0.1:8188 \
  --platform Linux --architecture x86_64
```

这两个 override **不探测/认证目标硬件**，也不把本地 macOS 变成受支持运行环境。

可选 `--inventory` 接受按包 id（`comfyui`、`motion-context`）组织的证据：

```json
{"motion-context": {"installed": true, "disabled": false, "import_error": "从本次启动日志摘录的具体错误"}}
```

只填真实证据，不凭空给出 import_error；发布日志前移除用户目录、文件列表和凭据。

解释输出：

- `issues` 表示发现的问题；`static_checks_pass` 只描述本次执行的静态检查。
- `pending` 列出未检部分。模板的 image/video/双路 latent 占位符未 staging 会进入 pending；不要为了清零它们上传私有文件或提交推理。
- `ready_for_inference` **固定为 false**；即使 exit 0、`issues: []`，也不代表干净安装、资源容量和生成已经通过。
- 完整运行验收还需使用者另行批准素材 staging 与推理。

## 8. 媒体依赖

实际运行前还须确认 FFmpeg 的 AAC 编码可用：有 `ffmpeg` 命令或 `ffprobe` 通过，不代表能编 AAC。旧系统 FFmpeg 可能在 H3 采样成功后拒绝 AAC；应在任务私有 PATH 里选择新版 FFmpeg 并实测完整拼接与配乐，不要修改共享服务或用 experimental 参数掩盖问题。具体流程见 Recipes 里的媒体预检说明。

## 9. 本目录自检

环境测试无需安装 GPU 库：

```bash
python3 -m unittest discover -s environments/h3/tests -v
```

覆盖：计划不执行、模型命令 URL/哈希且不下载、隔离标记与 hash-gated 补丁、INT8 整数提升、模型缺失、禁用节点、链接槽/类型、V3 autogrow/dynamic combo、不支持平台报告。**这不是 Linux/CUDA 安装测试。**

`vendor/audit/object-info.contract.json` 只保留所需节点的 input/output/module schema 和公开选项；用户 image/video/latent 与模型文件枚举均为空，不发布服务输入目录清单。
