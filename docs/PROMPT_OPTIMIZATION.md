# Prompt优化指南

## JYY的深夜发现

在对FG-CLIP 2模型进行测试后，我发现以下关键点：

### 1. 英文Prompt效果优于中文

尽管FG-CLIP 2声称支持中英双语，但实际测试表明：

| 场景 | 中文Prompt | 英文Prompt | 差异 |
|------|-----------|------------|------|
| 摔倒检测 | 0.02 | 0.86 | **巨大** |
| 火灾检测 | 0.84 | 0.54 | 中文略好 |
| 正常场景 | ~0.40 | ~0.40 | 相当 |

**结论**：对于某些场景（尤其是摔倒），英文prompt的效果显著优于中文。

### 2. Prompt风格对比

测试了4种英文prompt风格：

| 风格 | 示例 | 摔倒分数 | 评价 |
|------|------|---------|------|
| 风格1 | "a photo of someone falling down" | 0.733 | 良好 |
| 风格2 | "someone fell on the ground" | 0.109 | 差 |
| 风格3 | "person falling" | 0.567 | 一般 |
| 风格4 | "a person has fallen and is lying on the floor" | **0.953** | 最佳 |

**结论**：**描述性长句效果最好**（风格4），简短词组效果较差。

### 3. 推荐的Prompt格式

基于测试结果，推荐以下格式：

```yaml
fall:
  prompt: a person has fallen and is lying on the floor
  prompt_cn: 有人摔倒躺在地上  # 用于界面显示

fire:
  prompt: flames and fire burning with visible smoke
  prompt_cn: 发生火灾，有火焰和浓烟

normal:
  prompt: an ordinary indoor room with no emergency
  prompt_cn: 普通室内环境，无异常
```

### 4. 配置文件结构

```yaml
scenarios:
  <scenario_id>:
    enabled: true
    name: 中文场景名称（用于界面显示）
    prompt: 英文描述性prompt（用于检测）
    prompt_cn: 中文描述（备用/显示用）
    threshold: 0.35
    cooldown: 30
    consecutive_frames: 2
    alert_level: high/medium/low
```

### 5. 检测优先级

系统现在按以下优先级选择检测结果：

1. **alert_level**: high > medium > low
2. **置信度**: 相同优先级时，选择置信度更高的

这确保了紧急场景（fire/fall）不会被低优先级场景（normal）抢占。

## 配置文件说明

| 配置文件 | 场景数 | 用途 |
|----------|-------|------|
| `default.yaml` | 3 | 基础检测（摔倒/火灾/正常） |
| `minimal.yaml` | 4 | 精简版（摔倒/火灾/倒地不起/正常） |
| `elderly_care.yaml` | 12 | 完整养老场景 |

## 使用建议

1. **选择合适的配置**：资源有限时用`minimal.yaml`，完整功能用`elderly_care.yaml`
2. **调整阈值**：根据实际误报情况调整各场景的`threshold`
3. **调整连续帧**：高危场景设2-3帧，低优先级设1帧
4. **自定义场景**：参考英文prompt格式添加新场景

## 技术细节

- 模型：qihoo360/fg-clip2-base
- 推理方式：softmax归一化的相似度对比
- 温度参数：默认1.0（可在model_config.yaml调整）
