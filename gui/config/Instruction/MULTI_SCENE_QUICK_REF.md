# 多场景功能快速参考

## 🆕 新功能（v2.0）

用户现在可以**同时选择多个场景**进行检测！

---

## ⚡ 快速上手

### 获取所有选中的场景

```python
scenes = panel.get_selected_scenes()
# 返回: ["摔倒", "起火", "闯入"]
```

### 设置多个场景

```python
panel.set_selected_scenes(["摔倒", "起火"])
```

### 为每个场景执行检测

```python
for scene in panel.get_selected_scenes():
    prompts = get_prompts(scene)
    detect(frame, prompts)
```

---

## 📊 新增接口

| 接口 | 功能 | 示例 |
|------|------|------|
| `get_selected_scenes()` | 获取所有选中场景 | `["摔倒", "起火"]` |
| `set_selected_scenes(list)` | 设置多个场景 | `["摔倒", "起火", "闯入"]` |

---

## ✅ 向后兼容

旧代码**无需修改**：

```python
# 旧接口仍可用 ✅
scene = panel.get_current_scene_type()
config = panel.get_scene_config()
scene = config["scene_type"]
```

---

## 🎨 UI 变化

### 之前
```
场景类型: [下拉框 ▼]
```

### 现在
```
场景列表（勾选启用）
☑ 摔倒
☑ 起火
☐ 闯入
```

---

## 📖 详细文档

- [多场景功能指南](MULTI_SCENE_GUIDE.md) - 完整使用指南
- [实现总结](MULTI_SCENE_IMPLEMENTATION.md) - 技术细节

---

## 🧪 测试

```bash
# 无GUI测试
python examples/test_multi_scene.py

# GUI测试
python examples/test_multi_scene_gui.py
```

---

**版本:** v2.0  
**更新:** 2025-11-12
