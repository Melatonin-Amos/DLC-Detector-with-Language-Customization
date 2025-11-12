# SettingsPanel 接口速查卡

## 🎯 3秒快速上手

```python
from gui.settings_panel import SettingsPanel

panel = SettingsPanel(root)
config = panel.get_scene_config()  # 获取所有配置 ✅
```

---

## 📋 常用接口速查

### 获取配置

```python
# 获取完整配置（推荐）⭐
config = panel.get_scene_config()
# 返回: {"scene_type": "摔倒", "light_condition": "normal", ...}

# 获取当前场景
scene = panel.get_current_scene_type()
# 返回: "摔倒" | "起火" | "闯入" | ...

# 获取光照条件
light = panel.get_light_condition()
# 返回: "bright" | "normal" | "dim"

# 获取报警设置
alerts = panel.get_alert_settings()
# 返回: {"sound": True, "email": False, "record": True}

# 获取所有场景列表
scenes = panel.get_all_scene_types()
# 返回: ["摔倒", "起火", "闯入", ...]
```

---

### 修改配置

```python
# 切换场景
success = panel.set_scene_type("起火")  # 返回: True/False

# 添加新场景
success = panel.add_scene_type("打架")  # 返回: True/False

# 批量更新配置
panel.update_scene_config({
    "scene_type": "起火",
    "light_condition": "bright",
    "enable_sound": True
})
```

---

## 💡 常见使用场景

### 场景1: 根据场景选择提示词

```python
prompts_map = {
    "摔倒": ["person falling", "person on ground"],
    "起火": ["fire", "flames", "smoke"]
}

scene = panel.get_current_scene_type()
prompts = prompts_map[scene]
```

---

### 场景2: 根据光照调整阈值

```python
light = panel.get_light_condition()
threshold = {"bright": 0.3, "normal": 0.25, "dim": 0.2}[light]
```

---

### 场景3: 检测后触发报警

```python
if detected:
    alerts = panel.get_alert_settings()
    if alerts["sound"]:
        play_sound()
    if alerts["email"]:
        send_email()
    if alerts["record"]:
        start_recording()
```

---

### 场景4: 检测循环

```python
while True:
    frame = capture()
    config = panel.get_scene_config()  # 每次读取最新配置
    result = detect(frame, config)
```

---

## 📊 配置数据结构

```python
{
    "scene_type": "摔倒",           # 场景类型
    "light_condition": "normal",    # bright/normal/dim
    "enable_roi": False,            # ROI开关
    "enable_sound": True,           # 声音报警
    "enable_email": False,          # 邮件通知
    "auto_record": False,           # 自动录像
}
```

---

## 🔧 完整集成示例

```python
class VideoDetector:
    def __init__(self, settings_panel):
        self.panel = settings_panel
    
    def detect_frame(self, frame):
        # 1. 获取配置
        config = self.panel.get_scene_config()
        
        # 2. 选择提示词
        prompts = self.get_prompts(config["scene_type"])
        
        # 3. 调整阈值
        threshold = self.get_threshold(config["light_condition"])
        
        # 4. 执行检测
        result = self.clip_detect(frame, prompts, threshold)
        
        # 5. 处理报警
        if result.detected:
            alerts = self.panel.get_alert_settings()
            if alerts["sound"]: self.play_sound()
            if alerts["email"]: self.send_email()
            if alerts["record"]: self.start_recording()
        
        return result
```

---

## ⚡ 性能提示

✅ **可以在循环中频繁调用**
```python
while True:
    config = panel.get_scene_config()  # 开销极小
```

✅ **支持热更新（用户随时修改配置）**
```python
# 每次都读取最新配置，无需重启
config = panel.get_scene_config()
```

---

## 🚫 注意事项

### ❌ 不要直接访问内部变量

```python
# 错误 ❌
scene = panel.scene_type_var.get()

# 正确 ✅
scene = panel.get_current_scene_type()
```

### ❌ 不要缓存配置（除非有特殊原因）

```python
# 不推荐 ⚠️
config = panel.get_scene_config()
while True:
    detect(frame, config)  # 无法获取用户的新修改

# 推荐 ✅
while True:
    config = panel.get_scene_config()  # 每次读取最新
    detect(frame, config)
```

---

## 📖 深入阅读

| 需求 | 文档 |
|------|------|
| 快速上手 | [用户输入接口指南](USER_INPUT_INTERFACE.md) |
| 详细API | [API完整文档](SETTINGS_PANEL_API.md) |
| 架构理解 | [系统架构](ARCHITECTURE.md) |
| 所有文档 | [文档索引](README.md) |

---

## 🎯 API速查表

| 接口 | 返回 | 用途 |
|------|------|------|
| `get_scene_config()` ⭐ | `Dict` | 获取完整配置 |
| `get_current_scene_type()` | `str` | 当前场景 |
| `get_all_scene_types()` | `list` | 所有场景 |
| `get_light_condition()` | `str` | 光照条件 |
| `get_roi_settings()` | `Dict` | ROI设置 |
| `get_alert_settings()` | `Dict` | 报警设置 |
| `set_scene_type(name)` | `bool` | 切换场景 |
| `add_scene_type(name)` | `bool` | 添加场景 |
| `update_scene_config(dict)` | `None` | 批量更新 |

---

## 🚀 运行示例

```bash
# 无需GUI的简化示例（推荐）
python examples/settings_api_simple_demo.py

# 完整GUI示例
python gui/main_window.py
```

---

**打印此卡片，贴在显示器旁！** 📌

---

**版本:** v1.0  
**作者:** LXR  
**更新:** 2025-11-11
