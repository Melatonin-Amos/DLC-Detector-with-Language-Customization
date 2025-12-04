# DLC-Detector-with-Language-Customization

<p align="center">
  <img src="doc_asset/image/DLCupd.png" alt="DLC全栈技术流程图" width="800"/>
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> •
  <a href="#功能特性">功能特性</a> •
  <a href="#项目结构">项目结构</a> •
  <a href="#配置说明">配置说明</a> •
  <a href="#开发指南">开发指南</a> •
  <a href="#许可证">许可证</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python"/>
  <img src="https://img.shields.io/badge/PyTorch-1.12+-orange.svg" alt="PyTorch"/>
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"/>
</p>

---

<div align="center">
  
#### _“用智能手段，为银龄生命加上DLC。”_

</div>


这是上海交通大学电子信息与电气工程学部的一群大一学生在 [工程学导论（ME1221）](https://oc.sjtu.edu.cn/courses/84663) 课程中开发的项目。本项目实现了一个**基于 VLM 的支持语义定制的智能养老摄像头系统**，利用大规模预训练视觉语言模型进行 zero-shot 场景识别，实现高度个性化的智能监护功能。

## 功能特性

- 🎯 **Zero-shot 场景检测**：无需训练即可识别跌倒、火灾等紧急场景
- 🌐 **中英双语支持**：支持中文 Prompt 配置，界面中文显示
- ⚡ **双模型支持**：支持 [CLIP](https://arxiv.org/abs/2103.00020) 和 [FG-CLIP 2](https://360cvgroup.github.io/FG-CLIP/)
- 🔧 **灵活配置**：基于 Hydra 的配置系统，支持场景自定义
- 🖥️ **GUI 界面**：Tkinter 图形界面，实时预览与配置
- 📹 **多输入源**：支持摄像头实时流和本地视频文件

<p align="center">
  <img src="doc_asset/image/framework.png" alt="FG-CLIP2 架构图" width="700"/>
  <br/>
  <em>FG-CLIP 2 模型架构（推荐在算力充足时使用）</em>
</p>

## 快速开始

### 环境要求

- Python 3.10+
- CUDA 11.0+（推荐，CPU 模式较慢）
- 4GB+ 显存（FG-CLIP 2）

### 安装

```bash
# 克隆仓库
git clone https://github.com/Melatonin-Amos/DLC-Detector-with-Language-Customization.git
cd DLC-Detector-with-Language-Customization

# 创建 conda 环境（推荐）
conda create -n dlc python=3.10 -y
conda activate dlc

# 安装依赖
pip install -r requirements.txt

# Linux 用户安装中文字体（GUI 显示需要）
# Ubuntu/Debian:
sudo apt-get install -y fonts-noto-cjk fonts-wqy-zenhei && fc-cache -fv

# CentOS/Fedora:
sudo dnf install -y google-noto-sans-cjk-fonts && fc-cache -fv

# Arch:
sudo pacman -S noto-fonts-cjk && fc-cache -fv
```

> 💡 **提示**：Windows 和 macOS 自带中文字体，无需安装。字体配置可在 `config/gui_fonts.yaml` 中修改。

### 运行

```bash
# 使用 FG-CLIP 2 模型，首次运行会下载模型文件（约1.6GB），后续运行即可直接开始检测
python main.py --config-name=config_fgclip mode=camera camera.index=0

# 使用视频文件测试
python main.py --config-name=config_fgclip mode=video video_path=assets/test_videos/fire_detection/fire3.mp4

# 启用 AI 场景生成（可选，用于自定义场景）
export GEMINI_API_KEY="your_api_key"  # 推荐使用 Gemini
# 或 export DEEPSEEK_API_KEY="your_api_key"

# 对于Windows系统，可能需要使用不同的语法：
set GEMINI_API_KEY=your_api_key
# 或 set DEEPSEEK_API_KEY=your_api_key

python main.py --config-name=config_fgclip mode=camera
```

## 项目结构

```
DLC-Detector-with-Language-Customization/
├── main.py                       # 程序入口
├── requirements.txt              # 依赖列表
│
├── config/                       # Hydra 配置文件
│   ├── config.yaml               # CLIP 模型主配置
│   ├── config_fgclip.yaml        # FG-CLIP 2 模型主配置
│   ├── gui_fonts.yaml            # GUI 字体配置（跨平台）
│   ├── camera/                   # 摄像头配置
│   ├── model/                    # 模型参数配置
│   ├── detection/                # 检测场景配置
│   │   ├── default.yaml          # 默认场景（跌倒/火灾）
│   │   ├── elderly_care.yaml     # 养老场景扩展
│   │   └── minimal.yaml          # 精简场景
│   └── alert/                    # 警报配置
│
├── src/                          # 核心源码
│   ├── core/                     # 核心模块
│   │   ├── clip_detector.py      # 场景检测器
│   │   ├── video_stream.py       # 视频流处理
│   │   └── alert_manager.py      # 警报管理
│   ├── models/                   # 模型封装
│   │   ├── clip_wrapper.py       # CLIP 模型封装
│   │   └── fgclip_wrapper.py     # FG-CLIP 2 封装
│   └── utils/                    # 工具模块
│       ├── translator.py         # 中文翻译器
│       ├── config_loader.py      # 配置加载
│       ├── config_updater.py     # 配置更新器
│       ├── font_loader.py        # GUI 字体加载器
│       └── logger.py             # 日志工具
│
├── gui/                          # GUI 模块
│   ├── main_window.py            # 主窗口
│   └── settings_panel.py         # 设置面板
│
├── scripts/                      # 脚本工具
│   ├── download_models.py        # 模型下载脚本
│   └── run_demo.py               # 演示脚本
│
├── assets/                       # 资源文件
│   └── test_videos/              # 测试视频
│
└── docs/                         # 文档
    ├── FG_CLIP_GUIDE.md          # FG-CLIP 使用指南
    └── PROMPT_OPTIMIZATION.md    # Prompt 优化指南
```

## 配置说明

### 检测场景配置

在 `config/detection/` 下创建或修改 YAML 文件来自定义检测场景：

```yaml
# config/detection/default.yaml
scenarios:
  fall:                                         # 场景 ID（英文键名）
    enabled: true                               # 是否启用
    name: 跌倒检测                               # 显示名称
    prompt: a person has fallen and is lying on the floor  # 检测 Prompt
    prompt_cn: 有人摔倒躺在地上                  # 中文描述
    threshold: 0.375                            # 检测阈值（动态计算）
    cooldown: 30                                # 冷却时间（秒）
    consecutive_frames: 2                       # 连续帧要求
    alert_level: high                           # 警报级别 (high/medium/low)
  
  fire:
    enabled: true
    name: 火灾检测
    prompt: flames and fire burning with visible smoke
    prompt_cn: 发生火灾，有火焰和浓烟
    threshold: 0.375
    cooldown: 60
    consecutive_frames: 3
    alert_level: high
  
  normal:                                       # 正常场景（内置保护，不可删除）
    enabled: true 
    name: 正常场景
    prompt: an ordinary indoor room with no emergency
    prompt_cn: 普通室内环境，无异常
    threshold: 0.99                             # 高阈值，避免误报
    cooldown: 10
    consecutive_frames: 1
    alert_level: low                            # 强制为 low，不触发警报
```

> 💡 **提示**：通过 GUI 设置面板可以可视化地启用/禁用场景，配置会自动增量更新。

### 切换检测配置

```bash
# 使用养老场景扩展配置
python main.py --config-name=config_fgclip detection=elderly_care mode=camera

# 使用精简配置
python main.py --config-name=config_fgclip detection=minimal mode=camera
```

### 邮件警报配置

当检测到 `alert_level: high` 的场景时，系统可自动发送邮件通知。在 `config/alert/default.yaml` 中配置：

```yaml
email:
  enabled: true                        # 启用邮件警报
  smtp_server: "smtp.qq.com"           # SMTP服务器
  smtp_port: 465                       # SSL端口
  sender_email: "your@qq.com"          # 发件邮箱
  sender_password: "授权码"             # 邮箱授权码（非登录密码）
  recipients: ["family@example.com"]   # 收件人列表
```

> 💡 **提示**：QQ邮箱需在设置中开启SMTP服务并获取授权码。邮件将附带警报帧截图。

### Prompt 优化建议

经测试，**英文描述性长句效果最佳**。详见 [Prompt 优化指南](docs/PROMPT_OPTIMIZATION.md)。

| 风格 | 示例 | 效果 |
|:---:|------|:---:|
| ✅ 推荐 | `a person has fallen and is lying on the floor` | 0.95 |
| ❌ 不推荐 | `person falling` | 0.57 |

### GUI 使用

1. **主界面**：左侧视频预览，右侧警报面板（实时显示检测结果）
2. **设置面板**：点击「设置」可进入场景配置
   - 勾选/取消勾选场景即可启用/禁用
   - 点击「新建场景」可用 AI 自动生成配置
   - 内置场景（跌倒、火灾、正常）不可删除

## 开发指南

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements.txt

# 代码格式化
black src/ gui/ tests/

# 代码检查
flake8 src/ gui/
```

### 添加新检测场景

1. 在 `config/detection/` 下创建新的 YAML 文件或修改现有文件
2. 按照上述格式添加场景配置
3. 运行测试验证效果：

```bash
python main.py --config-name=config_fgclip detection=your_config mode=video video_path=your_test.mp4
```

### 模型扩展

如需集成新的 VLM 模型，参考 `src/models/fgclip_wrapper.py` 实现以下接口：

```python
class YourModelWrapper:
    def __init__(self, model_name: str, device: str = None):
        # 初始化模型
        pass
    
    def predict(self, image: Image, prompts: List[str]) -> Tuple[Tensor, Tensor]:
        # 返回 (logits, probabilities)
        pass
```

### 代码规范

- 使用 [Black](https://github.com/psf/black) 格式化代码
- 遵循 [PEP 8](https://pep8.org/) 风格指南
- 函数和类需添加 docstring
- 提交前运行 `pytest` 确保测试通过

## 常见问题

<details>
<summary><b>Q: GUI 中文显示为方框？</b></summary>

Linux 用户需安装中文字体：
```bash
# Ubuntu/Debian
sudo apt-get install -y fonts-noto-cjk fonts-wqy-zenhei && fc-cache -fv
```

Windows/macOS 通常自带中文字体，无需安装。
</details>

<details>
<summary><b>Q: 如何自定义字体配置？</b></summary>

编辑 `config/gui_fonts.yaml` 文件：
```yaml
# 修改字体大小
font_styles:
  normal:
    size: 14  # 增大默认字体
    weight: "bold"

# 修改标题颜色
title_color: "#1a5276"  # 深蓝色
```

重启程序后生效。
</details>

<details>
<summary><b>Q: 摄像头无法打开？</b></summary>

尝试不同的摄像头索引：
```bash
python main.py mode=camera camera.index=0  # 或 1, 2
```
</details>

<details>
<summary><b>Q: 显存不足？</b></summary>

使用精简配置或降低分辨率：
```bash
python main.py --config-name=config_fgclip detection=minimal camera.width=640 camera.height=480
```
</details>

<details>
<summary><b>Q: 如何使用 AI 生成自定义场景？</b></summary>

1. 设置 API 密钥环境变量：
```bash
export GEMINI_API_KEY="your_key"  # 优先使用
# 或
export DEEPSEEK_API_KEY="your_key"
```
2. 在 GUI 设置面板点击「新建场景」
3. 输入场景名称（如"打架检测"），AI 将自动生成配置
</details>

<details>
<summary><b>Q: 检测效果不理想？</b></summary>

- 使用**英文描述性长句**作为 Prompt
- 调整 `threshold` 值（降低可提高召回率，升高可减少误报）
- 确保 `normal` 场景已启用，作为对比基准
</details>

## 贡献者

本项目由上海交通大学 2025 级本科生团队开发：

- 开发团队成员

欢迎提交 Issue 和 Pull Request！我们特别鼓励您进行下面的增量式更新并且提交PR：

  - 隐私保护：在边缘设备+服务器的计算情境，如何保持摄像头视觉信息可能携带的用户隐私的安全性？您可以尝试使用稀疏视觉输入。
  - 更加开盒即用：可以简化当前的运行逻辑，把更多自由度交给GUI
  - 跨终端GUI与应用：可以开发针对Linux、安卓、iOS的GUI和通讯、计算机制



## 许可证

本项目采用 [MIT License](LICENSE) 开源。

## 致谢

- [OpenAI CLIP](https://github.com/openai/CLIP)
- [FG-CLIP 2 (Qihoo 360)](https://github.com/360CVGroup/FG-CLIP)
- [Hydra](https://hydra.cc/)
- [Google Gemini API](https://ai.google.dev/)
- [DeepSeek API](https://www.deepseek.com/)


---

<div align="center">

## 💖 支持我们 / Support Us

**代码不仅运行在 CPU 上，也运行在我们的咖啡因和热情之上。**

如果您喜欢这个由 SJTU 大一新生构建的项目，<br>
请点击右上角的 <img src="https://img.shields.io/github/stars/Melatonin-Amos/DLC-Detector-with-Language-Customization?style=social" alt="star"/> 按钮支持我们！

每一个 Star ⭐️ 都能：
👉 让我们的头发少掉一根
👉 让我们的模型推理快 1ms (玄学)
👉 鼓励我们在开源的道路上走得更远

</div>

---
<p align="center">
  Made with ❤️ at Shanghai Jiao Tong University
</p>

---
