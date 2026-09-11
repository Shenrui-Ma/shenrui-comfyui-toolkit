# H3 首帧动态立绘

把 ComfyUI 生成的角色图作为实际首帧，生成单镜头动作与同步声音，再用 RIFE 从 24fps 插帧到 60fps。完整的参考图制作、逐镜头恢复和合集剪辑由 [Video ReGen Recipes](https://github.com/Shenrui-Ma/video-regen-recipes) 编排。

**状态：从已有 API 图参数化整理，仅检查文件，未在公开配置下重新推理。** 此图是独立首帧图生视频，不是 Ref2VA 对白或跨段 latent 续接。

## 使用

1. 先在 ComfyUI 生成所选角色、服装与场景的首帧，记录图片文件和对应生成任务。复用图片时同样核对角色与镜头绑定；不能只把图片描述写进视频提示词。
2. 读取目标 ComfyUI 的 `/object_info`，检查下表所有节点、模型文件枚举与输入类型。准备 H3 FL2VA 模型、兼容文本编码器、视频 VAE、音频 VAE 和 RIFE 权重。不能把不同 H3 模式或不同 VAE 当成可互换模型。
3. 将首帧上传到目标 ComfyUI，或确认它位于该实例的 input 目录。用服务器实际可读的 input 相对名称填入 `first_frame`；本机图片路径不能直接传给远程实例。
4. 按 [parameters.json](parameters.json) 解析并替换 [api.template.json](api.template.json) 的完整占位值。宽、高、length 和 seed 必须保持 JSON 整数；提示词中的引号和换行交给 JSON 序列化器处理。每个镜头使用独立 seed、输出前缀和任务记录。
5. 全部参数解析完成且依赖核验通过后，才提交 `/prompt`。保留 `prompt_id` 并从该任务的 history 取回输出；连接中断先查询原任务，不重复提交。
6. 运行后的成品需核对实际视频帧数、时长、60fps 与音轨，再交给合集剪辑。输入 `length` 与最终帧数不是同一个数；不要通过改播放帧率冒充插帧，也不要默认裁到音频长度。

模板没有包含权重、角色素材或连接信息。ComfyUI 的部署、模型下载和任务提交均由调用方按自己的环境完成。

## 固定链路与依赖

| 节点 | 作用 / 必需连接 |
| --- | --- |
| `UNETLoader` → `MiniMaxH3MemoryEfficientSageAttentionPatch` | H3 模型与原图保留的注意力补丁；调度器和 Guider 都连接补丁输出 |
| `CLIPLoader`，两路 `VAELoader` | `type=minimax` 文本编码器，分开的 H3 视频 / 音频 VAE |
| `LoadImage` → `MiniMaxH3ImageToVideo.first_frame` | 首帧硬连接 `["137", 0]`，不能仅靠提示词声明参考图 |
| `BasicGuider`，`RandomNoise`，`BasicScheduler`，`KSamplerSelect` → `SamplerCustomAdvanced` | `20 steps`、`res_multistep`、`simple`、`denoise=1.0` |
| `VAEDecode` / `VAEDecodeAudio` | 同一采样结果分别解码画面与原生声音 |
| `RIFEInterpolation` | 24 → 60fps，`scale=2.0`、`batch_size=1`、`use_fp16=true`；模型名参数化 |
| `VHS_VideoCombine` | 接收 RIFE 画面与原生音频，H.264 MP4、yuv420p、CRF 16、60fps |

H3 节点、Sage 补丁、RIFE 和 VideoHelperSuite 的实现必须与目标实例的节点定义相符。此基础图没有 SolAttn / EasyCache，但仍需要 `MiniMaxH3MemoryEfficientSageAttentionPatch`。缺节点时先安装兼容实现或另建经过核验的适配图；不能悄悄断开补丁、音频或 RIFE 继续提交。具体节点仓库和版本不能仅凭同名猜测。

## 尺寸和时长

| 参数组 | width × height | H3 length | 说明 |
| --- | --- | --- | --- |
| `portrait-10s` | 864 × 1344 | 243 | 基础来源图的约 10 秒配置 |
| `portrait-15s` | 864 × 1344 | 362 | 来自另一张约 15 秒图的长度；移到本基础图尚未实跑 |

原生时间基准为 24fps；生成节点可能对长度作模型适配，RIFE 的端点策略也可能影响输出帧数。243 / 362 是来源图的输入参数，不能直接许诺精确 10 / 15 秒成品，也不要改成 60fps 下的 600 / 900。

15 秒来源使用另一套注意力 / 缓存补丁，包含 `PathchSageAttentionKJ`、`SolAttnPatch` 与 `EasyCache`。本目录没有把那套补丁或其效果声明合并进基础图；只是记录一个可配置的长度。不同量化、注意力实现和硬件也可能改变结果。

## 整理记录

基础来源图 SHA-256：`2b21a42087edae0e2df8c3568f27e79c9674a73564a5d73bc121badbb2385522`。保留全部 16 个节点及原有连接，只参数化权重、首帧、提示词、尺寸、length、seed 和输出前缀，并将 `save_metadata` 设为 `false`。保存任务清单用于恢复；不要把完整工作流和提示词自动嵌入分享的视频文件。

[validation.json](validation.json) 记录结构、依赖闭包、占位符及索引哈希检查。本次未启动 ComfyUI、读取模型或生成 / 渲染任何图片视频，也未验证新环境的显存需求与成品质量。
