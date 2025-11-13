# SettingsPanel 公开接口文档

## 概述

`SettingsPanel` 类提供了一套完整的公开接口，让协作者可以方便地获取和修改用户在GUI中配置的参数。这些接口支持：

- ✅ 读取用户输入的场景配置
- ✅ 以编程方式修改配置
- ✅ 添加自定义场景类型
- ✅ 与检测模块无缝集成

---

## 目录

1. [快速开始](#快速开始)
2. [读取配置接口](#读取配置接口)
3. [修改配置接口](#修改配置接口)
4. [场景管理接口](#场景管理接口)
5. [配置数据结构](#配置数据结构)
6. [集成示例](#集成示例)
7. [最佳实践](#最佳实践)

---

## 快速开始

### 基本用法

```python
from gui.settings_panel import SettingsPanel
import tkinter as tk

# 创建主窗口
root = tk.Tk()

# 创建设置面板
panel = SettingsPanel(root)

# 读取配置
config = panel.get_scene_config()
print(f"当前场景: {config['scene_type']}")
print(f"光照条件: {config['light_condition']}")

# 修改配置
panel.update_scene_config({
    "scene_type": "起火",
    "enable_sound": True
})
```

### 与主窗口共享配置

```python
# 在主窗口中
app_config = {
    "scene": {...},
    "scene_types": [...]
}

# 传入共享配置（引用传递）
panel = SettingsPanel(root, app_config=app_config)

# 设置面板的修改会自动同步到 app_config
```

---

## 读取配置接口

### 1. `get_scene_config()` ⭐ 推荐

获取当前场景的**完整配置**。

**方法签名:**
```python
def get_scene_config(self) -> Dict
```

**返回值:**
```python
{
    "scene_type": str,           # 场景类型（如"摔倒"、"起火"）
    "light_condition": str,      # 光照条件: 'bright' | 'normal' | 'dim'
    "enable_roi": bool,          # 是否启用ROI
    "enable_sound": bool,        # 是否启用声音报警
    "enable_email": bool,        # 是否启用邮件通知
    "auto_record": bool,         # 是否自动录像
}
```

**使用示例:**
```python
config = panel.get_scene_config()

# 直接使用配置
if config["scene_type"] == "摔倒":
    prompts = ["person falling down", "person on the ground"]
elif config["scene_type"] == "起火":
    prompts = ["fire", "smoke", "flames"]

# 根据光照调整阈值
thresholds = {
    "bright": 0.3,
    "normal": 0.25,
    "dim": 0.2
}
threshold = thresholds[config["light_condition"]]
```

---

### 2. `get_current_scene_type()`

获取当前选中的场景类型名称。

**方法签名:**
```python
def get_current_scene_type(self) -> str
```

**返回值:**
- `str`: 场景类型名称，如 `"摔倒"`, `"起火"`, `"闯入"` 等

**使用示例:**
```python
scene = panel.get_current_scene_type()
print(f"当前场景: {scene}")  # "摔倒"

# 根据场景加载不同的提示词
prompts_map = {
    "摔倒": ["person falling", "person lying on ground"],
    "起火": ["fire", "flames", "smoke"],
    "闯入": ["person entering", "unauthorized access"]
}
prompts = prompts_map.get(scene, [])
```

---

### 3. `get_all_scene_types()`

获取所有可用的场景类型列表（包括内置和自定义）。

**方法签名:**
```python
def get_all_scene_types(self) -> list[str]
```

**返回值:**
- `list[str]`: 场景类型列表副本（修改不会影响原列表）

**使用示例:**
```python
scenes = panel.get_all_scene_types()
print(scenes)  # ["摔倒", "起火", "闯入"]

# 遍历所有场景
for scene in scenes:
    print(f"场景: {scene}")
```

---

### 4. `get_light_condition()`

获取当前光照条件设置。

**方法签名:**
```python
def get_light_condition(self) -> str
```

**返回值:**
- `str`: 光照条件
  - `"bright"` - 明亮
  - `"normal"` - 正常
  - `"dim"` - 昏暗

**使用示例:**
```python
light = panel.get_light_condition()

# 根据光照调整图像预处理
if light == "dim":
    # 增强图像亮度
    enhanced_frame = cv2.convertScaleAbs(frame, alpha=1.5, beta=30)
elif light == "bright":
    # 降低曝光补偿
    enhanced_frame = cv2.convertScaleAbs(frame, alpha=0.8, beta=-10)
else:
    enhanced_frame = frame
```

---

### 5. `get_roi_settings()`

获取ROI（感兴趣区域）相关设置。

**方法签名:**
```python
def get_roi_settings(self) -> Dict
```

**返回值:**
```python
{
    "enabled": bool,     # 是否启用ROI
    "coordinates": None  # ROI坐标（待实现，目前为None）
}
```

**使用示例:**
```python
roi = panel.get_roi_settings()

if roi["enabled"]:
    # 只在ROI区域内检测
    if roi["coordinates"]:
        x, y, w, h = roi["coordinates"]
        roi_frame = frame[y:y+h, x:x+w]
        result = detector.detect(roi_frame)
    else:
        print("ROI已启用但未设置坐标")
else:
    # 全画面检测
    result = detector.detect(frame)
```

---

### 6. `get_alert_settings()`

获取报警相关设置。

**方法签名:**
```python
def get_alert_settings(self) -> Dict
```

**返回值:**
```python
{
    "sound": bool,    # 是否启用声音报警
    "email": bool,    # 是否启用邮件通知
    "record": bool,   # 是否自动录像
}
```

**使用示例:**
```python
alerts = panel.get_alert_settings()

# 检测到事件后触发报警
if detection_positive:
    if alerts["sound"]:
        play_alert_sound()
    
    if alerts["email"]:
        send_email_notification(
            subject=f"检测到{scene_type}",
            body="请及时查看监控画面"
        )
    
    if alerts["record"]:
        start_auto_recording(duration=60)  # 录制60秒
```

---

## 修改配置接口

### 1. `update_scene_config()` ⭐ 推荐

批量更新场景配置（部分更新）。

**方法签名:**
```python
def update_scene_config(self, config: Dict) -> None
```

**参数:**
- `config`: 配置字典，可以包含以下任意键（只需要提供要修改的项）：
  - `scene_type`: str
  - `light_condition`: str (`'bright'` | `'normal'` | `'dim'`)
  - `enable_roi`: bool
  - `enable_sound`: bool
  - `enable_email`: bool
  - `auto_record`: bool

**使用示例:**
```python
# 只更新部分配置
panel.update_scene_config({
    "scene_type": "起火",
    "enable_sound": True
})

# 批量更新多个配置
panel.update_scene_config({
    "light_condition": "bright",
    "enable_roi": False,
    "enable_email": True,
    "auto_record": True
})
```

---

### 2. `set_scene_type()`

以编程方式切换场景类型。

**方法签名:**
```python
def set_scene_type(self, scene_type: str) -> bool
```

**参数:**
- `scene_type`: 场景类型名称

**返回值:**
- `bool`: 成功返回 `True`，场景不存在返回 `False`

**使用示例:**
```python
# 切换场景
success = panel.set_scene_type("起火")
if success:
    print("场景切换成功")
    # 重新加载检测模型
    reload_model_for_scene("起火")
else:
    print("场景不存在")
```

---

## 场景管理接口

### 1. `add_scene_type()`

以编程方式添加新的场景类型。

**方法签名:**
```python
def add_scene_type(self, scene_name: str) -> bool
```

**参数:**
- `scene_name`: 新场景的名称

**返回值:**
- `bool`: 成功返回 `True`，场景已存在或名称为空返回 `False`

**使用示例:**
```python
# 添加新场景
success = panel.add_scene_type("闯入")
if success:
    print("场景添加成功")
    # 立即切换到新场景
    panel.set_scene_type("闯入")
else:
    print("场景已存在或名称无效")

# 批量添加场景
new_scenes = ["打架", "人员聚集", "车辆违停"]
for scene in new_scenes:
    panel.add_scene_type(scene)
```

---

## 配置数据结构

### 完整的 app_config 结构

```python
app_config = {
    # 场景配置
    "scene": {
        "scene_type": "摔倒",           # 当前场景类型
        "light_condition": "normal",    # 光照条件: bright/normal/dim
        "enable_roi": False,            # 是否启用ROI
        "enable_sound": True,           # 声音报警
        "enable_email": False,          # 邮件通知
        "auto_record": False,           # 自动录像
    },
    
    # 场景类型列表
    "scene_types": ["摔倒", "起火"],
}
```

### 访问方式

```python
# 方式1: 通过公开接口（推荐）
config = panel.get_scene_config()
scene_type = config["scene_type"]

# 方式2: 直接访问 app_config（不推荐，绕过了封装）
scene_type = panel.app_config["scene"]["scene_type"]
```

**⚠️ 注意:** 推荐使用公开接口而非直接访问 `app_config`，这样可以：
- 保持封装性
- 避免直接依赖内部数据结构
- 获得类型提示和文档支持

---

## 集成示例

### 示例1: 与检测器集成

```python
class CLIPDetector:
    def __init__(self, settings_panel: SettingsPanel):
        self.panel = settings_panel
        
    def detect_frame(self, frame):
        """检测视频帧"""
        # 获取配置
        config = self.panel.get_scene_config()
        
        # 根据场景类型选择提示词
        prompts = self._get_prompts_for_scene(config["scene_type"])
        
        # 根据光照调整阈值
        threshold = self._get_threshold_for_light(config["light_condition"])
        
        # 执行检测
        if config["enable_roi"]:
            roi_settings = self.panel.get_roi_settings()
            # 在ROI区域检测
            ...
        else:
            # 全画面检测
            results = self.detect(frame, prompts, threshold)
        
        # 触发报警
        if results:
            self._handle_alert(results)
        
        return results
    
    def _handle_alert(self, results):
        """处理检测结果并触发报警"""
        alerts = self.panel.get_alert_settings()
        
        if alerts["sound"]:
            self.play_sound()
        
        if alerts["email"]:
            self.send_email(results)
        
        if alerts["record"]:
            self.start_recording()
```

---

### 示例2: 动态场景切换

```python
class VideoProcessor:
    def __init__(self, settings_panel: SettingsPanel):
        self.panel = settings_panel
        self.current_scene = None
        
    def process_video(self):
        """处理视频流"""
        while True:
            frame = self.capture_frame()
            
            # 检查场景是否变化
            new_scene = self.panel.get_current_scene_type()
            if new_scene != self.current_scene:
                print(f"场景切换: {self.current_scene} → {new_scene}")
                self.reload_model(new_scene)
                self.current_scene = new_scene
            
            # 使用当前配置处理帧
            config = self.panel.get_scene_config()
            result = self.detect(frame, config)
            
            self.display(result)
```

---

### 示例3: 配置持久化

```python
import json

class ConfigManager:
    def __init__(self, settings_panel: SettingsPanel):
        self.panel = settings_panel
        self.config_file = "config.json"
    
    def save_to_file(self):
        """保存配置到文件"""
        config = {
            "scene": self.panel.get_scene_config(),
            "scene_types": self.panel.get_all_scene_types(),
        }
        
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("配置已保存")
    
    def load_from_file(self):
        """从文件加载配置"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # 恢复场景类型
            for scene in config["scene_types"]:
                self.panel.add_scene_type(scene)
            
            # 恢复场景配置
            self.panel.update_scene_config(config["scene"])
            
            print("配置已加载")
        except FileNotFoundError:
            print("配置文件不存在，使用默认配置")
```

---

## 最佳实践

### 1. ✅ 使用完整配置接口

**推荐:**
```python
config = panel.get_scene_config()
scene = config["scene_type"]
light = config["light_condition"]
```

**不推荐:**
```python
scene = panel.scene_type_var.get()  # 直接访问内部变量
light = panel.light_condition_var.get()
```

---

### 2. ✅ 批量更新配置

**推荐:**
```python
panel.update_scene_config({
    "scene_type": "起火",
    "enable_sound": True,
    "enable_email": True
})
```

**不推荐:**
```python
panel.scene_type_var.set("起火")
panel.enable_sound_var.set(True)
panel.enable_email_var.set(True)
```

---

### 3. ✅ 定期读取配置

在检测循环中定期读取配置，支持用户动态修改：

```python
def detection_loop():
    while True:
        # 每次都读取最新配置（支持热更新）
        config = panel.get_scene_config()
        
        # 使用最新配置进行检测
        result = detector.detect(frame, config)
```

---

### 4. ✅ 使用依赖注入模式

将 `SettingsPanel` 实例注入到需要配置的模块：

```python
class DetectionSystem:
    def __init__(self, settings_panel: SettingsPanel):
        self.panel = settings_panel  # 依赖注入
    
    def run(self):
        config = self.panel.get_scene_config()
        # ...

# 使用
panel = SettingsPanel(root)
system = DetectionSystem(panel)  # 注入
```

---

### 5. ✅ 配置变化监听

虽然目前没有内置的监听机制，但可以通过轮询实现：

```python
class ConfigWatcher:
    def __init__(self, settings_panel: SettingsPanel):
        self.panel = settings_panel
        self.last_config = None
    
    def check_changes(self):
        """检查配置是否变化"""
        current_config = self.panel.get_scene_config()
        
        if current_config != self.last_config:
            print("配置已变化:")
            for key in current_config:
                if current_config[key] != self.last_config.get(key):
                    print(f"  {key}: {self.last_config.get(key)} → {current_config[key]}")
            
            self.last_config = current_config
            return True
        
        return False
```

---

## 运行示例代码

```bash
# 运行完整示例集
cd /path/to/DLC-Detector-with-Language-Customization
python examples/settings_panel_api_demo.py
```

---

## 常见问题

### Q1: 如何获取用户输入的场景名称？

**A:** 使用 `get_current_scene_type()` 或 `get_all_scene_types()`

```python
# 获取当前场景
current = panel.get_current_scene_type()

# 获取所有场景（包括用户自定义的）
all_scenes = panel.get_all_scene_types()
```

---

### Q2: 配置修改后如何同步到主窗口？

**A:** 传入 `app_config` 时使用引用传递，修改会自动同步

```python
# 主窗口创建共享配置
app_config = {...}

# 传入设置面板（引用传递）
panel = SettingsPanel(root, app_config=app_config)

# 设置面板修改后，app_config 会自动更新
panel.update_scene_config({"scene_type": "起火"})
print(app_config["scene"]["scene_type"])  # "起火"
```

---

### Q3: 如何在检测过程中支持用户动态修改配置？

**A:** 在检测循环中每次都读取最新配置

```python
while True:
    # 每次迭代都读取最新配置
    config = panel.get_scene_config()
    
    # 使用最新配置
    result = detect(frame, config)
```

---

### Q4: 可以直接访问 `panel.app_config` 吗？

**A:** 技术上可以，但**不推荐**。应该使用公开接口：

```python
# ✅ 推荐
config = panel.get_scene_config()

# ❌ 不推荐（绕过封装）
config = panel.app_config["scene"]
```

---

## 配置监听接口 ✨ 新增

### 概述

配置监听功能允许你实时监控用户的配置变化，并在变化发生时自动执行相应操作。

### API 列表

| 方法 | 功能 |
|------|------|
| `start_config_monitor()` | 启动配置监听器 |
| `stop_config_monitor()` | 停止配置监听器 |
| `get_config_snapshot()` | 获取配置快照 |
| `print_current_config()` | 打印当前配置 |

### 使用示例

```python
from gui.main_window import MainWindow

gui = MainWindow()

# 定义回调函数
def on_config_change(old_config, new_config):
    if old_config["scene_type"] != new_config["scene_type"]:
        print(f"场景已切换: {new_config['scene_type']}")
        # 重新加载模型...

# 启动监听
gui.settings_panel.start_config_monitor(
    callback=on_config_change,
    interval=500,              # 每500ms检查一次
    print_changes=True,        # 自动打印变化
    print_full_config=True     # 打印完整配置
)

gui.run()
```

### 详细文档

完整的配置监听API文档请参阅：[配置监听接口文档](CONFIG_MONITOR_API.md)

---

## 完整 API 速查表

### 读取接口（7个）
| 方法 | 功能 |
|------|------|
| `get_scene_config()` | 获取完整场景配置 ⭐ |
| `get_current_scene_type()` | 获取当前场景类型 |
| `get_selected_scenes()` | 获取所有选中的场景 ✨ |
| `get_all_scene_types()` | 获取所有场景类型列表 |
| `get_light_condition()` | 获取光照条件 |
| `get_roi_settings()` | 获取ROI设置 |
| `get_alert_settings()` | 获取报警设置 |

### 写入接口（4个）
| 方法 | 功能 |
|------|------|
| `set_scene_type(name)` | 切换场景类型 |
| `set_selected_scenes(list)` | 设置多个选中场景 ✨ |
| `update_scene_config(dict)` | 批量更新配置 ⭐ |
| `add_scene_type(name)` | 添加新场景类型 |

### 配置监听接口（4个）✨ 新增
| 方法 | 功能 |
|------|------|
| `start_config_monitor()` | 启动配置监听器 |
| `stop_config_monitor()` | 停止配置监听器 |
| `get_config_snapshot()` | 获取配置快照 |
| `print_current_config()` | 打印当前配置 |

---

## 相关文档

- [配置监听接口文档](CONFIG_MONITOR_API.md) ✨ 新增
- [多场景选择指南](MULTI_SCENE_GUIDE.md)
- [用户输入接口文档](USER_INPUT_INTERFACE.md)
- [快速参考](QUICK_REFERENCE.md)

---

**文档版本:** v2.0  
**作者:** LXR（李修然）  
**最后更新:** 2025年11月12日
