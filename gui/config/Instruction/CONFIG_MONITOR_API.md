# 配置监听接口文档

## 📋 概述

`SettingsPanel` 提供了强大的配置监听功能，可以实时监控用户的配置变化并自动执行相应操作。

## 🚀 快速开始

### 基础用法

```python
from gui.main_window import MainWindow

# 创建主窗口
gui = MainWindow()

# 定义配置变化回调函数
def on_config_change(old_config, new_config):
    print("配置已更新！")
    # 处理配置变化...

# 启动配置监听
gui.settings_panel.start_config_monitor(on_config_change)

# 启动GUI
gui.run()
```

## 📚 API 参考

### 1. `start_config_monitor(callback, interval=500, print_changes=True, print_full_config=True)`

启动配置监听器。

**参数：**
- `callback` (callable): 配置变化时的回调函数，签名：`callback(old_config: Dict, new_config: Dict)`
- `interval` (int): 检查间隔（毫秒），默认 500ms
- `print_changes` (bool): 是否自动打印配置变化，默认 True
- `print_full_config` (bool): 是否在变化时打印完整配置，默认 True

**示例：**
```python
def my_callback(old_config, new_config):
    if old_config["scene_type"] != new_config["scene_type"]:
        reload_model(new_config["scene_type"])

gui.settings_panel.start_config_monitor(
    callback=my_callback,
    interval=1000,          # 每1秒检查一次
    print_changes=True,     # 打印变化
    print_full_config=False # 不打印完整配置
)
```

---

### 2. `stop_config_monitor()`

停止配置监听器。

**示例：**
```python
gui.settings_panel.stop_config_monitor()
```

---

### 3. `get_config_snapshot()`

获取当前配置的完整快照。

**返回：** `Dict` - 包含所有配置参数的字典

**配置快照结构：**
```python
{
    "scene_type": str,              # 当前场景类型
    "selected_scenes": list[str],   # 所有选中的场景
    "confidence_threshold": float,   # 置信度阈值
    "detection_interval": float,     # 检测间隔
    "camera_id": int,               # 摄像头ID
    "alert_delay": float,           # 告警延迟
    "light_condition": str,         # 光照条件
    "enable_roi": bool,             # 是否启用ROI
    "enable_sound": bool,           # 是否启用声音报警
    "enable_email": bool,           # 是否启用邮件通知
    "auto_record": bool,            # 是否自动录像
}
```

**示例：**
```python
snapshot = gui.settings_panel.get_config_snapshot()
print(f"当前场景: {snapshot['scene_type']}")
print(f"选中场景: {snapshot['selected_scenes']}")
```

---

### 4. `print_current_config()`

手动打印当前配置信息。

**示例：**
```python
gui.settings_panel.print_current_config()
```

**输出示例：**
```
============================================================
📋 当前配置信息:
============================================================
🎯 当前场景类型: 摔倒
📌 所有选中场景: 摔倒, 起火

⚙️  配置参数:
   • 置信度阈值: 0.5
   • 检测间隔: 1.0 秒
   • 摄像头ID: 0
   • 告警延迟: 2.0 秒

🎨 场景参数:
   • 光照条件: normal
   • 启用ROI: 否
   • 声音报警: 是
   • 邮件通知: 否
   • 自动录像: 否
============================================================
```

---

## 💡 使用场景

### 场景 1: 场景切换时重新加载模型

```python
def on_config_change(old_config, new_config):
    # 检测场景类型是否变化
    if old_config["scene_type"] != new_config["scene_type"]:
        print(f"场景切换: {old_config['scene_type']} → {new_config['scene_type']}")
        # 重新加载检测模型
        detector.load_model(new_config["scene_type"])
    
    # 检测选中场景列表变化
    old_scenes = set(old_config["selected_scenes"])
    new_scenes = set(new_config["selected_scenes"])
    if old_scenes != new_scenes:
        print(f"场景列表更新: {new_scenes}")
        # 为每个场景加载对应的提示词
        for scene in new_scenes:
            load_prompts_for_scene(scene)

gui.settings_panel.start_config_monitor(on_config_change)
```

---

### 场景 2: 摄像头参数变化时重启视频流

```python
def on_config_change(old_config, new_config):
    # 检测摄像头ID是否变化
    if old_config["camera_id"] != new_config["camera_id"]:
        print(f"摄像头切换: {old_config['camera_id']} → {new_config['camera_id']}")
        # 重启视频捕获
        video_capture.stop()
        video_capture.start(new_config["camera_id"])
    
    # 检测检测间隔是否变化
    if old_config["detection_interval"] != new_config["detection_interval"]:
        print(f"检测间隔更新: {new_config['detection_interval']}秒")
        # 更新检测器的帧率
        detector.set_interval(new_config["detection_interval"])

gui.settings_panel.start_config_monitor(on_config_change)
```

---

### 场景 3: 报警设置变化时更新通知系统

