# 多场景选择功能使用指南

## 📋 功能概述

现在用户可以**同时选择多个场景**进行检测！新功能特点：

- ✅ 场景列表显示为复选框（可多选）
- ✅ 用户可以新建自定义场景
- ✅ 用户可以勾选/取消勾选场景
- ✅ 用户可以删除选中的场景
- ✅ 完全向后兼容旧代码
- ✅ 新增专用的多场景接口

---

## 🎨 UI 变化

### 之前（单选）
```
场景类型: [下拉框: 摔倒 ▼]  [➕ 新建场景]  [删除场景]
```

### 现在（多选）
```
[➕ 新建场景]  [🗑️ 删除场景]

场景列表（勾选启用）
┌──────────────┐
│ ☑ 摔倒      │
│ ☑ 起火      │
│ ☐ 闯入      │
│ ☐ 打架      │
└──────────────┘
（可滚动）
```

---

## 📊 数据结构变化

### 旧版配置
```python
app_config = {
    "scene": {
        "scene_type": "摔倒",  # 单个场景
        ...
    }
}
```

### 新版配置
```python
app_config = {
    "scene": {
        "scene_type": "摔倒",              # 保留（第一个选中的场景）
        "selected_scenes": ["摔倒", "起火"],  # 新增（所有选中的场景）
        ...
    }
}
```

**向后兼容说明：**
- `scene_type` 保留，始终等于第一个选中的场景
- 旧代码无需修改，仍可正常工作
- 新代码使用 `selected_scenes` 获取所有场景

---

## 🔌 对外接口

### 1️⃣ 读取接口

#### `get_selected_scenes()` - ⭐ 推荐（新增）

获取所有选中的场景列表。

```python
scenes = panel.get_selected_scenes()
# 返回: ["摔倒", "起火", "闯入"]

# 为每个场景执行检测
for scene in scenes:
    prompts = get_prompts_for_scene(scene)
    result = detector.detect(frame, prompts)
```

---

#### `get_current_scene_type()` - 向后兼容

获取第一个选中的场景（用于向后兼容）。

```python
scene = panel.get_current_scene_type()
# 返回: "摔倒"（第一个选中的）

# 旧代码仍可正常工作
prompts = get_prompts(scene)
```

---

#### `get_scene_config()` - 增强版

获取完整配置，现在包含 `selected_scenes` 字段。

```python
config = panel.get_scene_config()

# 返回:
{
    "scene_type": "摔倒",                    # 第一个（向后兼容）
    "selected_scenes": ["摔倒", "起火"],      # 所有选中的（新增）
    "light_condition": "normal",
    "enable_roi": False,
    ...
}

# 使用新字段
for scene in config["selected_scenes"]:
    detect(frame, scene)

# 旧代码仍可用
detect(frame, config["scene_type"])
```

---

### 2️⃣ 修改接口

#### `set_selected_scenes(list)` - ⭐ 推荐（新增）

设置选中的多个场景。

```python
# 设置多个场景
success = panel.set_selected_scenes(["摔倒", "起火", "闯入"])
if success:
    print("场景设置成功")
    
# 获取验证
scenes = panel.get_selected_scenes()
print(scenes)  # ["摔倒", "起火", "闯入"]
```

---

#### `set_scene_type(scene)` - 向后兼容

设置单个场景（会清除其他选择）。

```python
# 只选中一个场景
success = panel.set_scene_type("起火")

# 结果：selected_scenes = ["起火"]
scenes = panel.get_selected_scenes()
print(scenes)  # ["起火"]
```

---

#### `update_scene_config(dict)` - 增强版

批量更新配置，现在支持 `selected_scenes` 字段。

```python
# 方式1：使用 selected_scenes（推荐）
panel.update_scene_config({
    "selected_scenes": ["摔倒", "起火"],
    "light_condition": "bright"
})

# 方式2：使用 scene_type（向后兼容）
panel.update_scene_config({
    "scene_type": "起火",  # 只选中这一个
    "enable_sound": True
})
```

