# 配置持久化实现总结

## 修改内容

### 1. 主窗口 (`gui/main_window.py`)

#### 添加配置字典
在 `MainWindow.__init__()` 中添加了应用配置字典：

```python
# 应用配置（在主窗口关闭前保持）
self.app_config = {
    "rtsp": {
        "url": "rtsp://",
        "username": "",
        "password": "",
        "port": "554",
        "timeout": "10"
    },
    "scene": {
        "scene_type": "摔倒",
        "light_condition": "normal",
        "enable_roi": False,
        "enable_sound": True,
        "enable_email": False,
        "auto_record": True
    },
    "scene_types": ["摔倒", "起火"]
}
```

#### 修改设置面板打开方式
在 `_on_settings()` 方法中，将配置字典传递给设置面板：

```python
def _on_settings(self) -> None:
    """打开设置面板"""
    if self.settings_panel is None or not self.settings_panel.parent.winfo_exists():
        self.settings_panel = SettingsPanel(app_config=self.app_config)
```

### 2. 设置面板 (`gui/settings_panel.py`)

#### 修改构造函数
接受并使用共享的配置字典：

```python
def __init__(self, app_config: dict = None) -> None:
    """初始化设置面板"""
    # 使用传入的配置或创建默认配置（用于独立测试）
    if app_config is None:
        app_config = {
            "rtsp": {...},
            "scene": {...},
            "scene_types": ["摔倒", "起火"]
        }
    self.app_config = app_config
    self.scene_types = self.app_config["scene_types"]
    # ...
```

#### RTSP页面配置绑定

**初始化时从配置读取**：
```python
# 从app_config读取初始值
self.rtsp_url_var = tk.StringVar(value=self.app_config["rtsp"]["url"])
self.rtsp_user_var = tk.StringVar(value=self.app_config["rtsp"]["username"])
self.rtsp_pass_var = tk.StringVar(value=self.app_config["rtsp"]["password"])
self.rtsp_port_var = tk.StringVar(value=self.app_config["rtsp"]["port"])
self.rtsp_timeout_var = tk.IntVar(value=int(self.app_config["rtsp"]["timeout"]))
```

**保存时写回配置**：
```python
def _save_rtsp_config(self) -> None:
    """保存RTSP配置"""
    self.app_config["rtsp"]["url"] = self.rtsp_url_var.get()
    self.app_config["rtsp"]["username"] = self.rtsp_user_var.get()
    self.app_config["rtsp"]["password"] = self.rtsp_pass_var.get()
    self.app_config["rtsp"]["port"] = self.rtsp_port_var.get()
    self.app_config["rtsp"]["timeout"] = str(self.rtsp_timeout_var.get())
    
    messagebox.showinfo("保存成功", "RTSP配置已保存")
    print(f"RTSP配置已保存到app_config: {self.app_config['rtsp']}")
```

#### 场景页面配置绑定

**初始化时从配置读取**：
```python
# 从app_config读取初始值
self.scene_type_var = tk.StringVar(value=self.app_config["scene"]["scene_type"])
self.light_condition_var = tk.StringVar(value=self.app_config["scene"]["light_condition"])
self.enable_roi_var = tk.BooleanVar(value=self.app_config["scene"]["enable_roi"])
self.enable_sound_var = tk.BooleanVar(value=self.app_config["scene"]["enable_sound"])
self.enable_email_var = tk.BooleanVar(value=self.app_config["scene"]["enable_email"])
self.auto_record_var = tk.BooleanVar(value=self.app_config["scene"]["auto_record"])
```

**保存时写回配置**：
```python
def _save_scene_config(self) -> None:
    """保存场景配置"""
    self.app_config["scene"]["scene_type"] = self.scene_type_var.get()
    self.app_config["scene"]["light_condition"] = self.light_condition_var.get()
    self.app_config["scene"]["enable_roi"] = self.enable_roi_var.get()
    self.app_config["scene"]["enable_sound"] = self.enable_sound_var.get()
    self.app_config["scene"]["enable_email"] = self.enable_email_var.get()
    self.app_config["scene"]["auto_record"] = self.auto_record_var.get()
    
    messagebox.showinfo("保存成功", "场景配置已保存")
    print(f"场景配置已保存到app_config: {self.app_config['scene']}")
```

## 工作原理

1. **主窗口拥有配置**：`MainWindow` 类在初始化时创建 `app_config` 字典
2. **引用传递**：打开设置面板时，将 `app_config` 的引用传递给 `SettingsPanel`
3. **双向绑定**：
   - 设置面板打开时，从 `app_config` 读取值初始化UI控件
   - 点击"保存配置"时，将UI控件的值写回 `app_config`
4. **持久化**：由于使用的是引用传递，所有修改都会影响主窗口的 `app_config`
5. **重新打开**：再次打开设置面板时，从已更新的 `app_config` 读取值

## 数据流图

```
MainWindow
└── app_config (字典) ─┐
                       │ (引用传递)
                       ↓
                  SettingsPanel
                  ├── 打开时：读取 app_config → UI控件
                  └── 保存时：UI控件 → 写入 app_config
                       │
                       └─→ 影响主窗口的 app_config
```

## 生命周期

- **创建**：主窗口启动时创建 `app_config`
- **存活**：整个程序运行期间保持
- **销毁**：主窗口关闭时销毁（配置丢失）

## 与之前的区别

### 之前的问题
```python
def _save_rtsp_config(self) -> None:
    # 创建本地字典，仅用于打印
    config = {
        "url": self.rtsp_url_var.get(),
        # ...
    }
    print(f"RTSP配置: {config}")  # 只打印，不保存
    # 关闭面板后配置丢失
```

### 现在的解决方案
```python
def _save_rtsp_config(self) -> None:
    # 直接更新共享配置
    self.app_config["rtsp"]["url"] = self.rtsp_url_var.get()
    # ...
    print(f"RTSP配置已保存到app_config: {self.app_config['rtsp']}")
    # 配置保持在主窗口的app_config中
```

## 测试方法

1. 运行程序：`/usr/local/bin/python3 gui/main_window.py`
2. 打开设置面板，修改配置，点击"保存配置"
3. 关闭设置面板
4. 重新打开设置面板
5. **验证**：配置应该保持之前修改的值

详细测试步骤请参考 `CONFIG_PERSISTENCE_TEST.md`

## 后续可能的增强

1. **配置文件持久化**：保存配置到 JSON/INI 文件
2. **自动保存**：修改配置后自动保存，无需点击按钮
3. **配置验证**：保存前验证配置的有效性
4. **配置导入/导出**：支持配置的备份和恢复
5. **多配置方案**：支持保存和切换不同的配置方案
