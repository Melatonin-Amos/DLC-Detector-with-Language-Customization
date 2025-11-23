# 模型切换快速指南

## 当前支持的模型

### 1. CLIP (OpenAI) - 默认模型
- **配置**: `config/model/vit_b_32.yaml`
- **类型**: `clip`
- **优势**: 速度快，资源占用低
- **劣势**: 需要翻译器，检测精度一般

### 2. FG-CLIP 2 (360CVGroup) - 推荐模型
- **配置**: `config/model/fgclip2.yaml`
- **类型**: `fgclip`
- **优势**: 中文原生支持，检测精度高
- **劣势**: 资源占用较高，需要transformers库

## 快速切换

### 方法1: 使用不同配置文件（永久切换）

**切换到FG-CLIP:**
```bash
# 编辑 config/config.yaml
defaults:
  - model: fgclip2  # 改这里

# 或者直接使用FG-CLIP配置
python main.py --config-name=config_fgclip mode=camera
```

**切换回CLIP:**
```bash
# 编辑 config/config.yaml
defaults:
  - model: vit_b_32  # 改这里

# 或者使用默认配置
python main.py mode=camera
```

### 方法2: 命令行参数（临时切换）

**切换到FG-CLIP:**
```bash
python main.py mode=camera model=fgclip2
```

**切换回CLIP:**
```bash
python main.py mode=camera model=vit_b_32
```

### 方法3: 创建自定义配置

**创建 `config/my_config.yaml`:**
```yaml
defaults:
  - camera: default
  - detection: default
  - model: fgclip2  # 你想用的模型
  - alert: default
  - _self_

mode: camera

# 其他自定义配置...
```

**使用自定义配置:**
```bash
python main.py --config-name=my_config
```

## 配置对比

| 配置项                  | CLIP (vit_b_32)    | FG-CLIP 2 (fgclip2)    |
|-------------------------|--------------------|------------------------|
| `model.type`            | `clip`             | `fgclip`               |
| `model.name`            | `ViT-B/32`         | `fgclip2-base-patch16` |
| `model.device`          | `cuda`             | `cuda`                 |
| `max_caption_length`    | 77                 | 196                    |
| `translation.enabled`   | `true`             | `false`                |
| 需要API Key             | ✅ 是               | ❌ 否                   |

## 翻译器配置

### 使用CLIP时（需要翻译器）

```yaml
# config/config.yaml
translation:
  enabled: true
  api_key: ${oc.env:GEMINI_API_KEY}  # 从环境变量读取
  model: gemini-2.5-flash
  cache_enabled: true
```

**设置环境变量:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### 使用FG-CLIP时（无需翻译器）

```yaml
# config/config_fgclip.yaml
translation:
  enabled: false  # FG-CLIP支持中文，不需要翻译
```

## 检测场景配置

两种模型共享相同的场景配置 (`config/detection/default.yaml`):

```yaml
scenarios:
  fall_detection:
    name: "摔倒检测"
    prompt_cn: "一个老人正在摔倒"  # CLIP会翻译成英文，FG-CLIP直接使用
    enabled: true
    threshold: 0.30
    
  fire_detection:
    name: "火灾检测"
    prompt_cn: "房间里发生火灾"
    enabled: true
    threshold: 0.35
    
  normal:
    name: "正常场景"
    prompt_cn: "正常的室内场景"
    enabled: true
    threshold: 0.25
```

## 性能调优建议

### CLIP优化

```yaml
# config/model/vit_b_32.yaml
inference:
  temperature: 1.0  # 降低可提高置信度差异

# config/camera/default.yaml
fps_limit: 15         # 提高帧率
extract_interval: 2   # 每2帧检测一次（降低可提高响应速度）
```

### FG-CLIP优化

```yaml
# config/model/fgclip2.yaml
inference:
  temperature: 1.0
  max_caption_length: 196  # 支持更详细的描述

# config/camera/default.yaml
fps_limit: 10         # FG-CLIP推理慢，降低帧率
extract_interval: 3   # 每3帧检测一次（减少计算量）
```

## 常见问题

### Q: 如何知道当前使用的是哪个模型？

**A:** 查看日志输出：
```
INFO - 创建FG-CLIP 2模型: fgclip2-base-patch16
```
或
```
INFO - 创建CLIP模型: ViT-B/32
```

### Q: FG-CLIP显存不够怎么办？

**A:** 切换到CPU模式：
```bash
python main.py mode=camera model=fgclip2 model.device=cpu
```

### Q: CLIP翻译器一直失败怎么办？

**A:** 切换到FG-CLIP（无需翻译器）：
```bash
python main.py --config-name=config_fgclip mode=camera
```

### Q: 如何测试两个模型的性能对比？

**A:** 运行测试脚本：
```bash
python tests/test_fgclip_integration.py
```

## 推荐使用场景

### 使用CLIP的场景
- ✅ 计算资源有限（CPU/低端GPU）
- ✅ 需要最快的推理速度
- ✅ 已有Gemini API Key
- ✅ 场景描述简单

### 使用FG-CLIP的场景  
- ✅ 检测精度要求高（摔倒检测）
- ✅ 有GPU且显存充足（≥4GB）
- ✅ 无API Key或离线使用
- ✅ 场景描述复杂/长文本
- ✅ 直接使用中文提示词

## 示例命令汇总

```bash
# 基础使用
python main.py mode=camera                                    # CLIP + 翻译器
python main.py --config-name=config_fgclip mode=camera       # FG-CLIP（推荐）

# 临时切换
python main.py mode=camera model=fgclip2                     # 临时用FG-CLIP
python main.py mode=camera model=vit_b_32                    # 临时用CLIP

# 自定义设置
python main.py mode=camera model=fgclip2 model.device=cpu    # FG-CLIP CPU模式
python main.py mode=camera camera.fps_limit=20               # 提高帧率

# 视频模式
python main.py mode=video video_path=test.mp4 model=fgclip2  # FG-CLIP视频检测

# 测试和演示
python examples/fgclip_simple_demo.py                        # FG-CLIP演示
python tests/test_fgclip_integration.py                      # 完整测试
```

## 更多信息

- [FG-CLIP详细指南](FG_CLIP_GUIDE.md)
- [配置文件说明](../config/README.md)
- [检测场景配置](../config/detection/default.yaml)
