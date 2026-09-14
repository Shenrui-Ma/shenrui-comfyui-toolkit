# H3 原生续接（Ref2VA latent 续接）

把上一段 H3 片段的联合音视频 latent 直接固定成下一段的 conditioning 行，让动作和声音跨剪辑点继续。上一段的尾部从它自己的 latent 里直接切出，不解码、不缩放、不重编码；固定的音频窗口右端对齐接缝、往回延伸，因此模型是接着你的配乐走，而不是另起一段听起来相近的声音。

**状态：接口与依赖已锁定，本仓库未复制上游图与节点实现，也未在公开配置下运行过。** 需要生成时按下面固定的版本取用。

## 与另一个 H3 图的分工

| 图 | 用途 |
| --- | --- |
| [H3 Ref2VA 对白基础图](../ref2va-dialogue/) | 独立分段生成，段与段之间没有 latent 续接 |
| 本包 | 有跨段续接要求时的执行包 |
| [H3 首帧动态立绘](../i2v-live-portrait/) | 首帧图生视频加 RIFE 插帧，不涉及续接 |

需要续接却用前两个图，出来的就是「动作相似、接缝是断的」。三者的节点依赖不能互相替代。

## 取用固定版本

上游节点包不在本仓库内，按 [dependencies.lock.json](dependencies.lock.json) 锁定的版本安装：

```text
仓库：https://github.com/NikoDemon80/ComfyUI-H3-Motion-Context
版本：tag v0.6.2 / commit 5335715abe54c1a9bfbe3494da29aae3e8635ce3
许可：GPL-3.0
路径：ComfyUI/custom_nodes/ComfyUI-H3-Motion-Context
```

示例图同样在上游，按 tag 取用并核对哈希：

```text
example_workflows/MiniMax H3 - fl2va - ref2va.json
sha256 d50b3050921183af6f0f8819fbdd79d88d8c1a37c28d40188b63a6eda53a32aa
```

本仓库只保留接口合同与依赖锁，复制过来的话会同时引入 GPL-3.0 代码与 MIT 声明冲突，也会让上游修好的布局适配停在旧版本。

## 使用

1. 先按 [interface.json](interface.json) 的 `runtime_checks` 对照目标实例 `/object_info`，确认六个节点类、输入类型与模型枚举都存在，并确认 ComfyUI 不低于 0.34.0。缺节点先装固定版本，不要静默断开续接继续提交。
2. 第一段按 `Load=0`、`Save=1` 配置；第 N 段用 `Load=N-1`、`Save=N`。Load、Save 与 Chain 必须在同一画布分组内，否则按钮无效。
3. `trim_frames` 一律从 `MiniMaxH3MotionContext` 的输出接过来，画面和声音交给同一个 Trim 节点。只裁画面的做法会让整条音轨比视频长 `trim_frames` 帧，24fps 下 5 帧就是 208ms。
4. 串行生成。上一段完成、latent 存盘后才提交下一段；断线先查原队列与 history，不重复提交。
5. 保留 `match_tail=true`，让音频时长严格等于 `frames/fps`。H3 的音频栅格四舍五入到最近的步，每段会多或少约 8ms，不处理会在每个接缝累积。
6. 用 `MiniMaxH3MotionContextSeamProbe` 测量接缝，再拼接成片。检查实际帧数、时长、音轨与接缝，记录验证范围。

## 可改与不可改

- 可直接填：角色图或首帧、提示词、seed、输出前缀、宽高与 length、latent 保存目录。
- 属于预定义选择：`context_length`（5 / 22 / 39 / 56）、`audio_context_length`、`match_tail`。
- 属于改行为、不算原模板复现通过：更换未验证的 H3 权重或量化、替换节点包版本、改成另一套续接语义、删掉 Trim 或音频分支。

## 边界

- 上下文窗口会从成片开头扣掉：`context_length=56` 约等于每段花 2.3 秒渲染最终丢弃的帧。
- `v0.3.1` 是最后一个兼容 ComfyUI 0.33.4 及更早版本的发行；版本与目标 ComfyUI 必须配对。
- Recipes 里「一点一滴刺痛我的心」现在改用 [H3 Core AV latent 续接](../ref2va-core-continuation/) 那套图：latent 的拆分、保存、读回全部走 Core 官方节点。两包的续接语义相同，但 latent 文件的落盘格式不同，**不能一边写一边读**。
- 本包不做插帧、不做超分、不决定剪辑节奏。那些属于 Recipes 的模板规则。