```python
def on_config_change(old_config, new_config):
    # 声音报警状态变化
    if old_config["enable_sound"] != new_config["enable_sound"]:
        if new_config["enable_sound"]:
            alert_system.enable_sound()
        else:
            alert_system.disable_sound()
    
    # 邮件通知状态变化
    if old_config["enable_email"] != new_config["enable_email"]:
        if new_config["enable_email"]:
            alert_system.enable_email()
        else:
            alert_system.disable_email()

gui.settings_panel.start_config_monitor(on_config_change)
```

---

### 场景 4: 仅监听特定配置项

```python
def on_config_change(old_config, new_config):
    # 只关注场景相关的变化
    scene_changed = (
        old_config["scene_type"] != new_config["scene_type"] or
        old_config["selected_scenes"] != new_config["selected_scenes"]
    )
    
    if scene_changed:
        print("场景配置已更新，重新初始化检测器...")
        detector.reinitialize(new_config["selected_scenes"])

# 禁用自动打印，自己处理输出
gui.settings_panel.start_config_monitor(
    callback=on_config_change,
    print_changes=False,
    print_full_config=False
)
```

---

### 场景 5: 记录配置变化历史

```python
config_history = []

def on_config_change(old_config, new_config):
    # 记录配置变化
    import datetime
    change_record = {
        "timestamp": datetime.datetime.now(),
        "old": old_config.copy(),
        "new": new_config.copy()
    }
    config_history.append(change_record)
    
    # 保存到日志文件
    with open("config_changes.log", "a") as f:
        f.write(f"{change_record}\n")
    
    print(f"配置变化已记录，历史记录数: {len(config_history)}")

gui.settings_panel.start_config_monitor(on_config_change)
```

---

## 🎯 完整示例

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.main_window import MainWindow
from typing import Dict

# 创建主窗口
gui = MainWindow()

# 定义配置变化处理函数
def handle_config_change(old_config: Dict, new_config: Dict):
    """处理配置变化"""
    
    # 1. 场景变化处理
    if old_config["scene_type"] != new_config["scene_type"]:
        print(f"✅ 场景已切换到: {new_config['scene_type']}")
        # TODO: 重新加载模型
    
    # 2. 多场景选择变化处理
    old_scenes = set(old_config["selected_scenes"])
    new_scenes = set(new_config["selected_scenes"])
    if old_scenes != new_scenes:
        added = new_scenes - old_scenes
        removed = old_scenes - new_scenes
        if added:
            print(f"✅ 新增场景: {', '.join(added)}")
            # TODO: 加载新场景的提示词
        if removed:
            print(f"✅ 移除场景: {', '.join(removed)}")
            # TODO: 卸载场景资源
    
    # 3. 摄像头变化处理
    if old_config["camera_id"] != new_config["camera_id"]:
        print(f"✅ 摄像头已切换到: {new_config['camera_id']}")
        # TODO: 重启视频流
    
    # 4. 报警设置变化处理
    if old_config["enable_sound"] != new_config["enable_sound"]:
        status = "启用" if new_config["enable_sound"] else "禁用"
        print(f"✅ 声音报警已{status}")
        # TODO: 更新报警系统

# 打印初始配置
print("\n" + "="*60)
print("🚀 系统启动")
print("="*60)
gui.settings_panel.print_current_config()

# 启动配置监听
gui.settings_panel.start_config_monitor(
    callback=handle_config_change,
    interval=500,
    print_changes=True,
    print_full_config=True
)

print("💡 配置监听器已启动，在GUI中修改配置会自动触发回调\n")

# 启动GUI
gui.run()
```

---

## ⚠️ 注意事项

1. **回调函数异常处理**
   - 回调函数中的异常会被自动捕获，不会中断监听器
   - 建议在回调函数中添加 try-except 处理关键逻辑

2. **性能考虑**
   - 默认检查间隔 500ms，可根据需要调整
   - 如果回调函数执行时间较长，建议增加 interval 值

3. **线程安全**
   - 回调函数在 Tkinter 主线程中执行
   - 如需执行耗时操作，建议使用线程或异步处理

4. **停止监听**
   - 监听器会在窗口关闭时自动停止
   - 也可以手动调用 `stop_config_monitor()` 停止

---

## 📊 监控的配置项

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `scene_type` | str | 当前场景类型（第一个选中的场景） |
| `selected_scenes` | list[str] | 所有选中的场景列表 |
| `confidence_threshold` | float | 置信度阈值 |
| `detection_interval` | float | 检测间隔（秒） |
| `camera_id` | int | 摄像头ID |
| `alert_delay` | float | 告警延迟（秒） |
| `light_condition` | str | 光照条件 ('bright' \| 'normal' \| 'dim') |
| `enable_roi` | bool | 是否启用ROI |
| `enable_sound` | bool | 是否启用声音报警 |
| `enable_email` | bool | 是否启用邮件通知 |
| `auto_record` | bool | 是否自动录像 |

---

## 🔗 相关文档

- [用户输入接口文档](USER_INPUT_INTERFACE.md)
- [多场景选择指南](MULTI_SCENE_GUIDE.md)
- [SettingsPanel API 参考](SETTINGS_PANEL_API.md)
