# 示例代码目录

本目录包含DLC项目的使用示例。

## 文件说明

### clip_demo.py

CLIP功能演示脚本，展示：
- CLIPWrapper的基础使用（图像编码、文本编码、相似度计算）
- CLIPDetector的场景检测功能
- 图像预处理流程
- 完整的检测工作流程

**运行方法**：
```bash
python examples/clip_demo.py
```

**注意**：
- 需要先安装依赖：`pip install -r requirements.txt`
- 确保配置文件存在：`config/detection_config.yaml`
- 演示脚本不需要实际图像，仅展示API使用方法

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行演示

```bash
python examples/clip_demo.py
```

### 3. 实际使用示例

```python
from src.models import CLIPWrapper
from src.core import CLIPDetector
from src.utils import load_config
from PIL import Image

# 1. 加载配置
config = load_config('config/detection_config.yaml')

# 2. 创建检测器
detector = CLIPDetector(config=config)

# 3. 加载图像
image = Image.open('test_image.jpg')

# 4. 执行检测
import time
result = detector.detect(image, current_time=time.time())

# 5. 处理结果
if result['detected']:
    print(f"⚠️  检测到: {result['scenario_name']}")
    print(f"   置信度: {result['confidence']:.3f}")
    print(f"   警报级别: {result['alert_level']}")
```

## 核心组件说明

### CLIPWrapper

CLIP模型封装，提供：
- `encode_image()`: 图像编码（ViT视觉编码器）
- `encode_text()`: 文本编码（Transformer语义编码器）
- `compute_similarity()`: 余弦相似度计算
- `predict()`: 端到端预测

### CLIPDetector

场景检测器，提供：
- `detect()`: 检测图像中的场景
- `get_scenario_statistics()`: 获取场景统计信息
- `enable_scenario()`: 启用/禁用场景
- `update_threshold()`: 更新检测阈值

### 图像预处理

使用`preprocess_for_clip()`进行标准的CLIP图像预处理：
1. 转换为RGB格式
2. 调整大小（短边缩放到224）
3. 中心裁剪为224x224
4. 转换为张量
5. 归一化（使用CLIP标准参数）

## 配置说明

检测配置文件：`config/detection_config.yaml`

关键配置项：
- `scenarios`: 场景定义
  - `prompts`: 正样本文本提示词
  - `negative_prompts`: 负样本文本提示词（对比）
  - `threshold`: 检测阈值
  - `consecutive_frames`: 连续触发帧数
- `model.inference.temperature`: 温度参数

## 下一步

完成CLIP相关功能后，需要实现：
1. 视频捕获模块 (`src/core/video_capture.py`)
2. 警报管理器 (`src/core/alert_manager.py`)
3. 主程序 (`main.py`)
4. 测试脚本

详见：[DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md)
