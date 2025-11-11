# 用户输入接口使用指南

## 快速索引

📖 **想要做什么？**

| 需求 | 使用方法 | 文档链接 |
|------|---------|---------|
| 🔍 获取用户选择的场景类型 | `panel.get_current_scene_type()` | [→](#获取场景类型) |
| ⚙️ 获取完整配置 | `panel.get_scene_config()` | [→](#获取完整配置) |
| 💡 根据光照调整检测 | `panel.get_light_condition()` | [→](#获取光照条件) |
| 🔔 获取报警设置 | `panel.get_alert_settings()` | [→](#获取报警设置) |
| 🎬 动态切换场景 | `panel.set_scene_type(name)` | [→](#切换场景) |
| ➕ 添加自定义场景 | `panel.add_scene_type(name)` | [→](#添加场景) |
| 📝 批量修改配置 | `panel.update_scene_config(dict)` | [→](#批量更新) |

---

## TL;DR（太长不看版）

### 3行代码获取用户输入

```python
from gui.settings_panel import SettingsPanel

panel = SettingsPanel(root)
config = panel.get_scene_config()  # 获取所有用户配置
```

### 配置数据结构

```python
{
    "scene_type": "摔倒",           # 用户选择的场景
    "light_condition": "normal",    # bright/normal/dim
    "enable_roi": False,            # 是否启用ROI
    "enable_sound": True,           # 声音报警
    "enable_email": False,          # 邮件通知
    "auto_record": False,           # 自动录像
}
```

---

## 核心概念

### 1. 配置共享机制

`SettingsPanel` 通过 **引用传递** 的 `app_config` 字典与主窗口通信：

```python
# 主窗口创建共享配置
app_config = {
    "scene": {...},
    "scene_types": [...]
}

# 传给设置面板（引用传递）
panel = SettingsPanel(root, app_config=app_config)

# 用户在GUI中修改 → app_config 自动更新
# 检测模块读取 app_config → 获得最新配置
```

**优点:**
- ✅ 无需手动同步
- ✅ 实时获取用户输入
- ✅ 支持热更新（无需重启）

---

### 2. 公开接口 vs 内部实现

**✅ 推荐：使用公开接口**
```python
config = panel.get_scene_config()  # 封装良好
scene = config["scene_type"]
```

**❌ 不推荐：直接访问内部变量**
```python
scene = panel.scene_type_var.get()  # 绕过封装
```

---

## 核心接口详解

### 获取场景类型

```python
# 获取当前场景
scene = panel.get_current_scene_type()
# 返回: "摔倒" | "起火" | "闯入" | ...

# 获取所有可用场景
all_scenes = panel.get_all_scene_types()
# 返回: ["摔倒", "起火", "闯入", ...]
```

**使用场景:**
- 根据场景类型选择不同的检测提示词
- 加载场景专用的检测模型
- 调整检测算法参数

**示例:**
```python
prompts_map = {
    "摔倒": ["person falling", "person on ground"],
    "起火": ["fire", "flames", "smoke"],
    "闯入": ["person entering", "unauthorized person"]
}

scene = panel.get_current_scene_type()
prompts = prompts_map.get(scene, [])
```

---

### 获取完整配置

```python
config = panel.get_scene_config()
```

**返回值结构:**
```python
{
    "scene_type": str,         # 场景类型
    "light_condition": str,    # 光照条件
    "enable_roi": bool,        # ROI开关
    "enable_sound": bool,      # 声音报警
    "enable_email": bool,      # 邮件通知
    "auto_record": bool,       # 自动录像
}
```

**使用场景:**
- 一次性获取所有配置
- 传递给检测模块
- 保存配置到文件

**示例:**
```python
config = panel.get_scene_config()

# 使用配置进行检测
result = detector.detect(
    frame,
    scene=config["scene_type"],
    threshold=get_threshold(config["light_condition"]),
    roi_enabled=config["enable_roi"]
)

# 处理检测结果
if result.detected:
    if config["enable_sound"]:
        play_sound()
    if config["auto_record"]:
        start_recording()
```

---

### 获取光照条件

```python
light = panel.get_light_condition()
# 返回: "bright" | "normal" | "dim"
```

**使用场景:**
- 调整检测阈值
- 图像预处理（亮度调整）
- 自适应算法参数

**示例:**
```python
light = panel.get_light_condition()

# 根据光照调整检测阈值
threshold_map = {
    "bright": 0.30,  # 明亮环境，提高阈值
    "normal": 0.25,  # 正常环境
    "dim": 0.20      # 昏暗环境，降低阈值
}
threshold = threshold_map[light]

# 或调整图像亮度
if light == "dim":
    frame = cv2.convertScaleAbs(frame, alpha=1.5, beta=30)
```

---

### 获取报警设置

```python
alerts = panel.get_alert_settings()
```

**返回值:**
```python
{
    "sound": bool,   # 声音报警
    "email": bool,   # 邮件通知
    "record": bool,  # 自动录像
}
```

**使用场景:**
- 检测到事件后触发相应的报警方式

**示例:**
```python
if detection_result.positive:
    alerts = panel.get_alert_settings()
    
    if alerts["sound"]:
        play_alert_sound()
    
    if alerts["email"]:
        send_notification_email(
            to="admin@example.com",
            subject=f"检测到{scene_type}事件",
            body=f"时间: {datetime.now()}\n位置: 摄像头1"
        )
    
    if alerts["record"]:
        recorder.start(duration=60)  # 录制60秒
```

---

### 切换场景

```python
success = panel.set_scene_type("起火")
if success:
    print("场景切换成功")
else:
    print("场景不存在")
```

**使用场景:**
- 通过代码动态切换检测场景
- 定时任务（如夜间切换到夜视模式）
- 外部触发（如接收到远程指令）

**示例:**
```python
import datetime

# 根据时间自动切换场景
hour = datetime.datetime.now().hour

if 22 <= hour or hour < 6:
    # 夜间模式
    panel.set_scene_type("闯入")
    panel.update_scene_config({"light_condition": "dim"})
else:
    # 日间模式
    panel.set_scene_type("摔倒")
    panel.update_scene_config({"light_condition": "normal"})
```

---

### 添加场景

```python
success = panel.add_scene_type("打架")
if success:
    print("场景添加成功")
    panel.set_scene_type("打架")  # 切换到新场景
```

**使用场景:**
- 动态扩展检测场景
- 用户自定义场景
- 插件系统

**示例:**
```python
# 批量添加自定义场景
custom_scenes = ["打架", "人员聚集", "车辆违停", "垃圾堆放"]

for scene in custom_scenes:
    if panel.add_scene_type(scene):
        print(f"✓ 已添加: {scene}")
    else:
        print(f"✗ 添加失败: {scene}")

# 查看所有场景
print(panel.get_all_scene_types())
```

---

### 批量更新

```python
panel.update_scene_config({
    "scene_type": "起火",
    "light_condition": "bright",
    "enable_sound": True,
    "enable_email": True,
    "auto_record": True
})
```

**使用场景:**
- 加载配置文件
- 恢复默认设置
- 快速切换预设

**示例:**
```python
import json

# 从文件加载配置
with open("config.json", "r") as f:
    saved_config = json.load(f)

# 批量应用配置
panel.update_scene_config(saved_config["scene"])

# 或定义预设配置
PRESETS = {
    "高灵敏度": {
        "light_condition": "dim",
        "enable_sound": True,
        "enable_email": True,
        "auto_record": True
    },
    "低功耗": {
        "light_condition": "bright",
        "enable_sound": False,
        "enable_email": False,
        "auto_record": False
    }
}

# 应用预设
panel.update_scene_config(PRESETS["高灵敏度"])
```

---

## 完整集成示例

### 示例1: 与检测循环集成

```python
class VideoDetector:
    def __init__(self, settings_panel):
        self.panel = settings_panel
        self.is_running = False
    
    def start(self):
        """开始检测"""
        self.is_running = True
        
        while self.is_running:
            # 读取视频帧
            frame = self.capture_frame()
            
            # 获取最新配置（支持用户动态修改）
            config = self.panel.get_scene_config()
            
            # 执行检测
            result = self.detect(frame, config)
            
            # 处理结果
            if result.detected:
                self.handle_detection(result, config)
    
    def detect(self, frame, config):
        """执行检测"""
        # 根据场景选择提示词
        scene = config["scene_type"]
        prompts = self.get_prompts(scene)
        
        # 根据光照调整阈值
        threshold = self.get_threshold(config["light_condition"])
        
        # 调用CLIP检测
        return self.clip_detector.detect(frame, prompts, threshold)
    
    def handle_detection(self, result, config):
        """处理检测结果"""
        alerts = self.panel.get_alert_settings()
        
        if alerts["sound"]:
            self.play_sound()
        
        if alerts["email"]:
            self.send_email(result)
        
        if alerts["record"]:
            self.start_recording()
```

---

### 示例2: 配置持久化

```python
import json

class ConfigManager:
    def __init__(self, settings_panel):
        self.panel = settings_panel
        self.config_file = "user_settings.json"
    
    def save(self):
        """保存配置到文件"""
        config = {
            "scene": self.panel.get_scene_config(),
            "scene_types": self.panel.get_all_scene_types()
        }
        
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("✓ 配置已保存")
    
    def load(self):
        """从文件加载配置"""
        try:
            with open(self.config_file, "r") as f:
                config = json.load(f)
            
            # 恢复场景类型
            for scene in config["scene_types"]:
                self.panel.add_scene_type(scene)
            
            # 恢复场景配置
            self.panel.update_scene_config(config["scene"])
            
            print("✓ 配置已加载")
        except FileNotFoundError:
            print("配置文件不存在，使用默认配置")
```

---

## 运行示例代码

### 简化版（无需GUI）

```bash
python examples/settings_api_simple_demo.py
```

输出示例：
```
✓ 获取完整场景配置:
  scene_type: 摔倒
  light_condition: normal
  enable_roi: False
  enable_sound: True
  ...

⚠️  检测到事件: 摔倒
   → 🔊 播放声音报警
   → 📹 开始自动录像
```

### 完整版（需要GUI）

```bash
python examples/settings_panel_api_demo.py
```

---

## 常见问题

### Q1: 如何实时获取用户修改的配置？

**A:** 在检测循环中每次都读取配置：

```python
while True:
    # 每次都读取最新配置
    config = panel.get_scene_config()
    
    # 使用最新配置
    result = detect(frame, config)
```

---

### Q2: 配置修改后需要手动保存吗？

**A:** 不需要。配置通过引用传递自动同步：

```python
# 主窗口
app_config = {...}
panel = SettingsPanel(root, app_config=app_config)

# 用户在GUI修改 → app_config 自动更新
# 无需手动保存
```

如果需要持久化到文件，使用 `ConfigManager`。

---

### Q3: 可以在不创建GUI的情况下使用吗？

**A:** 可以，直接操作 `app_config` 字典：

```python
app_config = {
    "scene": {"scene_type": "摔倒", ...},
    "scene_types": ["摔倒", "起火"]
}

# 直接读取
scene = app_config["scene"]["scene_type"]

# 直接修改
app_config["scene"]["scene_type"] = "起火"
```

---

### Q4: 如何添加新的配置项？

**A:** 在 `app_config` 中添加新字段，并在 `SettingsPanel` 中添加对应的接口：

```python
# 1. 在 app_config 添加新字段
app_config["scene"]["detection_interval"] = 1.0

# 2. 在 SettingsPanel 添加 getter
def get_detection_interval(self) -> float:
    return self.app_config["scene"]["detection_interval"]
```

---

## 相关文档

- 📖 [完整API参考](SETTINGS_PANEL_API.md) - 详细的接口文档
- 💻 [简化示例](../examples/settings_api_simple_demo.py) - 无GUI示例
- 🖥️ [完整示例](../examples/settings_panel_api_demo.py) - GUI示例
- 🎬 [主窗口集成](main_window.py) - 实际使用案例

---

## 快速参考表

| 接口方法 | 返回类型 | 用途 |
|---------|---------|------|
| `get_scene_config()` | `Dict` | 获取完整配置 ⭐ |
| `get_current_scene_type()` | `str` | 当前场景类型 |
| `get_all_scene_types()` | `list[str]` | 所有场景列表 |
| `get_light_condition()` | `str` | 光照条件 |
| `get_roi_settings()` | `Dict` | ROI设置 |
| `get_alert_settings()` | `Dict` | 报警设置 |
| `set_scene_type(name)` | `bool` | 切换场景 |
| `add_scene_type(name)` | `bool` | 添加场景 |
| `update_scene_config(dict)` | `None` | 批量更新 |

---

**作者:** LXR（李修然）  
**最后更新:** 2025年11月11日  
**版本:** v1.0
