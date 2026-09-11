# SDXL 两次采样角色图

原创工作流整理：**Shenrui Ma（四倍体果蝇）**。

从已有角色PNG所记录的最终保存分支整理：SDXL checkpoint、独立VAE、CLIP层设置、四个LoRA槽、1344×1344首采样、模型放大及2352×2352缩放、VAE重编码、0.1降噪二次采样、最终SaveImage。

保留35步、CFG7、euler_ancestral/normal和两个sampler共享seed的配置。已移除不通向最终输出的支路，并绕过强度明确为0的ControlNet；model=0但clip=1的LoRA仍保留，不能当成完全禁用。

[参数表](parameters.json)中的模型和提示词需由使用者填写，原角色、风格LoRA私有文件名和提示词未保留。模型须匹配SDXL/Illustrious家族；全部槽位要绑定实际可用文件，若省略某个LoRA则正确重接MODEL/CLIP，不能填空名字。

需要cowboy shot时，正向提示词明确人物、固定服装、头部至大腿的景别、无遮挡脸部和简洁背景。这里的景别由提示词决定，不是裁切保证。

图是参数化API模板，不能直接提交；先填完占位符，再核验当前节点和输出祖先。新的公开化图未重新生图，不能保证与原参考图片像素一致。
