# DLC 快速启动指南

## 环境准备

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. （可选）设置Gemini API密钥（用于中文翻译）
export GEMINI_API_KEY="your_api_key_here"
```

## 运行模式

### 1. 摄像头模式（带GUI）

```bash
python main.py mode=camera
```

**自定义摄像头索引：**
```bash
python main.py mode=camera camera.index=2
```

**自定义分辨率：**
```bash
python main.py mode=camera camera.width=1280 camera.height=720
```

### 2. 视频文件模式（带GUI）

```bash
python main.py mode=video video_path=assets/test_videos/fall_detection/test1.mp4
```

## 高级配置

### 调整检测阈值

```bash
# 降低跌倒检测阈值（更敏感）
python main.py mode=camera detection.scenarios.fall.threshold=0.2

# 增加连续触发帧数（减少误报）
python main.py mode=camera detection.scenarios.fall.consecutive_frames=5
```

### 禁用特定场景

```bash
# 只启用跌倒检测，禁用火灾检测
python main.py mode=camera detection.scenarios.fire.enabled=false
```

### 更换模型

```bash
# 使用更大的模型（精度更高但速度较慢）
python main.py mode=camera model=vit_l_14
```

### 禁用翻译功能

```bash
# 如果没有API密钥或想直接使用英文提示词
python main.py mode=camera translation.enabled=false
```

## 配置文件结构

```
config/
├── config.yaml              # 主配置
├── camera/
│   └── default.yaml        # 摄像头配置
├── detection/
│   └── default.yaml        # 检测场景配置（单个中文prompt）
├── model/
│   └── vit_b_32.yaml       # 模型配置
└── alert/
    └── default.yaml        # 警报配置
```

## 输出文件

检测结果会保存在以下位置：

- **警报日志**: `data/logs/alert.log`
- **警报帧图片**: `data/outputs/alerts/`
- **翻译缓存**: `data/.translation_cache.json`

## 常见问题

### 1. 摄像头无法打开

- 检查可用摄像头：`ls /dev/video*`
- 测试摄像头索引：修改 `camera.index=0` 或 `camera.index=2`
- 确保摄像头没有被其他程序占用

### 2. CLIP模型下载慢

- 首次运行会自动下载模型（约350MB）
- 可以使用国内镜像或手动下载

### 3. 翻译功能不可用

- 检查是否设置了`GEMINI_API_KEY`环境变量
- 或在配置中禁用翻译：`translation.enabled=false`

### 4. 中文字体显示异常（Linux）

```bash
# 安装中文字体
sudo apt-get install fonts-noto-cjk fonts-wqy-microhei
fc-cache -fv
```

## 调试模式

```bash
# 打印完整配置信息
python main.py mode=camera debug=true

# 查看更多日志
python main.py mode=camera alert.log.level=DEBUG
```
