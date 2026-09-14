# H3 Core AV latent 续接（Ref2VA）

用 Core 官方节点存取上一段的联合音视频 latent，再由 `MiniMaxH3MotionContext` 把它固定成下一段的 conditioning，让画面和声音跨剪辑点继续。

- 保存：Core `LTXVSeparateAVLatent` 把采样器输出的联合 AV latent 拆成视频、音频两路，各接一个 Core `SaveLatent`。
- 读取：下一段用两个 Core `LoadLatent` 读回，`LTXVConcatAVLatent` 重组后送进 `MiniMaxH3MotionContext.context_latent`。
- 裁切：发布帧的裁切在当前图里做——`ImageFromBatch` 的 `batch_index` 接 Motion Context 输出的 trim 值，画面与声音走同一条裁切路径。

本包**自带参数化图**（`first.api.template.json`、`continue.api.template.json`），占位符是整值 `{{name}}`，填类型化数值后可直接提交。

## 与另一个续接包的分工

| 包 | latent 存取方式 | 适用 |
| --- | --- | --- |
| [H3 原生续接](../ref2va-native-continuation/) | 由上游节点包自己的 Save/Load/Chain 节点负责 | 目标环境已按 v0.6.2 安装该包的完整节点集 |
| 本包 | 全部用 Core 官方节点拆分、保存、读回、重组 | 希望续接链路只依赖 Core 加一个 `MiniMaxH3MotionContext` |

两者续接语义相同（都是拿上一段的联合 AV latent 做 conditioning），差别只在 latent 怎么落盘和读回。**不要混用两套的存取节点**：一边用 Core `SaveLatent` 落盘，另一边用上游节点读，路径格式对不上。

## 参数

整值替换，不做字符串插值。以下是各占位符的类型：

| 占位符 | 类型 / 说明 |
| --- | --- |
| `diffusion_model`、`text_encoder`、`video_vae`、`audio_vae` | 从目标实例 `/object_info` 对应枚举中取的文件名 |
| `prompt` | 整段提示词文本 |
| `width`、`height` | 整数（64 的倍数） |
| `sample_frames` | 整数，须落在 17k+5 网格上 |
| `seed` | uint64 整数；以字符串保存的 seed 提交前必须解析成整数 |
| `steps` | 整数 |
| `visible_frames` | 整数，本段发布帧数 |
| `video_prefix` | `SaveVideo` 的输出前缀 |
| `video_latent_prefix`、`audio_latent_prefix` | 两路 `SaveLatent` 各自的前缀 |
| `reference_image`、`reference_video` | 本段的角色参考图与驱动视频切片 |
| `previous_video_latent`、`previous_audio_latent` | 上一段两路 latent 的路径（仅续段） |
| `context_length` | 预定义取值 5 / 22 / 39 / 56（仅续段） |
| `audio_context_length` | 本图基线 24（仅续段） |

第一段用 `first.api.template.json`（不含续接节点）；第 N 段用 `continue.api.template.json`，读第 N-1 段的两路 latent。

## 可改与不可改

- 可直接填：角色参考图、驱动切片、提示词、seed、宽高与帧数、输出前缀、前驱 latent 路径。
- 属于预定义选择：`context_length`、`audio_context_length`。
- 改了就不算同一工作流：替换节点包版本、换成另一套续接语义、删掉音频分支、换未验证的 H3 权重或量化。

## 边界

- 本仓库只整理图结构与接口，**没有启动过 ComfyUI、没有加载权重**，本包不在公开配置下实跑过。
- 同一节点方案的图在 Video ReGen Recipes 的既有环境完成过真实首段采样；那是方案层面的证据，不等于本包在新环境跑通。
- 本包不做插帧、不做超分、不决定剪辑节奏。那些属于模板规则，留在 [Recipes](https://github.com/Shenrui-Ma/video-regen-recipes)。
- 需要续接却用了独立分段图，出来的是「动作相似、接缝是断的」。
