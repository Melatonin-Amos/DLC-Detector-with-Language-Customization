# SettingsPanel 用户输入接口架构

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户界面层                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              SettingsPanel GUI                            │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐         │   │
│  │  │ 场景  │  │ 光照  │  │  ROI  │  │ 报警  │         │   │
│  │  │ 选择  │  │ 条件  │  │  区域 │  │ 设置  │         │   │
│  │  └────────┘  └────────┘  └────────┘  └────────┘         │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ tkinter 变量绑定
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      内部状态层                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              tkinter 变量                                 │   │
│  │  • scene_type_var (StringVar)                            │   │
│  │  • light_condition_var (StringVar)                       │   │
│  │  • enable_roi_var (BooleanVar)                          │   │
│  │  • enable_sound_var (BooleanVar)                        │   │
│  │  • enable_email_var (BooleanVar)                        │   │
│  │  • auto_record_var (BooleanVar)                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 同步到
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      数据持久化层                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              app_config (Dict)                            │   │
│  │  {                                                        │   │
│  │    "scene": {                                             │   │
│  │      "scene_type": "摔倒",                                │   │
│  │      "light_condition": "normal",                         │   │
│  │      "enable_roi": False,                                 │   │
│  │      "enable_sound": True,                                │   │
│  │      "enable_email": False,                               │   │
│  │      "auto_record": False                                 │   │
│  │    },                                                      │   │
│  │    "scene_types": ["摔倒", "起火"]                        │   │
│  │  }                                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 引用传递（自动同步）
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      公开接口层                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              SettingsPanel 公开接口                        │   │
│  │                                                            │   │
│  │  读取接口:                                                 │   │
│  │  • get_scene_config() → Dict                              │   │
│  │  • get_current_scene_type() → str                         │   │
│  │  • get_all_scene_types() → list[str]                      │   │
│  │  • get_light_condition() → str                            │   │
│  │  • get_roi_settings() → Dict                              │   │
│  │  • get_alert_settings() → Dict                            │   │
│  │                                                            │   │
│  │  修改接口:                                                 │   │
│  │  • set_scene_type(name: str) → bool                       │   │
│  │  • add_scene_type(name: str) → bool                       │   │
│  │  • update_scene_config(dict: Dict) → None                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ 协作者调用
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      应用层                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              检测模块                                      │   │
│  │  class VideoDetector:                                     │   │
│  │    def __init__(self, panel: SettingsPanel):              │   │
│  │      self.panel = panel                                   │   │
│  │                                                            │   │
│  │    def detect(self, frame):                               │   │
│  │      config = self.panel.get_scene_config()              │   │
│  │      # 使用配置执行检测...                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 数据流向图

### 用户输入 → 检测系统

```
用户在GUI中选择场景
         ↓
GUI更新 tkinter 变量
         ↓
_save_scene_config() 触发
         ↓
更新 app_config["scene"]
         ↓
检测循环调用 get_scene_config()
         ↓
返回最新配置
         ↓
根据配置执行检测
```

### 配置同步机制

```
┌──────────────┐
│ MainWindow   │
│              │
│ app_config = {│  ←──────────────┐
│   "scene": {}│                  │
│ }            │                  │
└──────┬───────┘                  │
       │                          │
       │ 引用传递                 │ 自动同步
       ↓                          │
┌──────────────┐                  │
│ SettingsPanel│                  │
│              │                  │
│ self.app_config──────────────→  │
│              │  修改后自动反映   │
└──────────────┘                  │
                                  │
┌──────────────┐                  │
│ Detector     │                  │
│              │                  │
│ 读取 app_config ─────────────────┘
└──────────────┘
```

---

## 接口调用流程图

### 场景1: 获取用户配置

```
协作者调用
    │
    ├─→ panel.get_scene_config()
    │       │
    │       ├─→ 读取 app_config["scene"]
    │       │
    │       └─→ 返回配置字典
    │
    └─→ 获得用户输入的所有配置
```

### 场景2: 动态切换场景

```
协作者调用
    │
    ├─→ panel.set_scene_type("起火")
    │       │
    │       ├─→ 检查场景是否存在
    │       │       │
    │       │       ├─ 存在 → 更新 scene_type_var
    │       │       │           │
    │       │       │           └─→ 返回 True
    │       │       │
    │       │       └─ 不存在 → 返回 False
    │       │
    │       └─→ 触发GUI更新
    │
    └─→ 场景切换完成
```

### 场景3: 检测循环中获取配置

```
while True:
    │
    ├─→ frame = capture()
    │
    ├─→ config = panel.get_scene_config()  ← 每次都读取最新配置
    │       │
    │       └─→ 返回当前用户设置
    │
    ├─→ result = detect(frame, config)
    │       │
    │       └─→ 使用最新配置执行检测
    │
    └─→ 继续下一帧
```

---

## 模块依赖关系

