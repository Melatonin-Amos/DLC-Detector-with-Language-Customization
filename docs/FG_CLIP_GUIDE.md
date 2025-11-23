# FG-CLIP 2集成指南

## 概述

FG-CLIP 2是360CVGroup开发的中英双语视觉语言对齐模型，相比原CLIP模型有以下优势：
- **原生中文支持**：无需翻译器，直接使用中文提示词
- **更高精度**：对摔倒、火灾等场景的检测灵敏度更高
- **动态分辨率**：自动适配图像尺寸，优化patch处理
- **校准参数**：内置logit_scale和logit_bias，提升分类精度

## 快速开始

### 1. 安装依赖

```bash
# 安装transformers库（FG-CLIP 2需要）
pip install transformers torch pillow
```

### 2. 使用FG-CLIP配置运行

```bash
# 使用FG-CLIP配置文件
python main.py --config-name=config_fgclip mode=camera

# 或者临时切换模型
python main.py mode=camera model=fgclip2
```

### 3. 使用原CLIP模型运行

```bash
# 使用默认配置（CLIP模型+翻译器）
python main.py mode=camera
```

## 配置说明

### FG-CLIP配置 (config/model/fgclip2.yaml)

```yaml
name: fgclip2-base-patch16  # 模型名称
type: fgclip                 # 模型类型标识
device: cuda                 # cuda或cpu

inference:
  temperature: 1.0           # softmax温度参数
  max_caption_length: 196    # 最大文本长度（支持长描述）
```

### 原CLIP配置 (config/model/vit_b_32.yaml)

```yaml
name: ViT-B/32              # OpenAI CLIP模型
type: clip                   # 模型类型标识
device: cuda

inference:
  temperature: 1.0
  max_caption_length: 77    # CLIP标准长度
```

## 性能对比

| 特性              | CLIP (ViT-B/32)     | FG-CLIP 2             |
|-------------------|---------------------|-----------------------|
| 中文支持          | ❌ 需要翻译器        | ✅ 原生支持           |
| 摔倒检测灵敏度    | 中等                | **高**                |
| 火灾检测灵敏度    | 中等                | **高**                |
| 推理速度          | 快                  | 中等                  |
| 显存占用          | ~2GB                | ~4GB                  |
| 文本长度限制      | 77 tokens           | 196 tokens            |

## 技术细节

### 模型架构

FG-CLIP 2使用更先进的视觉-语言对齐架构：
- **视觉编码器**：动态patch处理，根据图像尺寸自适应
- **文本编码器**：支持中英双语tokenization
- **相似度计算**：logit_scale和logit_bias校准

### 代码示例

```python
from src.models.fgclip_wrapper import FGCLIPWrapper
from PIL import Image

# 初始化模型
model = FGCLIPWrapper(
    model_name="fgclip2-base-patch16",
    device="cuda",
    max_caption_length=196
)

# 加载图像
image = Image.open("test.jpg")

# 中文提示词（无需翻译）
texts = [
    "一个老人正在摔倒",
    "房间里发生火灾",
    "正常的室内场景"
]

# 推理
logits, probs = model.predict(image, texts)
print(f"检测结果: {texts[probs.argmax()]}, 置信度: {probs.max():.4f}")
```

### 动态max_num_patches

FG-CLIP自动根据图像尺寸调整patch数量：

```python
# 1920x1080图像 -> (1920//16) * (1080//16) = 8100 patches
# 限制在1024以内 -> max_num_patches=1024

# 640x480图像 -> (640//16) * (480//16) = 1200 patches
# 限制在1024以内 -> max_num_patches=1024

# 320x240图像 -> (320//16) * (240//16) = 300 patches
# 限制在128以上 -> max_num_patches=300
```

## 故障排查

### 问题1: transformers模块未找到

```bash
pip install transformers torch
```

### 问题2: 模型下载失败

FG-CLIP会自动从Hugging Face下载模型，首次运行需要网络连接：

```python
# 设置镜像（可选）
export HF_ENDPOINT=https://hf-mirror.com
```

### 问题3: 显存不足

降低batch size或使用CPU模式：

```bash
python main.py mode=camera model=fgclip2 model.device=cpu
```

### 问题4: 中文提示词仍被翻译

检查translation配置是否禁用：

```yaml
translation:
  enabled: false  # 确保关闭翻译器
```

## 切换模型

### 临时切换到FG-CLIP

```bash
python main.py mode=camera model=fgclip2
```

### 临时切换到CLIP

```bash
python main.py mode=camera model=vit_b_32
```

### 永久切换

修改 `config/config.yaml`:

```yaml
defaults:
  - model: fgclip2  # 或 vit_b_32
```

## 高级用法

### 自定义FG-CLIP配置

创建 `config/model/fgclip_custom.yaml`:

```yaml
name: fgclip2-large-patch14  # 使用更大的模型
type: fgclip
device: cuda

inference:
  temperature: 0.8            # 调整温度参数
  max_caption_length: 256     # 更长的文本支持
```

使用自定义配置：

```bash
python main.py mode=camera model=fgclip_custom
```

## 性能优化建议

1. **GPU模式**：优先使用CUDA加速
2. **帧率控制**：调整camera.fps_limit避免过载
3. **提取间隔**：设置camera.extract_interval每N帧检测一次
4. **批处理**：FG-CLIP支持文本批处理，已优化

## 参考资料

- [FG-CLIP GitHub](https://github.com/360CVGroup/FG-CLIP)
- [Transformers文档](https://huggingface.co/docs/transformers)
- [项目README](../README.md)
