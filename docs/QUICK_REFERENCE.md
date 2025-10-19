# DLC项目快速参考手册

## 常用命令

### Git操作
```bash
# 创建个人开发分支
git checkout -b [姓名拼音]_dev

# 查看当前分支
git branch

# 从main分支同步更新
git checkout main
git pull origin main
git checkout [姓名拼音]_dev
git merge main

# 提交代码
git add .
git commit -m "feat(module): description"
git push origin [姓名拼音]_dev

# 创建Pull Request
在GitHub网页上操作
```

### Python环境
```bash
# 创建虚拟环境
python -m venv venv
# 或者，我更建议用conda管理
conda create -n dlc python=3.10


# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
# 或者，我更建议用conda管理
conda activate dlc


# 安装依赖
pip install -r requirements.txt

# 退出虚拟环境
deactivate
```

### 项目运行
```bash
# 下载CLIP模型
python scripts/download_models.py

# 测试相机连接
python scripts/test_camera.py --source rtsp
python scripts/test_camera.py --source video --path assets/test_videos/test1.mp4

# 运行主程序
python main.py --source rtsp
python main.py --source video --path assets/test_videos/fall_detection/test1.mp4

# 运行测试
pytest tests/
```

## 文件路径速查

### 需要修改的配置文件
- `config/camera_config.yaml` - 相机参数
- `config/model_config.yaml` - CLIP模型配置
- `config/detection_config.yaml` - 检测场景和阈值

### 需要开发的核心文件
- `src/core/video_capture.py` - 视频捕获
- `src/models/clip_wrapper.py` - CLIP封装
- `src/core/clip_detector.py` - 检测器
- `src/core/alert_manager.py` - 警报管理
- `main.py` - 主程序

### 测试视频存放位置
- `assets/test_videos/fall_detection/` - 跌倒场景
- `assets/test_videos/fire_detection/` - 火灾场景
- `assets/test_videos/normal_scenarios/` - 正常场景

### 输出文件位置
- `data/logs/` - 日志文件
- `data/outputs/alerts/` - 警报图像
- `data/models/clip/` - CLIP模型权重

## 代码模板

### 导入常用库
```python
import cv2
import numpy as np
import torch
from PIL import Image
import yaml
import logging
```

### 读取配置文件
```python
import yaml

with open('config/detection_config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
```

### 基本日志设置
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### OpenCV读取视频
```python
import cv2

cap = cv2.VideoCapture("rtsp://...")  # RTSP流
# 或
cap = cv2.VideoCapture("video.mp4")   # 视频文件

while True:
    ret, frame = cap.read()
    if not ret:
        break
    # 处理帧
    cv2.imshow('Frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

## 开发任务检查清单

### 开始开发前
- [ ] 已完成Git/GitHub学习
- [ ] 已获得GitHub Copilot访问权限
- [ ] 已创建个人开发分支
- [ ] 已配置Python虚拟环境
- [ ] 已阅读DEVELOPMENT_GUIDE.md

### 开发过程中
- [ ] 代码遵循PEP 8规范
- [ ] 添加了必要的注释和docstring
- [ ] 编写了单元测试
- [ ] 在本地测试通过
- [ ] 及时提交代码（小步快跑）

### 提交代码前
- [ ] 从main分支同步最新代码
- [ ] 解决了合并冲突（如有）
- [ ] 所有测试通过
- [ ] 更新了相关文档
- [ ] 提交信息清晰明确

### Pull Request前
- [ ] 代码已推送到个人分支
- [ ] PR描述清楚（做了什么，为什么）
- [ ] 关联了相关的Issue（如有）
- [ ] 请求了代码审查

## 常见问题快速解决

### Q1: RTSP流无法连接
```bash
# 使用VLC测试RTSP地址
vlc rtsp://username:password@ip:port/path

# 检查OpenCV是否支持RTSP
python -c "import cv2; print(cv2.getBuildInformation())"
```

### Q2: CLIP模型下载失败
```bash
# 使用镜像源
export HF_ENDPOINT=https://hf-mirror.com

# 手动下载后放到指定目录
# data/models/clip/
```

### Q3: CUDA/GPU相关问题
```python
# 检查PyTorch是否支持CUDA
import torch
print(torch.cuda.is_available())
print(torch.version.cuda)

# 强制使用CPU（jyy：不是很建议，但凡有独显都建议用CUDA）
device = torch.device("cpu")
```

### Q4: 依赖包安装失败
```bash
# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 分步安装
pip install torch torchvision
pip install opencv-python
# ...
```

## 联系方式

- **项目负责人**: 金抑扬 (JYY)
- **GitHub仓库**: https://github.com/Melatonin-Amos/DLC-Detector-with-Language-Customization

---

**最后更新**: 2025年10月19日
