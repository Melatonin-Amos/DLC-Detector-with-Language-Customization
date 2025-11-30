# TODO: 设置面板（拓展功能）
#
# 功能说明：
# 1. 提供场景配置界面
# 2. 视频/摄像头配置
# 3. 阈值调整（不给用户）
#
# 主要类：
# - SettingsPanel: 设置面板类
#
# 开发优先级：⭐ (第10-11周完成)

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Optional, Union, Callable
from ttkthemes import ThemedStyle
import threading
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.config_updater import ConfigUpdater, PROTECTED_SCENE_NAMES
import yaml


class SettingsPanel:
    """设置面板类 - 左侧导航右侧内容的双栏布局"""

    def __init__(
        self, parent: Union[tk.Tk, tk.Toplevel], app_config: Dict = None
    ) -> None:
        """
        初始化设置面板

        Args:
            parent: 父窗口
            app_config: 应用程序配置字典（从主窗口传入，用于持久化配置）
        """
        self.parent = parent
        self.current_page: Optional[str] = None
        self.content_frames: Dict[str, ttk.Frame] = {}

        # 初始化字体配置
        self._setup_fonts()

        # 使用传入的配置或创建新配置（用于测试）
        if app_config is None:
            # 测试模式：创建默认配置
            self.app_config = {
                "video": {
                    "default_path": "",
                    "auto_play": True,
                    "loop_play": False,
                    "default_speed": "1.0",
                },
                "camera": {
                    "camera_index": "0",
                    "resolution": "1280x720",
                },
                "scene": {
                    "scene_type": "摔倒",  # 保留用于向后兼容
                    "selected_scenes": ["摔倒"],  # 新增：用户选择的多个场景
                    "light_condition": "normal",
                    "enable_roi": False,
                    "enable_sound": True,
                    "enable_email": False,
                    "auto_record": False,
                },
                "scene_types": ["摔倒", "起火"],
            }
        else:
            # 生产模式：使用主窗口传入的配置
            self.app_config = app_config
            # 确保存在 selected_scenes 字段（向后兼容）
            if "selected_scenes" not in self.app_config.get("scene", {}):
                # 从旧的 scene_type 初始化
                if "scene" in self.app_config:
                    self.app_config["scene"]["selected_scenes"] = [
                        self.app_config["scene"].get("scene_type", "摔倒")
                    ]
            # 确保存在 video 和 camera 配置
            if "video" not in self.app_config:
                self.app_config["video"] = {
                    "default_path": "",
                    "auto_play": True,
                    "loop_play": False,
                    "default_speed": "1.0",
                }
            if "camera" not in self.app_config:
                self.app_config["camera"] = {
                    "camera_index": "0",
                    "resolution": "1280x720",
                }

        # 初始化 ConfigUpdater（复用实例，避免重复创建）
        self._config_updater: Optional[ConfigUpdater] = None
        self._init_config_updater()
        
        # 场景变化回调（用于通知外部组件，如检测器热重载）
        self._on_scenarios_changed_callback: Optional[Callable] = None

        # 场景类型列表：优先从 YAML 加载，否则使用配置或默认值
        self.scene_types: list[
            str
        ] = self._load_scene_types_from_yaml() or self.app_config.get(
            "scene_types", ["摔倒", "起火"]
        )
        # 同步到 app_config
        self.app_config["scene_types"] = self.scene_types

        # 场景复选框变量字典 {场景名: BooleanVar}
        self.scene_checkbox_vars: Dict[str, tk.BooleanVar] = {}

        # 设置窗口长宽比 (3:2)
        self.aspect_ratio = 3 / 2

        # 缩放状态跟踪
        self._resize_state = {
            "lock": False,  # 防止递归调用
            "width": 1000,  # 初始宽度
            "height": 666,  # 初始高度 (保持3:2比例)
            "initialized": False,  # 是否已完成初始化
        }

        # 创建主容器
        self._create_main_container()

        # 创建左侧导航栏
        self._create_navigation()

        # 创建右侧内容区域
        self._create_content_area()

        # 创建各个设置页面
        self._create_pages()

        # 默认显示视频配置页面
        self.show_page("video")

        # 绑定窗口缩放事件
        self.parent.bind("<Configure>", self._on_window_resize)

    def _init_config_updater(self) -> None:
        """初始化配置更新器实例（带异常处理）"""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config",
                "detection",
                "default.yaml",
            )
            self._config_updater = ConfigUpdater(config_path)
        except FileNotFoundError as e:
            print(f"⚠️  配置文件不存在: {e}")
            self._config_updater = None
        except Exception as e:
            print(f"⚠️  ConfigUpdater 初始化失败: {e}")
            self._config_updater = None

    def get_config_updater(self) -> Optional[ConfigUpdater]:
        """
        获取配置更新器实例（安全访问）
        
        Returns:
            ConfigUpdater 实例，若不可用则返回 None
        """
        return self._config_updater

    def set_scenarios_changed_callback(self, callback: Callable) -> None:
        """
        设置场景变化回调函数
        
        当场景配置发生变化时（新增、删除、启用/禁用），
        会调用此回调通知外部组件（如检测器）进行热重载。
        
        Args:
            callback: 回调函数，无参数
        """
        self._on_scenarios_changed_callback = callback

    def _notify_scenarios_changed(self) -> None:
        """通知外部组件场景配置已变化"""
        if self._on_scenarios_changed_callback:
            try:
                self._on_scenarios_changed_callback()
            except Exception as e:
                print(f"⚠️  场景变化回调执行失败: {e}")

    def _load_scene_types_from_yaml(self) -> Optional[list[str]]:
        """从 YAML 配置文件加载场景类型列表

        Returns:
            场景类型列表，如果加载失败返回 None
        """
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config",
                "detection",
                "default.yaml",
            )

            if not os.path.exists(config_path):
                return None

            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config or "scenarios" not in config:
                return None

            # 从 scenarios 中提取场景名称和启用状态
            scenarios = config["scenarios"]
            scene_types = []
            enabled_scenes = []
            
            for scenario in scenarios.values():
                name = scenario.get("name")
                if name:
                    scene_types.append(name)
                    # 收集已启用的场景
                    if scenario.get("enabled", False):
                        enabled_scenes.append(name)

            if scene_types:
                # 同步已启用的场景到 app_config
                if enabled_scenes and "scene" in self.app_config:
                    self.app_config["scene"]["selected_scenes"] = enabled_scenes
                return scene_types

        except Exception as e:
            print(f"⚠️  从 YAML 加载场景失败: {e}")

        return None

    def _setup_fonts(self) -> None:
        """配置字体和样式"""
        # 强制使用微软雅黑，全部加粗
        self.font_family = "Microsoft YaHei"

        # 定义不同用途的字体 - 全部加粗，字号加大
        self.fonts = {
            "normal": (self.font_family, 12, "bold"),
            "title": (self.font_family, 16, "bold"),
            "large": (self.font_family, 18, "bold"),
            "small": (self.font_family, 11, "bold"),
            "italic": (self.font_family, 12, "bold"),
        }

        # 配置ttk样式
        style = ttk.Style()

        # 配置基本样式
        style.configure(".", font=self.fonts["normal"])
        style.configure("TButton", font=self.fonts["normal"], padding=(12, 6))
        style.configure("TLabel", font=self.fonts["normal"])
        style.configure("TLabelframe", padding=15)
        style.configure("TLabelframe.Label", font=self.fonts["title"])
        style.configure("TCombobox", padding=5)
        style.configure("TEntry", padding=5)
        style.configure("TCheckbutton", font=self.fonts["normal"])
        style.configure("TRadiobutton", font=self.fonts["normal"])

        # 自定义导航按钮样式
        style.configure(
            "Nav.TButton",
            font=self.fonts["normal"],
            padding=(15, 12),
        )

        # 自定义操作按钮样式
        style.configure(
            "Action.TButton",
            font=self.fonts["normal"],
            padding=(12, 8),
        )

    def _create_main_container(self) -> None:
        """创建主容器"""
        self.main_container = ttk.Frame(self.parent)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 配置网格权重
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=0)  # 左侧导航固定宽度
        self.main_container.grid_columnconfigure(1, weight=1)  # 右侧内容可扩展

    def _create_navigation(self) -> None:
        """创建左侧导航栏"""
        # 导航栏框架 - 增加内边距
        nav_frame = ttk.LabelFrame(self.main_container, text="设置选项", padding=15)
        nav_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        # 1. 视频配置按钮
        self.btn_video = ttk.Button(
            nav_frame,
            text="🎬 视频配置",
            command=lambda: self.show_page("video"),
            width=18,
            style="Nav.TButton",
        )
        self.btn_video.pack(fill=tk.X, pady=(0, 12))

        # 2. 场景配置按钮
        self.btn_scene = ttk.Button(
            nav_frame,
            text="🎯 场景配置",
            command=lambda: self.show_page("scene"),
            width=18,
            style="Nav.TButton",
        )
        self.btn_scene.pack(fill=tk.X, pady=(0, 12))

        # 保存按钮列表以便高亮显示
        self.nav_buttons = {
            "video": self.btn_video,
            "scene": self.btn_scene,
        }

    def _create_content_area(self) -> None:
        """创建右侧内容区域容器"""
        self.content_container = ttk.Frame(self.main_container)
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

    def _center_window(self, window: tk.Toplevel, width: int, height: int) -> None:
        """
        将窗口居中显示在屏幕上

        Args:
            window: 要居中的窗口
            width: 窗口宽度
            height: 窗口高度
        """
        # 获取屏幕尺寸
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # 计算居中位置
        center_x = int((screen_width - width) / 2)
        center_y = int((screen_height - height) / 2)

        # 设置窗口位置
        window.geometry(f"{width}x{height}+{center_x}+{center_y}")

    def _create_pages(self) -> None:
        """创建所有设置页面"""
        # 创建视频配置页面
        self.content_frames["video"] = self._create_video_page()

        # 创建场景配置页面
        self.content_frames["scene"] = self._create_scene_page()

    def _create_video_page(self) -> ttk.Frame:
        """创建视频配置页面"""
        frame = ttk.LabelFrame(self.content_container, text="🎬 视频配置", padding=20)

        # 说明文字
        desc_label = ttk.Label(
            frame,
            text="配置本地视频和摄像头参数",
            font=self.fonts["italic"],
            foreground="gray",
        )
        desc_label.pack(anchor="w", pady=(0, 20))

        # === 本地视频设置 ===
        video_section = ttk.LabelFrame(frame, text="本地视频", padding=15)
        video_section.pack(fill=tk.X, pady=(0, 20))

        # 默认视频路径
        path_frame = ttk.Frame(video_section)
        path_frame.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(path_frame, text="默认路径:", width=12, anchor="w").pack(side=tk.LEFT)
        self.video_path_var = tk.StringVar(
            value=self.app_config.get("video", {}).get("default_path", "")
        )
        ttk.Entry(path_frame, textvariable=self.video_path_var, width=40).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10)
        )
        ttk.Button(
            path_frame,
            text="浏览...",
            command=self._browse_video,
            width=10,
            style="Action.TButton",
        ).pack(side=tk.LEFT)

        # 播放选项
        options_frame = ttk.Frame(video_section)
        options_frame.pack(fill=tk.X, pady=(0, 12))

        self.auto_play_var = tk.BooleanVar(
            value=self.app_config.get("video", {}).get("auto_play", True)
        )
        ttk.Checkbutton(
            options_frame, text="加载后自动播放", variable=self.auto_play_var
        ).pack(side=tk.LEFT, padx=(0, 30))

        self.loop_play_var = tk.BooleanVar(
            value=self.app_config.get("video", {}).get("loop_play", False)
        )
        ttk.Checkbutton(
            options_frame, text="循环播放", variable=self.loop_play_var
        ).pack(side=tk.LEFT)

        # 默认倍速
        speed_frame = ttk.Frame(video_section)
        speed_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(speed_frame, text="默认倍速:", width=12, anchor="w").pack(
            side=tk.LEFT
        )
        self.default_speed_var = tk.StringVar(
            value=self.app_config.get("video", {}).get("default_speed", "1.0")
        )
        speed_combo = ttk.Combobox(
            speed_frame,
            textvariable=self.default_speed_var,
            values=["0.25", "0.5", "1.0", "1.5", "2.0", "3.0"],
            state="readonly",
            width=12,
        )
        speed_combo.pack(side=tk.LEFT, padx=(10, 0))

        # === 摄像头设置 ===
        camera_section = ttk.LabelFrame(frame, text="本地摄像头", padding=15)
        camera_section.pack(fill=tk.X, pady=(0, 20))

        # 摄像头索引
        camera_frame = ttk.Frame(camera_section)
        camera_frame.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(camera_frame, text="摄像头索引:", width=12, anchor="w").pack(
            side=tk.LEFT
        )
        self.camera_index_var = tk.StringVar(
            value=self.app_config.get("camera", {}).get("camera_index", "0")
        )
        ttk.Combobox(
            camera_frame,
            textvariable=self.camera_index_var,
            values=["0", "1", "2", "3"],
            state="readonly",
            width=12,
        ).pack(side=tk.LEFT, padx=(10, 0))

        # 分辨率
        resolution_frame = ttk.Frame(camera_section)
        resolution_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(resolution_frame, text="分辨率:", width=12, anchor="w").pack(
            side=tk.LEFT
        )
        self.resolution_var = tk.StringVar(
            value=self.app_config.get("camera", {}).get("resolution", "1280x720")
        )
        ttk.Combobox(
            resolution_frame,
            textvariable=self.resolution_var,
            values=["640x480", "1280x720", "1920x1080"],
            state="readonly",
            width=15,
        ).pack(side=tk.LEFT, padx=(10, 0))

        # 按钮区域 - 增加间距
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))

        ttk.Button(
            button_frame,
            text="测试摄像头",
            command=self._test_camera,
            style="Action.TButton",
        ).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Button(
            button_frame,
            text="保存配置",
            command=self._save_video_config,
            style="Action.TButton",
        ).pack(side=tk.LEFT)

        return frame

    def _browse_video(self) -> None:
        """浏览选择视频文件"""
        file_path = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=[
                ("视频文件", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv"),
                ("所有文件", "*.*"),
            ],
        )
        if file_path:
            self.video_path_var.set(file_path)

    def _test_camera(self) -> None:
        """测试摄像头连接"""
        camera_index = int(self.camera_index_var.get())
        messagebox.showinfo(
            "测试摄像头", f"正在测试摄像头 {camera_index}...\n(此功能待实现)"
        )

    def _save_video_config(self) -> None:
        """保存视频配置"""
        # 更新配置
        if "video" not in self.app_config:
            self.app_config["video"] = {}
        if "camera" not in self.app_config:
            self.app_config["camera"] = {}

        self.app_config["video"]["default_path"] = self.video_path_var.get()
        self.app_config["video"]["auto_play"] = self.auto_play_var.get()
        self.app_config["video"]["loop_play"] = self.loop_play_var.get()
        self.app_config["video"]["default_speed"] = self.default_speed_var.get()
        self.app_config["camera"]["camera_index"] = self.camera_index_var.get()
        self.app_config["camera"]["resolution"] = self.resolution_var.get()

        messagebox.showinfo("保存成功", "视频配置已保存")
        print(
            f"视频配置已保存: {self.app_config['video']}, {self.app_config['camera']}"
        )

    def _create_scene_page(self) -> ttk.Frame:
        """创建场景配置页面"""
        frame = ttk.LabelFrame(self.content_container, text="🎯 场景配置", padding=20)

        # 说明文字
        desc_label = ttk.Label(
            frame,
            text="选择要启用的检测场景（可多选）",
            font=self.fonts["italic"],
            foreground="gray",
        )
        desc_label.pack(anchor="w", pady=(0, 20))

        # 场景管理按钮区
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(0, 20))

        # 新建场景按钮
        ttk.Button(
            button_frame,
            text="➕ 新建场景",
            command=self._create_new_scene,
            width=13,
            style="Action.TButton",
        ).pack(side=tk.LEFT, padx=(0, 12))

        # 删除场景按钮
        ttk.Button(
            button_frame,
            text="🗑️ 删除场景",
            command=self._delete_selected_scenes,
            width=13,
            style="Action.TButton",
        ).pack(side=tk.LEFT)

        # 场景选择区域（可滚动）
        scene_frame = ttk.LabelFrame(frame, text="场景列表（勾选启用）", padding=18)
        scene_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # 创建滚动条和画布
        canvas = tk.Canvas(scene_frame, height=150, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scene_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 存储画布和滚动框架的引用
        self.scene_canvas = canvas

        # 创建场景复选框
        self._create_scene_checkboxes()

        # 场景参数区域
        params_frame = ttk.LabelFrame(frame, text="通用场景参数", padding=15)
        params_frame.pack(fill=tk.X, pady=(0, 15))

        # 光照条件
        light_frame = ttk.Frame(params_frame)
        light_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(light_frame, text="光照条件:", width=12, anchor="w").pack(
            side=tk.LEFT
        )
        self.light_condition_var = tk.StringVar(
            value=self.app_config.get("scene", {}).get("light_condition", "normal")
        )
        ttk.Radiobutton(
            light_frame, text="明亮", variable=self.light_condition_var, value="bright"
        ).pack(side=tk.LEFT, padx=(10, 15))
        ttk.Radiobutton(
            light_frame, text="正常", variable=self.light_condition_var, value="normal"
        ).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(
            light_frame, text="昏暗", variable=self.light_condition_var, value="dim"
        ).pack(side=tk.LEFT)

        # 检测区域
        area_frame = ttk.Frame(params_frame)
        area_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(area_frame, text="检测区域:", width=12, anchor="w").pack(side=tk.LEFT)
        self.enable_roi_var = tk.BooleanVar(
            value=self.app_config.get("scene", {}).get("enable_roi", False)
        )
        ttk.Checkbutton(
            area_frame,
            text="启用感兴趣区域(ROI)",
            variable=self.enable_roi_var,
            command=self._toggle_roi,
        ).pack(side=tk.LEFT, padx=(10, 0))

        # 报警设置
        alarm_frame = ttk.Frame(params_frame)
        alarm_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(alarm_frame, text="报警设置:", width=12, anchor="w").pack(
            side=tk.LEFT
        )
        self.enable_sound_var = tk.BooleanVar(
            value=self.app_config.get("scene", {}).get("enable_sound", True)
        )
        ttk.Checkbutton(
            alarm_frame, text="声音报警", variable=self.enable_sound_var
        ).pack(side=tk.LEFT, padx=(10, 20))

        self.enable_email_var = tk.BooleanVar(
            value=self.app_config.get("scene", {}).get("enable_email", False)
        )
        ttk.Checkbutton(
            alarm_frame, text="短信通知", variable=self.enable_email_var
        ).pack(side=tk.LEFT)

        # 录像设置
        record_frame = ttk.Frame(params_frame)
        record_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(record_frame, text="录像设置:", width=12, anchor="w").pack(
            side=tk.LEFT
        )
        self.auto_record_var = tk.BooleanVar(
            value=self.app_config.get("scene", {}).get("auto_record", False)
        )
        ttk.Checkbutton(
            record_frame, text="事件触发时自动录像", variable=self.auto_record_var
        ).pack(side=tk.LEFT, padx=(10, 0))

        # 按钮区域
        scene_button_frame = ttk.Frame(frame)
        scene_button_frame.pack(fill=tk.X, pady=(15, 10))

        ttk.Button(
            scene_button_frame,
            text="设置ROI区域",
            command=self._set_roi_area,
            style="Action.TButton",
        ).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Button(
            scene_button_frame,
            text="保存场景配置",
            command=self._save_scene_config,
            style="Action.TButton",
        ).pack(side=tk.LEFT)

        return frame

    def _create_scene_checkboxes(self) -> None:
        """创建场景复选框列表"""
        # 清空现有复选框
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.scene_checkbox_vars.clear()

        # 获取已选中的场景列表
        selected_scenes = self.app_config["scene"]["selected_scenes"]

        # 为每个场景创建复选框
        for i, scene in enumerate(self.scene_types):
            var = tk.BooleanVar(value=scene in selected_scenes)
            self.scene_checkbox_vars[scene] = var

            checkbox = ttk.Checkbutton(
                self.scrollable_frame,
                text=scene,
                variable=var,
                command=self._on_scene_checkbox_change,
                style="TCheckbutton",
            )
            checkbox.grid(row=i, column=0, sticky="w", padx=15, pady=8)

        # 如果没有场景，显示提示
        if not self.scene_types:
            ttk.Label(
                self.scrollable_frame,
                text="暂无场景，请点击'新建场景'添加",
                foreground="gray",
                font=self.fonts["small"],
            ).grid(row=0, column=0, padx=15, pady=20)

    def _on_scene_checkbox_change(self) -> None:
        """场景复选框状态改变时的回调"""
        # 更新选中的场景列表
        selected = [
            scene for scene, var in self.scene_checkbox_vars.items() if var.get()
        ]
        self.app_config["scene"]["selected_scenes"] = selected

        # 更新 scene_type 为第一个选中的场景（保持向后兼容）
        if selected:
            self.app_config["scene"]["scene_type"] = selected[0]
        else:
            # 如果没有选中任何场景，保持原值或设为空
            if self.scene_types:
                self.app_config["scene"]["scene_type"] = self.scene_types[0]

    def show_page(self, page_name: str) -> None:
        """
        显示指定的设置页面

        Args:
            page_name: 页面名称 ('video', 'scene')
        """
        # 隐藏当前页面
        if self.current_page and self.current_page in self.content_frames:
            self.content_frames[self.current_page].grid_forget()

        # 显示新页面
        if page_name in self.content_frames:
            self.content_frames[page_name].grid(row=0, column=0, sticky="nsew")
            self.current_page = page_name

            # 更新导航按钮状态（可选：添加视觉反馈）
            # 这里可以通过修改按钮样式来高亮当前选中的按钮

    # ========== 回调函数 ==========

    def _on_scene_change(self, event=None) -> None:
        """场景类型改变时的回调"""
        scene = self.scene_type_var.get()
        print(f"切换到场景: {scene}")
        # TODO: 根据场景类型加载预设参数

    def _create_new_scene(self) -> None:
        """创建新场景 - 使用Gemini AI生成配置"""
        # 创建对话框窗口
        dialog = tk.Toplevel(self.parent)
        dialog.title("新建场景")
        dialog.resizable(False, False)

        # 设置窗口大小为父窗口的50%并居中显示
        dialog_width = int(self.parent.winfo_width() * 0.5)
        dialog_height = int(self.parent.winfo_height() * 0.5)
        self._center_window(dialog, dialog_width, dialog_height)

        # 设置为模态窗口
        dialog.transient(self.parent)
        dialog.grab_set()

        # 创建输入框架 - 增加边距
        input_frame = ttk.Frame(dialog, padding=40)
        input_frame.pack(fill=tk.BOTH, expand=True)

        # 说明标签
        ttk.Label(
            input_frame, text="请输入新场景的名称：", font=self.fonts["title"]
        ).pack(pady=(10, 25))

        # 场景名称输入框
        scene_name_var = tk.StringVar()
        name_entry = ttk.Entry(
            input_frame, textvariable=scene_name_var, font=self.fonts["title"], width=30
        )
        name_entry.pack(pady=(0, 20), ipady=5)
        name_entry.focus()

        # 提示文字
        ttk.Label(
            input_frame,
            text="例如：跌倒、起火、闯入等",
            font=self.fonts["small"],
            foreground="gray",
        ).pack(pady=(0, 35))

        # 状态标签（用于显示生成中状态）
        status_label = ttk.Label(
            input_frame,
            text="",
            font=self.fonts["small"],
            foreground="blue",
        )
        status_label.pack(pady=(0, 15))

        # 按钮框架（居中）
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(pady=(15, 0))

        confirm_btn = ttk.Button(
            button_frame, text="✓ 确定", width=12, style="Action.TButton"
        )
        confirm_btn.pack(side=tk.LEFT, padx=15)

        cancel_btn = ttk.Button(
            button_frame, text="✕ 取消", width=12, style="Action.TButton"
        )
        cancel_btn.pack(side=tk.LEFT, padx=15)

        def on_timeout():
            """超时时的回调"""
            dialog.destroy()  # 关闭新建场景窗口
            messagebox.showwarning(
                "AI 生成超时",
                "DeepSeek AI 服务响应超时，可能原因：\n\n"
                "• 网络连接较慢或不稳定\n"
                "• API 服务响应延迟\n\n"
                "建议：\n"
                "1. 检查网络连接\n"
                "2. 稍后重试\n"
                "3. 系统已为您创建默认配置",
                parent=self.parent,
            )

        def on_confirm():
            """确认创建 - 使用DeepSeek AI生成配置"""
            scene_name = scene_name_var.get().strip()

            if not scene_name:
                messagebox.showwarning("输入错误", "场景名称不能为空", parent=dialog)
                return

            if scene_name in self.scene_types:
                messagebox.showwarning(
                    "场景已存在",
                    f"场景 '{scene_name}' 已经存在，请使用其他名称",
                    parent=dialog,
                )
                return

            # 检查 ConfigUpdater 是否可用
            if self._config_updater is None:
                messagebox.showerror(
                    "配置错误",
                    "配置更新器不可用，请检查配置文件是否存在",
                    parent=dialog,
                )
                return

            # 禁用按钮，显示加载状态
            confirm_btn.config(state=tk.DISABLED)
            cancel_btn.config(state=tk.DISABLED)
            name_entry.config(state=tk.DISABLED)
            
            # 根据 AI 可用性显示不同提示
            if self._config_updater.is_ai_available():
                status_label.config(text="🤖 AI正在生成场景配置，请稍候...")
            else:
                status_label.config(text="⚙️ 正在生成默认配置...")
            dialog.update()

            def generate_scene_config():
                """在后台线程中生成场景配置"""
                import time

                timeout_seconds = 35  # 稍长于 ConfigUpdater 的超时时间
                start_time = time.time()

                try:
                    # 复用已初始化的 config_updater
                    config_updater = self._config_updater

                    # 获取当前场景数量（用于计算阈值）
                    current_config = config_updater.load_current_config()
                    current_scenario_count = len(current_config.get("scenarios", {}))

                    # 使用 AI 生成场景配置（传入当前场景数）
                    scene_config = config_updater.generate_scene_with_ai(
                        scene_name, total_scenarios=current_scenario_count
                    )

                    # 检查是否超时
                    elapsed = time.time() - start_time
                    if scene_config is None and elapsed > timeout_seconds * 0.8:
                        # 超时情况：显示提示框并关闭窗口
                        dialog.after(0, lambda: on_timeout())
                        return

                    if scene_config is None:
                        # AI 失败或不可用，使用默认配置
                        scene_config = config_updater._generate_default_scene_config(
                            scene_name, total_scenarios=current_scenario_count
                        )

                    # 生成场景key（已内置 fallback 到拼音）
                    scene_key = config_updater.generate_scene_key_with_ai(scene_name)

                    # 确保enabled为True（新创建的场景默认启用）
                    scene_config["enabled"] = True
                    
                    # 获取场景显示名称
                    display_name = scene_config.get("name", scene_name)

                    # 直接添加到配置文件（会自动重新计算所有阈值）
                    success = config_updater.add_new_scenario(scene_key, scene_config)

                    # 回到主线程更新UI
                    dialog.after(
                        0,
                        lambda: on_generation_complete(success, display_name, scene_key),
                    )

                except Exception as e:
                    print(f"生成场景配置时出错: {e}")
                    dialog.after(0, lambda: on_generation_error(str(e)))

            def on_generation_complete(success: bool, scene_name: str, scene_key: str):
                """生成完成后的回调"""
                if success:
                    # 添加到场景列表
                    self.scene_types.append(scene_name)

                    # 重新创建复选框列表（这会创建新的 scene_checkbox_vars）
                    self._create_scene_checkboxes()

                    # 自动勾选新创建的场景
                    if (
                        hasattr(self, "scene_checkbox_vars")
                        and scene_name in self.scene_checkbox_vars
                    ):
                        self.scene_checkbox_vars[scene_name].set(True)

                    # 通知场景变化（触发配置更新）
                    self._on_scene_checkbox_change()
                    
                    # 通知外部组件（如检测器）进行热重载
                    self._notify_scenarios_changed()

                    messagebox.showinfo(
                        "创建成功",
                        f"场景 '{scene_name}' 已成功创建\n配置已自动生成并保存",
                        parent=dialog,
                    )
                    dialog.destroy()
                else:
                    status_label.config(text="❌ 配置保存失败", foreground="red")
                    confirm_btn.config(state=tk.NORMAL)
                    cancel_btn.config(state=tk.NORMAL)
                    name_entry.config(state=tk.NORMAL)

            def on_generation_error(error_msg: str):
                """生成出错时的回调"""
                status_label.config(text=f"❌ 生成失败: {error_msg}", foreground="red")
                confirm_btn.config(state=tk.NORMAL)
                cancel_btn.config(state=tk.NORMAL)
                name_entry.config(state=tk.NORMAL)

            # 在后台线程中执行生成
            thread = threading.Thread(target=generate_scene_config, daemon=True)
            thread.start()

        def on_cancel():
            """取消创建"""
            dialog.destroy()

        # 绑定按钮命令
        confirm_btn.config(command=on_confirm)
        cancel_btn.config(command=on_cancel)

        # 绑定回车键
        name_entry.bind("<Return>", lambda e: on_confirm())
        dialog.bind("<Escape>", lambda e: on_cancel())

        # 等待对话框关闭
        dialog.wait_window()

    def _delete_selected_scenes(self) -> None:
        """删除选中的场景"""
        # 获取当前选中的场景
        selected_scenes = [
            scene for scene, var in self.scene_checkbox_vars.items() if var.get()
        ]

        if not selected_scenes:
            messagebox.showwarning("未选择场景", "请先勾选要删除的场景")
            return

        # 检查是否包含内置场景（使用统一的 PROTECTED_SCENE_NAMES 常量）
        builtin_selected = [s for s in selected_scenes if s in PROTECTED_SCENE_NAMES]

        if builtin_selected:
            messagebox.showwarning(
                "无法删除",
                f"以下场景是内置场景，无法删除：\n{', '.join(builtin_selected)}\n\n内置场景包括：跌倒检测、火灾检测、正常场景",
            )
            return

        # 确认删除
        scene_list = "\n".join(f"• {s}" for s in selected_scenes)
        result = messagebox.askyesno(
            "确认删除",
            f"确定要删除以下场景吗？\n\n{scene_list}\n\n此操作将同时删除配置文件中的场景配置，无法撤销。",
        )

        if result:
            # 检查 ConfigUpdater 是否可用
            if self._config_updater is None:
                messagebox.showerror(
                    "配置错误",
                    "配置更新器不可用，请检查配置文件是否存在",
                )
                return
            
            # 从配置文件中删除场景
            try:
                # 复用已初始化的 config_updater
                success = self._config_updater.delete_scenarios_by_names(selected_scenes)

                if not success:
                    messagebox.showerror(
                        "删除失败",
                        "配置文件删除失败，请查看控制台输出",
                    )
                    return

            except Exception as e:
                messagebox.showerror(
                    "删除失败",
                    f"删除配置文件时出错：\n{str(e)}",
                )
                print(f"删除场景配置失败: {e}")
                import traceback

                traceback.print_exc()
                return

            # 从列表中移除选中的场景
            for scene in selected_scenes:
                if scene in self.scene_types:
                    self.scene_types.remove(scene)

            # 从已选中列表中移除
            current_selected = self.app_config["scene"]["selected_scenes"]
            self.app_config["scene"]["selected_scenes"] = [
                s for s in current_selected if s not in selected_scenes
            ]

            # 重新创建复选框
            self._create_scene_checkboxes()
            
            # 触发场景变化回调（通知配置更新）
            self._on_scene_checkbox_change()
            
            # 通知外部组件（如检测器）进行热重载
            self._notify_scenarios_changed()

            messagebox.showinfo(
                "删除成功",
                f"已成功删除 {len(selected_scenes)} 个场景\n配置文件已同步更新",
            )

    def _toggle_roi(self) -> None:
        """切换ROI启用状态"""
        enabled = self.enable_roi_var.get()
        print(f"ROI {'启用' if enabled else '禁用'}")

    def _set_roi_area(self) -> None:
        """设置ROI区域"""
        messagebox.showinfo(
            "设置ROI", "ROI区域设置功能待实现\n将打开视频预览窗口进行区域选择"
        )
        # TODO: 实现ROI区域选择界面

    def _save_scene_config(self) -> None:
        """保存场景配置"""
        # 更新选中的场景列表
        selected = [
            scene for scene, var in self.scene_checkbox_vars.items() if var.get()
        ]
        self.app_config["scene"]["selected_scenes"] = selected

        # 更新 scene_type（保持向后兼容，取第一个选中的场景）
        if selected:
            self.app_config["scene"]["scene_type"] = selected[0]

        # 更新其他配置
        self.app_config["scene"]["light_condition"] = self.light_condition_var.get()
        self.app_config["scene"]["enable_roi"] = self.enable_roi_var.get()
        self.app_config["scene"]["enable_sound"] = self.enable_sound_var.get()
        self.app_config["scene"]["enable_email"] = self.enable_email_var.get()
        self.app_config["scene"]["auto_record"] = self.auto_record_var.get()

        scene_info = f"已选场景: {', '.join(selected) if selected else '无'}"
        messagebox.showinfo("保存成功", f"场景配置已保存\n\n{scene_info}")
        print(f"场景配置已保存到app_config: {self.app_config['scene']}")

    # ========== 对外公开接口 ==========

    def get_current_scene_type(self) -> str:
        """
        获取当前选中的场景类型（第一个选中的场景，用于向后兼容）

        Returns:
            str: 场景类型名称（如 "摔倒"、"起火"等）

        Example:
            >>> panel = SettingsPanel(root)
            >>> scene = panel.get_current_scene_type()
            >>> print(scene)  # "摔倒"

        Note:
            如果用户选择了多个场景，此方法返回第一个选中的场景。
            建议使用 get_selected_scenes() 获取所有选中的场景。
        """
        selected = self.app_config["scene"]["selected_scenes"]
        if selected:
            return selected[0]
        # 如果没有选中任何场景，返回第一个可用场景
        return self.scene_types[0] if self.scene_types else ""

    def get_selected_scenes(self) -> list[str]:
        """
        获取所有选中的场景列表（新接口，推荐使用）

        Returns:
            list[str]: 用户选中的所有场景类型列表

        Example:
            >>> panel = SettingsPanel(root)
            >>> scenes = panel.get_selected_scenes()
            >>> print(scenes)  # ["摔倒", "起火", "闯入"]
            >>> for scene in scenes:
            ...     prompts = get_prompts_for_scene(scene)
            ...     detect(frame, prompts)
        """
        return self.app_config["scene"]["selected_scenes"].copy()

    def get_all_scene_types(self) -> list[str]:
        """
        获取所有可用的场景类型列表

        Returns:
            list[str]: 场景类型列表，包含内置场景和用户自定义场景

        Example:
            >>> panel = SettingsPanel(root)
            >>> scenes = panel.get_all_scene_types()
            >>> print(scenes)  # ["摔倒", "起火", "闯入"]
        """
        return self.scene_types.copy()

    def get_scene_config(self) -> Dict:
        """
        获取当前场景的完整配置

        Returns:
            Dict: 包含所有场景参数的字典

        Dictionary Structure:
            {
                "scene_type": str,              # 第一个选中的场景（向后兼容）
                "selected_scenes": list[str],   # 所有选中的场景列表（新增）
                "light_condition": str,         # 光照条件：'bright' | 'normal' | 'dim'
                "enable_roi": bool,             # 是否启用ROI
                "enable_sound": bool,           # 是否启用声音报警
                "enable_email": bool,           # 是否启用短信通知
                "auto_record": bool,            # 是否自动录像
            }

        Example:
            >>> panel = SettingsPanel(root)
            >>> config = panel.get_scene_config()
            >>> print(config["scene_type"])        # "摔倒"（第一个）
            >>> print(config["selected_scenes"])   # ["摔倒", "起火"]（所有）
            >>> print(config["light_condition"])   # "normal"
            >>> print(config["enable_roi"])        # False
        """
        selected = self.app_config["scene"]["selected_scenes"]
        return {
            "scene_type": (
                selected[0]
                if selected
                else (self.scene_types[0] if self.scene_types else "")
            ),
            "selected_scenes": selected.copy(),
            "light_condition": self.light_condition_var.get(),
            "enable_roi": self.enable_roi_var.get(),
            "enable_sound": self.enable_sound_var.get(),
            "enable_email": self.enable_email_var.get(),
            "auto_record": self.auto_record_var.get(),
        }

    def get_light_condition(self) -> str:
        """
        获取当前光照条件设置

        Returns:
            str: 光照条件，可能的值: 'bright'（明亮）、'normal'（正常）、'dim'（昏暗）

        Example:
            >>> panel = SettingsPanel(root)
            >>> light = panel.get_light_condition()
            >>> if light == "dim":
            ...     # 调整检测算法的灵敏度
        """
        return self.light_condition_var.get()

    def get_roi_settings(self) -> Dict:
        """
        获取ROI（感兴趣区域）相关设置

        Returns:
            Dict: ROI设置字典

        Dictionary Structure:
            {
                "enabled": bool,     # 是否启用ROI
                "coordinates": None  # ROI坐标（待实现，目前为None）
            }

        Example:
            >>> panel = SettingsPanel(root)
            >>> roi = panel.get_roi_settings()
            >>> if roi["enabled"]:
            ...     # 只在ROI区域内进行检测
            ...     coords = roi["coordinates"]
        """
        return {
            "enabled": self.enable_roi_var.get(),
            "coordinates": None,  # TODO: 实现ROI坐标存储
        }

    def get_alert_settings(self) -> Dict:
        """
        获取报警设置

        Returns:
            Dict: 报警设置字典

        Dictionary Structure:
            {
                "sound": bool,    # 是否启用声音报警
                "email": bool,    # 是否启用邮件通知
                "record": bool,   # 是否自动录像
            }

        Example:
            >>> panel = SettingsPanel(root)
            >>> alerts = panel.get_alert_settings()
            >>> if alerts["sound"]:
            ...     play_alert_sound()
            >>> if alerts["email"]:
            ...     send_email_notification()
            >>> if alerts["record"]:
            ...     start_recording()
        """
        return {
            "sound": self.enable_sound_var.get(),
            "email": self.enable_email_var.get(),
            "record": self.auto_record_var.get(),
        }

    def set_scene_type(self, scene_type: str) -> bool:
        """
        以编程方式设置场景类型（供外部调用，向后兼容）

        Args:
            scene_type: 场景类型名称

        Returns:
            bool: 设置成功返回True，场景不存在返回False

        Example:
            >>> panel = SettingsPanel(root)
            >>> success = panel.set_scene_type("起火")
            >>> if success:
            ...     print("场景切换成功")

        Note:
            此方法会将选中场景列表设置为只包含指定场景。
            如需选中多个场景，请使用 set_selected_scenes()。
        """
        if scene_type in self.scene_types:
            # 设置为只选中这一个场景
            self.app_config["scene"]["selected_scenes"] = [scene_type]
            self.app_config["scene"]["scene_type"] = scene_type
            # 更新复选框状态
            if hasattr(self, "scene_checkbox_vars"):
                for scene, var in self.scene_checkbox_vars.items():
                    var.set(scene == scene_type)
            return True
        return False

    def set_selected_scenes(self, scene_list: list[str]) -> bool:
        """
        以编程方式设置选中的多个场景（新接口）

        Args:
            scene_list: 场景类型名称列表

        Returns:
            bool: 设置成功返回True，场景列表为空或包含不存在的场景返回False

        Example:
            >>> panel = SettingsPanel(root)
            >>> success = panel.set_selected_scenes(["摔倒", "起火", "闯入"])
            >>> if success:
            ...     print("场景选择成功")
            ...     scenes = panel.get_selected_scenes()
            ...     print(f"已选场景: {scenes}")
        """
        if not scene_list:
            return False

        # 检查所有场景是否存在
        for scene in scene_list:
            if scene not in self.scene_types:
                return False

        # 更新配置
        self.app_config["scene"]["selected_scenes"] = scene_list.copy()
        self.app_config["scene"]["scene_type"] = scene_list[0]

        # 更新复选框状态
        if hasattr(self, "scene_checkbox_vars"):
            for scene, var in self.scene_checkbox_vars.items():
                var.set(scene in scene_list)

        return True

    def add_scene_type(self, scene_name: str) -> bool:
        """
        以编程方式添加新的场景类型（供外部调用）

        Args:
            scene_name: 新场景的名称

        Returns:
            bool: 添加成功返回True，场景已存在或名称为空返回False

        Example:
            >>> panel = SettingsPanel(root)
            >>> success = panel.add_scene_type("闯入")
            >>> if success:
            ...     print(f"已添加场景: 闯入")
            ...     panel.set_scene_type("闯入")
        """
        scene_name = scene_name.strip()

        if not scene_name or scene_name in self.scene_types:
            return False

        # 添加到场景列表
        self.scene_types.append(scene_name)

        # 更新复选框列表（如果已创建）
        if hasattr(self, "scrollable_frame"):
            self._create_scene_checkboxes()

        return True

    def update_scene_config(self, config: Dict) -> None:
        """
        以编程方式更新场景配置（供外部调用）

        Args:
            config: 配置字典，可以包含以下任意键：
                - scene_type: str（单个场景，向后兼容）
                - selected_scenes: list[str]（多个场景，新增）
                - light_condition: str ('bright' | 'normal' | 'dim')
                - enable_roi: bool
                - enable_sound: bool
                - enable_email: bool
                - auto_record: bool

        Example:
            >>> panel = SettingsPanel(root)
            >>> # 方式1：单场景（向后兼容）
            >>> panel.update_scene_config({
            ...     "scene_type": "起火",
            ...     "light_condition": "bright",
            ...     "enable_sound": True
            ... })
            >>>
            >>> # 方式2：多场景（推荐）
            >>> panel.update_scene_config({
            ...     "selected_scenes": ["摔倒", "起火", "闯入"],
            ...     "light_condition": "normal",
            ...     "enable_email": True
            ... })
        """
        # 处理多场景选择（优先）
        if "selected_scenes" in config:
            scene_list = config["selected_scenes"]
            if isinstance(scene_list, list) and scene_list:
                valid_scenes = [s for s in scene_list if s in self.scene_types]
                if valid_scenes:
                    self.app_config["scene"]["selected_scenes"] = valid_scenes
                    self.app_config["scene"]["scene_type"] = valid_scenes[0]
                    # 更新复选框
                    if hasattr(self, "scene_checkbox_vars"):
                        for scene, var in self.scene_checkbox_vars.items():
                            var.set(scene in valid_scenes)

        # 处理单场景选择（向后兼容）
        elif "scene_type" in config and config["scene_type"] in self.scene_types:
            scene = config["scene_type"]
            self.app_config["scene"]["selected_scenes"] = [scene]
            self.app_config["scene"]["scene_type"] = scene
            # 更新复选框
            if hasattr(self, "scene_checkbox_vars"):
                for s, var in self.scene_checkbox_vars.items():
                    var.set(s == scene)

        if "light_condition" in config:
            self.light_condition_var.set(config["light_condition"])

        if "enable_roi" in config:
            self.enable_roi_var.set(config["enable_roi"])

        if "enable_sound" in config:
            self.enable_sound_var.set(config["enable_sound"])

        if "enable_email" in config:
            self.enable_email_var.set(config["enable_email"])

        if "auto_record" in config:
            self.auto_record_var.set(config["auto_record"])

    # ========== 配置监听接口 ==========

    def get_config_snapshot(self) -> Dict:
        """
        获取当前配置的完整快照

        Returns:
            Dict: 包含所有配置参数的字典快照

        Dictionary Structure:
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

        Example:
            >>> panel = SettingsPanel(root)
            >>> snapshot = panel.get_config_snapshot()
            >>> print(snapshot["selected_scenes"])  # ["摔倒", "起火"]
        """
        selected = self.app_config["scene"]["selected_scenes"]
        scene_config = self.app_config["scene"]

        return {
            "scene_type": (
                selected[0]
                if selected
                else (self.scene_types[0] if self.scene_types else "")
            ),
            "selected_scenes": selected.copy(),
            "confidence_threshold": scene_config.get("confidence_threshold"),
            "detection_interval": scene_config.get("detection_interval"),
            "camera_id": scene_config.get("camera_id"),
            "alert_delay": scene_config.get("alert_delay"),
            "light_condition": self.light_condition_var.get(),
            "enable_roi": self.enable_roi_var.get(),
            "enable_sound": self.enable_sound_var.get(),
            "enable_email": self.enable_email_var.get(),
            "auto_record": self.auto_record_var.get(),
        }

    def start_config_monitor(
        self,
        callback,
        interval: int = 500,
        print_changes: bool = True,
        print_full_config: bool = True,
    ) -> None:
        """
        启动配置监听器，当配置发生变化时自动调用回调函数

        Args:
            callback: 回调函数，签名为 callback(old_config: Dict, new_config: Dict)
            interval: 检查间隔（毫秒），默认500ms
            print_changes: 是否自动打印配置变化，默认True
            print_full_config: 是否在变化时打印完整配置，默认True

        Example:
            >>> def on_config_change(old_config, new_config):
            ...     print("配置已更新！")
            ...     # 处理配置变化
            ...     if old_config["scene_type"] != new_config["scene_type"]:
            ...         reload_detection_model(new_config["scene_type"])
            >>>
            >>> panel = SettingsPanel(root)
            >>> panel.start_config_monitor(on_config_change)
            >>> # 现在配置变化时会自动调用 on_config_change

        Note:
            - 监听器会在后台持续运行，直到窗口关闭
            - 回调函数会在Tkinter主线程中执行
            - 如果回调函数抛出异常，监听器会继续运行
        """
        # 保存初始配置
        self._last_config = self.get_config_snapshot()
        self._monitor_callback = callback
        self._monitor_interval = interval
        self._monitor_print_changes = print_changes
        self._monitor_print_full_config = print_full_config

        # 启动监听
        self._check_config_changes()

    def _check_config_changes(self) -> None:
        """内部方法：定期检查配置变化"""
        try:
            current_config = self.get_config_snapshot()

            # 检查是否有变化
            if current_config != self._last_config:
                # 打印变化信息（如果启用）
                if self._monitor_print_changes:
                    self._print_config_diff(self._last_config, current_config)

                # 打印完整配置（如果启用）
                if self._monitor_print_full_config:
                    self._print_config()

                # 调用用户回调
                try:
                    self._monitor_callback(self._last_config, current_config)
                except Exception as e:
                    print(f"❌ 配置监听回调函数出错: {e}")

                # 更新上次配置
                self._last_config = current_config.copy()

            # 继续监听
            self.parent.after(self._monitor_interval, self._check_config_changes)
        except Exception as e:
            print(f"❌ 配置监听出错: {e}")
            # 即使出错也继续监听
            self.parent.after(self._monitor_interval, self._check_config_changes)

    def _print_config_diff(self, old_config: Dict, new_config: Dict) -> None:
        """内部方法：打印配置变化的简洁信息"""
        # 检查选中场景列表变化
        old_scenes = set(old_config.get("selected_scenes", []))
        new_scenes = set(new_config.get("selected_scenes", []))
        
        if old_scenes != new_scenes:
            added = new_scenes - old_scenes
            removed = old_scenes - new_scenes
            if added:
                print(f"  ✅ 启用: {', '.join(added)}")
            if removed:
                print(f"  ❌ 禁用: {', '.join(removed)}")

    def _print_config(self) -> None:
        """内部方法：打印完整的配置信息"""
        print("\n" + "=" * 60)
        print("📋 当前配置信息:")
        print("=" * 60)

        # 场景配置
        selected = self.app_config["scene"]["selected_scenes"]
        print(f"🎯 当前场景类型: {selected[0] if selected else '无'}")
        print(f"📌 所有选中场景: {', '.join(selected) if selected else '无'}")

        # 其他配置信息
        scene_config = self.app_config["scene"]
        print(f"\n⚙️  配置参数:")
        print(f"   • 置信度阈值: {scene_config.get('confidence_threshold', 'N/A')}")
        print(f"   • 检测间隔: {scene_config.get('detection_interval', 'N/A')} 秒")
        print(f"   • 摄像头ID: {scene_config.get('camera_id', 'N/A')}")
        print(f"   • 告警延迟: {scene_config.get('alert_delay', 'N/A')} 秒")

        # 场景参数
        print(f"\n🎨 场景参数:")
        print(f"   • 光照条件: {scene_config.get('light_condition', 'N/A')}")
        print(f"   • 启用ROI: {'是' if scene_config.get('enable_roi') else '否'}")
        print(f"   • 声音报警: {'是' if scene_config.get('enable_sound') else '否'}")
        print(f"   • 邮件通知: {'是' if scene_config.get('enable_email') else '否'}")
        print(f"   • 自动录像: {'是' if scene_config.get('auto_record') else '否'}")
        print("=" * 60 + "\n")

    def print_current_config(self) -> None:
        """
        手动打印当前配置信息（公共接口）

        Example:
            >>> panel = SettingsPanel(root)
            >>> panel.print_current_config()
            📋 当前配置信息:
            🎯 当前场景类型: 摔倒
            ...
        """
        self._print_config()

    def stop_config_monitor(self) -> None:
        """
        停止配置监听器

        Example:
            >>> panel = SettingsPanel(root)
            >>> panel.start_config_monitor(callback)
            >>> # ... 一段时间后 ...
            >>> panel.stop_config_monitor()  # 停止监听
        """
        # 通过设置一个标志来停止监听
        if hasattr(self, "_monitor_callback"):
            self._monitor_callback = None

    def _on_window_resize(self, event: tk.Event) -> None:
        """窗口缩放事件处理器，保持窗口宽高比 (3:2)"""
        if event.widget is not self.parent or self._resize_state["lock"]:
            return

        # 等待窗口完全初始化后再开始调整
        if not self._resize_state["initialized"]:
            self.parent.after(
                100, lambda: self._resize_state.update({"initialized": True})
            )
            return

        new_width, new_height = event.width, event.height
        if new_width <= 0 or new_height <= 0:
            return

        # 避免重复调整相同尺寸
        if (
            new_width == self._resize_state["width"]
            and new_height == self._resize_state["height"]
        ):
            return

        # 计算目标尺寸
        desired_height = int(new_width / self.aspect_ratio)
        desired_width = int(new_height * self.aspect_ratio)

        # 根据拉伸方向决定基准 (宽度或高度哪个变化更大)
        width_delta = abs(new_width - self._resize_state["width"])
        height_delta = abs(new_height - self._resize_state["height"])

        if width_delta >= height_delta:
            # 以宽度为基准
            target_width = max(1000, new_width)  # 最小宽度 1000px
            target_height = max(666, desired_height)  # 最小高度 666px (保持3:2比例)
        else:
            # 以高度为基准
            target_height = max(666, new_height)  # 最小高度 666px
            target_width = max(1000, desired_width)  # 最小宽度 1000px

        # 更新窗口尺寸
        self._resize_state["lock"] = True
        self.parent.geometry(f"{target_width}x{target_height}")
        self._resize_state["lock"] = False

        # 更新状态
        self._resize_state["width"] = target_width
        self._resize_state["height"] = target_height


def main() -> None:
    """测试设置面板"""
    root = tk.Tk()
    root.title("DLC检测系统 - 设置")
    root.geometry("1000x666")  # 最小尺寸,保持3:2比例

    # 创建设置面板
    panel = SettingsPanel(root)

    root.mainloop()


if __name__ == "__main__":
    main()