```
┌─────────────────────────────────────────────┐
│           main_window.py                     │
│  • 创建 app_config                           │
│  • 创建 SettingsPanel(root, app_config)     │
│  • 读取 app_config 获取用户设置              │
└────────────────┬────────────────────────────┘
                 │
                 │ 依赖
                 ↓
┌─────────────────────────────────────────────┐
│         settings_panel.py                    │
│  • 提供GUI配置界面                           │
│  • 更新 app_config                           │
│  • 提供公开接口                              │
└────────────────┬────────────────────────────┘
                 │
                 │ 被使用
                 ↓
┌─────────────────────────────────────────────┐
│         detector.py (协作者模块)             │
│  • 注入 SettingsPanel 实例                   │
│  • 调用公开接口获取配置                       │
│  • 根据配置执行检测                          │
└─────────────────────────────────────────────┘
```

---

## 接口分类与用途

### 一次性配置获取

```python
config = panel.get_scene_config()  # 获取所有配置
```

**适用场景:**
- 初始化检测系统
- 保存配置到文件
- 一次性获取所有参数

---

### 定向配置获取

```python
scene = panel.get_current_scene_type()
light = panel.get_light_condition()
alerts = panel.get_alert_settings()
```

**适用场景:**
- 只需要特定配置项
- 性能敏感场景
- 代码可读性优先

---

### 配置修改

```python
# 单个修改
panel.set_scene_type("起火")

# 批量修改
panel.update_scene_config({
    "scene_type": "起火",
    "light_condition": "bright"
})
```

**适用场景:**
- 程序化切换场景
- 加载配置文件
- 预设配置应用

---

## 使用模式对比

### 模式1: 循环读取（推荐）

```python
while True:
    config = panel.get_scene_config()  # 每次都读取
    result = detect(frame, config)
```

**优点:**
- ✅ 支持热更新
- ✅ 始终使用最新配置

**缺点:**
- ⚠️ 每次都创建新字典（开销很小）

---

### 模式2: 缓存配置（不推荐）

```python
config = panel.get_scene_config()  # 只读取一次

while True:
    result = detect(frame, config)  # 使用缓存
```

**优点:**
- ✅ 性能略好（可忽略）

**缺点:**
- ❌ 无法获取用户的实时修改
- ❌ 需要手动刷新缓存

---

### 模式3: 监听变化（高级）

```python
last_config = None

while True:
    config = panel.get_scene_config()
    
    if config != last_config:
        # 配置变化，重新加载模型
        reload_model(config)
        last_config = config
    
    result = detect(frame, config)
```

**优点:**
- ✅ 支持配置变化时触发特殊操作
- ✅ 性能最优

**适用:**
- 需要在配置变化时重新加载模型
- 需要记录配置变化历史

---

## 设计原则

### 1. 封装原则

**❌ 不要直接访问内部实现:**
```python
scene = panel.scene_type_var.get()  # 直接访问tkinter变量
```

**✅ 使用公开接口:**
```python
scene = panel.get_current_scene_type()  # 通过接口访问
```

---

### 2. 单一职责原则

每个接口只做一件事：

```python
get_scene_config()      # 只负责返回配置
set_scene_type()        # 只负责设置场景
get_alert_settings()    # 只负责返回报警设置
```

---

### 3. 依赖注入原则

**✅ 推荐（依赖注入）:**
```python
class Detector:
    def __init__(self, panel: SettingsPanel):
        self.panel = panel  # 注入依赖
```

**❌ 不推荐（硬编码依赖）:**
```python
class Detector:
    def __init__(self):
        self.panel = SettingsPanel(...)  # 内部创建
```

---

### 4. 最小知识原则

协作者只需要知道接口，不需要了解内部实现：

```python
# 协作者只需要知道:
config = panel.get_scene_config()

# 不需要知道:
# - tkinter 变量如何存储
# - app_config 的结构
# - GUI 如何更新
```

---

## 性能考量

### 接口调用开销

| 接口 | 时间复杂度 | 空间复杂度 |
|------|-----------|-----------|
| `get_scene_config()` | O(1) | O(1) - 创建新字典 |
| `get_current_scene_type()` | O(1) | O(1) |
| `get_all_scene_types()` | O(n) | O(n) - 复制列表 |
| `set_scene_type()` | O(n) | O(1) - 线性搜索 |

**结论:** 所有接口调用开销极小，可以在检测循环中频繁调用。

---

## 扩展性设计

### 添加新配置项

只需3步：

**1. 在 app_config 添加字段**
```python
app_config["scene"]["new_field"] = default_value
```

**2. 在 GUI 添加控件**
```python
self.new_field_var = tk.StringVar(value=default_value)
```

**3. 添加公开接口**
```python
def get_new_field(self) -> str:
    return self.app_config["scene"]["new_field"]
```

---

## 文档架构

```
gui/
├── README.md                          # 文档导航中心
├── USER_INPUT_INTERFACE.md           # 用户指南（推荐首读）
├── SETTINGS_PANEL_API.md              # API完整参考
├── INTERFACE_IMPLEMENTATION_SUMMARY.md # 实现总结
└── ARCHITECTURE.md                    # 本文档（架构说明）
```

---

**文档版本:** v1.0  
**作者:** LXR（李修然）  
**最后更新:** 2025年11月11日
