# RMBG-2.0 角色去背景（Alpha + 蒙版）

把一张角色图的背景去掉，同时产出透明图和蒙版。四个节点，两个是 Core 的加载/保存，剩下一个来自公开的 ComfyUI-RMBG 节点包。

**这是可选的辅助步骤。** 用户没要求去背景时不要替换他的原图；下游流程要求 RGB 时，先按明确底色合成，不要直接把 alpha 丢掉。

## 输入与输出

| 占位符 | 说明 |
|---|---|
| `input_image` | 已上传到实例输入目录的源图文件名；**不要传绝对路径** |
| `alpha_prefix` | 透明图输出路径前缀，例如 `character-cutout/alpha` |
| `mask_prefix` | 蒙版输出路径前缀，例如 `character-cutout/mask` |

节点 3 保存 alpha 通道图（RGBA），节点 4 保存蒙版。

## 固定参数

`model=RMBG-2.0`、`sensitivity=1.0`、`process_res=1024`、`mask_blur=0`、`mask_offset=0`、`invert_output=false`、`refine_foreground=false`、`background=Alpha`、`background_color=#FFFFFF`。

这些值是既有预览环境用过的组合。想让边缘更紧或更松，调 `sensitivity`，一次只改一个参数，然后肉眼比对输出，别只看蒙版的直方图。

## 依赖

- 节点包 ComfyUI-RMBG，revision `bd509b47`，GPL-3.0
- 模型 `1038lab/RMBG-2.0`，revision `1cd47876`，四个文件（权重约 844 MB）

细节与哈希见 [dependencies.lock.json](dependencies.lock.json)，接口与恢复路径见 [interface.json](interface.json)。

## 两处容易踩的地方

- **返回槽位**：蒙版取的是 `SaveImage` 的 slot 2。不同版本的节点包返回顺序可能不同，升级之后按目标实例的 `/object_info` 重新核对，不要假设 slot 2 还是蒙版。
- **许可**：节点是 GPL-3.0，模型许可是另一回事——官方模型卡标注 CC BY-NC 4.0，商用需要与 BRIA 另行约定。公开镜像能下载不等于拿到授权。

## 自检

```bash
python3 -m unittest discover -s workflows/images/rmbg-2-alpha/tests -v
```

覆盖占位符契约、接口与图的一致性、依赖锁字段和隐私扫描。**这不是 GPU 运行测试**：本仓库没有在干净环境跑过这张图。
