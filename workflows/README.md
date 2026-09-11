# 工作流目录

[机器可读索引](index.json)提供工作流 ID、模型家族、文件位置、SHA-256 和验证状态。图的格式与运行条件以各目录说明为准；带占位符的模板先渲染并核验，再提交。

- [H3 Ref2VA 对白基础图](h3/ref2va-dialogue/)：独立分段的联合音视频生成，配合 Recipes 构建器。
- [H3 首帧动态立绘](h3/i2v-live-portrait/)：首帧图生视频、原生音频与 RIFE 24 → 60fps，配合角色合集模板。

具体工作流在此维护，完整创作步骤与素材模板放在 [Video ReGen Recipes](https://github.com/Shenrui-Ma/video-regen-recipes)。消费者应记录使用的 commit 和文件哈希；找不到匹配工作流时如实说明，不能用不同模型或生成模式冒充。

- [SDXL 两次采样角色图](images/sdxl-two-pass-cowboy-shot/)：可参数化的 cowboy shot 角色参考图链路。