---

## 💡 使用示例

### 示例1：为所有选中的场景执行检测

```python
class MultiSceneDetector:
    def __init__(self, settings_panel):
        self.panel = settings_panel
    
    def detect_frame(self, frame):
        """为每个选中的场景执行检测"""
        # 获取所有选中的场景
        selected_scenes = self.panel.get_selected_scenes()
        
        print(f"检测场景: {selected_scenes}")
        
        results = []
        for scene in selected_scenes:
            # 为每个场景生成提示词
            prompts = self.get_prompts_for_scene(scene)
            
            # 执行检测
            result = self.clip_detect(frame, prompts)
            
            if result.detected:
                results.append({
                    "scene": scene,
                    "confidence": result.confidence
                })
        
        return results
    
    def get_prompts_for_scene(self, scene):
        """根据场景生成提示词"""
        prompts_map = {
            "摔倒": ["person falling down", "person lying on ground"],
            "起火": ["fire", "flames", "smoke"],
            "闯入": ["person entering", "unauthorized person"],
            "打架": ["people fighting", "violent behavior"]
        }
        return prompts_map.get(scene, [])
```

---

### 示例2：向后兼容模式（旧代码无需修改）

```python
class OldDetector:
    def __init__(self, settings_panel):
        self.panel = settings_panel
    
    def detect_frame(self, frame):
        """旧代码，使用 scene_type（仍可正常工作）"""
        # 获取当前场景（第一个选中的）
        scene = self.panel.get_current_scene_type()
        
        # 或使用 get_scene_config()
        config = self.panel.get_scene_config()
        scene = config["scene_type"]
        
        # 执行检测
        prompts = self.get_prompts(scene)
        return self.detect(frame, prompts)
```

---

### 示例3：组合检测结果

```python
def detect_with_multi_scenes(frame, panel):
    """组合多个场景的检测结果"""
    scenes = panel.get_selected_scenes()
    
    # 收集所有场景的提示词
    all_prompts = []
    for scene in scenes:
        prompts = get_prompts_for_scene(scene)
        all_prompts.extend(prompts)
    
    # 一次性检测所有提示词
    results = clip_detector.detect(frame, all_prompts, threshold=0.25)
    
    # 处理结果
    for result in results:
        print(f"检测到: {result.label}, 置信度: {result.confidence}")
    
    return results
```

---

### 示例4：根据时间段自动切换场景

```python
import datetime

def auto_switch_scenes(panel):
    """根据时间自动切换检测场景"""
    hour = datetime.datetime.now().hour
    
    if 22 <= hour or hour < 6:
        # 夜间：只检测闯入
        panel.set_selected_scenes(["闯入"])
        panel.update_scene_config({"light_condition": "dim"})
        print("夜间模式：监测闯入")
    
    elif 9 <= hour < 18:
        # 白天：检测多种场景
        panel.set_selected_scenes(["摔倒", "起火", "打架"])
        panel.update_scene_config({"light_condition": "normal"})
        print("白天模式：全面监测")
    
    else:
        # 过渡时段
        panel.set_selected_scenes(["摔倒", "闯入"])
        panel.update_scene_config({"light_condition": "bright"})
        print("过渡时段：重点监测")
```

---

## 🔄 迁移指南

### 对于使用旧接口的协作者

**好消息：无需修改代码！** 旧接口完全兼容。

```python
# 旧代码（仍可正常工作）✅
scene = panel.get_current_scene_type()
config = panel.get_scene_config()
scene_type = config["scene_type"]
```

---

### 对于想使用多场景的协作者

**只需改用新接口：**

```python
# 旧方式（单场景）
scene = panel.get_current_scene_type()
result = detect(frame, scene)

# 新方式（多场景）⭐
scenes = panel.get_selected_scenes()
for scene in scenes:
    result = detect(frame, scene)
```

