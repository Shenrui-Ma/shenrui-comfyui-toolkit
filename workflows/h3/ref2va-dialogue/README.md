# H3 Ref2VA 对白基础图

来源：Video ReGen Recipes 的独立分段音视频制作方法。此处维护具体 API 节点结构；剧情、素材绑定和逐段构建由 [Recipes](https://github.com/Shenrui-Ma/video-regen-recipes/tree/main/templates/anime-dialogue-scene/mygo-ave-mujica)负责。

图中保留模型、尺寸、帧数、种子、提示词与输出前缀占位符。构建器还需添加实际 LoadImage / LoadAudio 节点和动态参考输入。它不能直接提交到 `/prompt`。

基线为 BasicGuider、res_multistep/simple、20步、24fps，两路 VAE 解码后 CreateVideo / SaveVideo。没有跨段 latent 续接；不能用于需要原生 Motion Context 的舞蹈配方。

记录来源于已有图的参数化整理，尚未在新环境实跑。部署时按当前 `/object_info` 核验 H3 节点、模型枚举和动态输入；不包含权重或用户素材。