---

## 🧪 测试

运行测试脚本：

```bash
python examples/test_multi_scene.py
```

输出示例：
```
============================================================
测试多场景配置功能
============================================================

初始配置:
  选中场景: ['摔倒']
  scene_type（兼容）: 摔倒

用户选择多个场景: ['摔倒', '起火']
  选中场景: ['摔倒', '起火']
  scene_type（兼容）: 摔倒

为每个场景生成检测提示词:
  摔倒: ['person falling', 'person on ground']
  起火: ['fire', 'flames', 'smoke']

✓ 向后兼容，旧代码仍可正常工作
```

---

## 📖 API 速查表

| 接口 | 类型 | 功能 | 兼容性 |
|------|------|------|--------|
| `get_selected_scenes()` | 读取 | 获取所有选中场景 | ⭐ 新增 |
| `get_current_scene_type()` | 读取 | 获取第一个场景 | ✅ 兼容 |
| `get_scene_config()` | 读取 | 获取完整配置（含 selected_scenes） | ✅ 增强 |
| `set_selected_scenes(list)` | 修改 | 设置多个场景 | ⭐ 新增 |
| `set_scene_type(scene)` | 修改 | 设置单个场景 | ✅ 兼容 |
| `update_scene_config(dict)` | 修改 | 批量更新（支持 selected_scenes） | ✅ 增强 |

---

## ⚠️ 注意事项

### 1. 配置初始化

如果使用旧的 `app_config`，系统会自动添加 `selected_scenes` 字段：

```python
# 旧配置
app_config = {
    "scene": {"scene_type": "摔倒", ...}
}

# SettingsPanel 会自动添加
app_config["scene"]["selected_scenes"] = ["摔倒"]
```

---

### 2. 删除场景

- 内置场景（"摔倒"、"起火"）**无法删除**
- 删除场景时会同时从选中列表移除
- 删除场景前需先勾选要删除的场景

---

### 3. 场景顺序

`selected_scenes` 列表的顺序由用户勾选顺序决定，`scene_type` 始终等于列表的第一个元素。

---

## 🎯 最佳实践

### ✅ 推荐做法

```python
# 1. 使用新接口获取多场景
scenes = panel.get_selected_scenes()
for scene in scenes:
    process(scene)

# 2. 设置多场景时检查返回值
if panel.set_selected_scenes(["摔倒", "起火"]):
    print("设置成功")
else:
    print("场景不存在")

# 3. 检查是否有选中的场景
scenes = panel.get_selected_scenes()
if not scenes:
    print("警告：未选择任何场景")
```

---

### ❌ 避免的做法

```python
# 不要直接访问内部变量
scenes = panel.app_config["scene"]["selected_scenes"]  # ❌

# 应该使用公开接口
scenes = panel.get_selected_scenes()  # ✅
```

---

## 📞 常见问题

### Q1: 旧代码需要修改吗？

**A:** 不需要！旧接口完全兼容，`scene_type` 仍然可用。

---

### Q2: 如何判断用户选了多个场景？

```python
scenes = panel.get_selected_scenes()
if len(scenes) > 1:
    print(f"用户选择了 {len(scenes)} 个场景")
```

---

### Q3: scene_type 和 selected_scenes 的关系？

**A:** `scene_type` = `selected_scenes[0]`（第一个选中的场景）

---

### Q4: 如何清空所有选择？

目前不支持清空所有场景。至少需要选中一个场景。如果尝试设置空列表，`set_selected_scenes([])` 会返回 `False`。

---

## 🔗 相关文档

- [用户输入接口指南](USER_INPUT_INTERFACE.md)
- [API完整文档](SETTINGS_PANEL_API.md)
- [系统架构](ARCHITECTURE.md)

---

**版本:** v2.0（多场景支持）  
**作者:** LXR（李修然）  
**更新日期:** 2025年11月12日
