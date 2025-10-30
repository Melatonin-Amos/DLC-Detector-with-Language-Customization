# TODO: 设置面板（拓展功能）
#
# 功能说明：
# 1. 提供场景配置界面
# 2. RTSP流配置
# 3. 阈值调整（不给用户）
#
# 主要类：
# - SettingsPanel: 设置面板类
#
# 开发优先级：⭐ (第10-11周完成)

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional, Union


class SettingsPanel:
    """设置面板类 - 左侧导航右侧内容的双栏布局"""

    def __init__(self, parent: Union[tk.Tk, tk.Toplevel]) -> None:
        """
        初始化设置面板

        Args:
            parent: 父窗口
        """
        self.parent = parent
        self.current_page: Optional[str] = None
        self.content_frames: Dict[str, ttk.Frame] = {}

        # 场景类型列表（可动态添加）
        self.scene_types: list[str] = ["摔倒", "起火"]

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

        # 默认显示第一个页面
        self.show_page("rtsp")

        # 绑定窗口缩放事件
        self.parent.bind("<Configure>", self._on_window_resize)

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
        # 导航栏框架
        nav_frame = ttk.LabelFrame(self.main_container, text="设置选项", padding="10")
        nav_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # 导航按钮样式配置
        button_style = {"width": 20, "padding": 10}

        # 1. RTSP流配置按钮
        self.btn_rtsp = ttk.Button(
            nav_frame,
            text="📡 RTSP流配置",
            command=lambda: self.show_page("rtsp"),
            **button_style,
        )
        self.btn_rtsp.pack(fill=tk.X, pady=(0, 10))

        # 2. 场景配置按钮
        self.btn_scene = ttk.Button(
            nav_frame,
            text="🎬 场景配置",
            command=lambda: self.show_page("scene"),
            **button_style,
        )
        self.btn_scene.pack(fill=tk.X, pady=(0, 10))

        # 保存按钮列表以便高亮显示
        self.nav_buttons = {
            "rtsp": self.btn_rtsp,
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
        # 创建RTSP流配置页面
        self.content_frames["rtsp"] = self._create_rtsp_page()

        # 创建场景配置页面
        self.content_frames["scene"] = self._create_scene_page()

    def _create_rtsp_page(self) -> ttk.Frame:
        """创建RTSP流配置页面"""
        frame = ttk.LabelFrame(
            self.content_container, text="📡 RTSP流配置", padding="20"
        )

        # 说明文字
        desc_label = ttk.Label(
            frame,
            text="配置视频流的RTSP连接参数",
            font=("Arial", 10, "italic"),
            foreground="gray",
        )
        desc_label.pack(anchor="w", pady=(0, 20))

        # RTSP URL输入
        url_frame = ttk.Frame(frame)
        url_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(url_frame, text="RTSP URL:", width=15).pack(side=tk.LEFT)
        self.rtsp_url_var = tk.StringVar(value="rtsp://")
        rtsp_entry = ttk.Entry(url_frame, textvariable=self.rtsp_url_var, width=50)
        rtsp_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # 用户名输入
        user_frame = ttk.Frame(frame)
        user_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(user_frame, text="用户名:", width=15).pack(side=tk.LEFT)
        self.rtsp_user_var = tk.StringVar()
        user_entry = ttk.Entry(user_frame, textvariable=self.rtsp_user_var, width=30)
        user_entry.pack(side=tk.LEFT, padx=(5, 0))

        # 密码输入
        pass_frame = ttk.Frame(frame)
        pass_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(pass_frame, text="密码:", width=15).pack(side=tk.LEFT)
        self.rtsp_pass_var = tk.StringVar()
        pass_entry = ttk.Entry(
            pass_frame, textvariable=self.rtsp_pass_var, show="*", width=30
        )
        pass_entry.pack(side=tk.LEFT, padx=(5, 0))

        # 端口号输入
        port_frame = ttk.Frame(frame)
        port_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(port_frame, text="端口号:", width=15).pack(side=tk.LEFT)
        self.rtsp_port_var = tk.StringVar(value="554")
        port_entry = ttk.Entry(port_frame, textvariable=self.rtsp_port_var, width=10)
        port_entry.pack(side=tk.LEFT, padx=(5, 0))

        # 超时设置
        timeout_frame = ttk.Frame(frame)
        timeout_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(timeout_frame, text="连接超时(秒):", width=15).pack(side=tk.LEFT)
        self.rtsp_timeout_var = tk.IntVar(value=10)
        timeout_spinbox = ttk.Spinbox(
            timeout_frame,
            from_=5,
            to=60,
            textvariable=self.rtsp_timeout_var,
            width=10,
        )
        timeout_spinbox.pack(side=tk.LEFT, padx=(5, 0))

        # 按钮区域
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            button_frame, text="测试连接", command=self._test_rtsp_connection
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(button_frame, text="保存配置", command=self._save_rtsp_config).pack(
            side=tk.LEFT
        )

        return frame

    def _create_scene_page(self) -> ttk.Frame:
        """创建场景配置页面"""
        frame = ttk.LabelFrame(self.content_container, text="🎬 场景配置", padding="20")

        # 说明文字
        desc_label = ttk.Label(
            frame,
            text="配置不同检测场景的参数",
            font=("Arial", 10, "italic"),
            foreground="gray",
        )
        desc_label.pack(anchor="w", pady=(0, 20))

        # 场景选择和新建
        scene_select_frame = ttk.Frame(frame)
        scene_select_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(scene_select_frame, text="场景类型:", width=15).pack(side=tk.LEFT)
        self.scene_type_var = tk.StringVar(value=self.scene_types[0])
        self.scene_combo = ttk.Combobox(
            scene_select_frame,
            textvariable=self.scene_type_var,
            values=self.scene_types,
            state="readonly",
            width=20,
        )
        self.scene_combo.pack(side=tk.LEFT, padx=(5, 10))
        self.scene_combo.bind("<<ComboboxSelected>>", self._on_scene_change)

        # 新建场景按钮
        ttk.Button(
            scene_select_frame,
            text="➕ 新建场景",
            command=self._create_new_scene,
            width=12,
        ).pack(side=tk.LEFT, padx=(0, 10))

        # 删除场景按钮
        ttk.Button(
            scene_select_frame,
            text="删除场景",
            command=self._delete_current_scene,
            width=12,
        ).pack(side=tk.LEFT)

        # 场景参数区域
        params_frame = ttk.LabelFrame(frame, text="场景参数", padding="15")
        params_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # 光照条件
        light_frame = ttk.Frame(params_frame)
        light_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(light_frame, text="光照条件:", width=15).pack(side=tk.LEFT)
        self.light_condition_var = tk.StringVar(value="normal")
        ttk.Radiobutton(
            light_frame, text="明亮", variable=self.light_condition_var, value="bright"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            light_frame, text="正常", variable=self.light_condition_var, value="normal"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            light_frame, text="昏暗", variable=self.light_condition_var, value="dim"
        ).pack(side=tk.LEFT, padx=5)

        # 检测区域
        area_frame = ttk.Frame(params_frame)
        area_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(area_frame, text="检测区域:", width=15).pack(side=tk.LEFT)
        self.enable_roi_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            area_frame,
            text="启用感兴趣区域(ROI)",
            variable=self.enable_roi_var,
            command=self._toggle_roi,
        ).pack(side=tk.LEFT, padx=(5, 0))

        # 报警设置
        alarm_frame = ttk.Frame(params_frame)
        alarm_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(alarm_frame, text="报警设置:", width=15).pack(side=tk.LEFT)
        self.enable_sound_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            alarm_frame, text="声音报警", variable=self.enable_sound_var
        ).pack(side=tk.LEFT, padx=5)

        self.enable_email_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            alarm_frame, text="邮件通知", variable=self.enable_email_var
        ).pack(side=tk.LEFT, padx=5)

        # 录像设置
        record_frame = ttk.Frame(params_frame)
        record_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(record_frame, text="录像设置:", width=15).pack(side=tk.LEFT)
        self.auto_record_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            record_frame, text="事件触发时自动录像", variable=self.auto_record_var
        ).pack(side=tk.LEFT, padx=(5, 0))

        # 按钮区域
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="设置ROI区域", command=self._set_roi_area).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        ttk.Button(
            button_frame, text="保存场景配置", command=self._save_scene_config
        ).pack(side=tk.LEFT)

        return frame

    def show_page(self, page_name: str) -> None:
        """
        显示指定的设置页面

        Args:
            page_name: 页面名称 ('rtsp', 'scene')
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

    def _test_rtsp_connection(self) -> None:
        """测试RTSP连接"""
        url = self.rtsp_url_var.get()
        if not url or url == "rtsp://":
            messagebox.showwarning("警告", "请输入有效的RTSP URL")
            return

        messagebox.showinfo("测试连接", f"正在测试连接: {url}\n(此功能待实现)")
        # TODO: 实现实际的RTSP连接测试

    def _save_rtsp_config(self) -> None:
        """保存RTSP配置"""
        config = {
            "url": self.rtsp_url_var.get(),
            "username": self.rtsp_user_var.get(),
            "password": self.rtsp_pass_var.get(),
            "port": self.rtsp_port_var.get(),
            "timeout": self.rtsp_timeout_var.get(),
        }
        messagebox.showinfo("保存成功", "RTSP配置已保存")
        print(f"RTSP配置: {config}")
        # TODO: 实现配置保存到文件

    def _on_scene_change(self, event=None) -> None:
        """场景类型改变时的回调"""
        scene = self.scene_type_var.get()
        print(f"切换到场景: {scene}")
        # TODO: 根据场景类型加载预设参数

    def _create_new_scene(self) -> None:
        """创建新场景"""
        # 创建对话框窗口
        dialog = tk.Toplevel(self.parent)
        dialog.title("新建场景")
        dialog.resizable(False, False)

        # 设置窗口大小并居中显示
        dialog_width = 480
        dialog_height = 280
        self._center_window(dialog, dialog_width, dialog_height)

        # 设置为模态窗口
        dialog.transient(self.parent)
        dialog.grab_set()

        # 创建输入框架
        input_frame = ttk.Frame(dialog, padding="30")
        input_frame.pack(fill=tk.BOTH, expand=True)

        # 说明标签
        ttk.Label(
            input_frame, text="请输入新场景的名称：", font=("Arial", 12, "bold")
        ).pack(pady=(10, 20))

        # 场景名称输入框
        scene_name_var = tk.StringVar()
        name_entry = ttk.Entry(
            input_frame, textvariable=scene_name_var, font=("Arial", 12), width=30
        )
        name_entry.pack(pady=(0, 20))
        name_entry.focus()

        # 提示文字
        ttk.Label(
            input_frame,
            text="例如：跌倒、起火、闯入等",
            font=("Arial", 9),
            foreground="gray",
        ).pack(pady=(0, 30))

        def on_confirm():
            """确认创建"""
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

            # 添加到场景列表
            self.scene_types.append(scene_name)

            # 更新下拉框
            self.scene_combo["values"] = self.scene_types

            # 选中新创建的场景
            self.scene_type_var.set(scene_name)

            messagebox.showinfo(
                "创建成功", f"场景 '{scene_name}' 已成功创建", parent=dialog
            )

            dialog.destroy()

        def on_cancel():
            """取消创建"""
            dialog.destroy()

        # 按钮框架（居中）
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(pady=(10, 0))

        ttk.Button(
            button_frame, text="✓ 确定", command=on_confirm, width=15, padding=8
        ).pack(side=tk.LEFT, padx=10)

        ttk.Button(
            button_frame, text="✕ 取消", command=on_cancel, width=15, padding=8
        ).pack(side=tk.LEFT, padx=10)

        # 绑定回车键
        name_entry.bind("<Return>", lambda e: on_confirm())
        dialog.bind("<Escape>", lambda e: on_cancel())

        # 等待对话框关闭
        dialog.wait_window()

    def _delete_current_scene(self) -> None:
        """删除当前选中的场景"""
        current_scene = self.scene_type_var.get()

        # 检查是否是内置场景
        builtin_scenes = ["摔倒", "起火"]
        if current_scene in builtin_scenes:
            messagebox.showwarning(
                "无法删除", f"'{current_scene}' 是内置场景，无法删除"
            )
            return

        # 确认删除
        result = messagebox.askyesno(
            "确认删除", f"确定要删除场景 '{current_scene}' 吗？\n此操作无法撤销。"
        )

        if result:
            # 从列表中移除
            self.scene_types.remove(current_scene)

            # 更新下拉框
            self.scene_combo["values"] = self.scene_types

            # 切换到第一个场景
            if self.scene_types:
                self.scene_type_var.set(self.scene_types[0])

            messagebox.showinfo("删除成功", f"场景 '{current_scene}' 已删除")

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
        config = {
            "scene_type": self.scene_type_var.get(),
            "light_condition": self.light_condition_var.get(),
            "enable_roi": self.enable_roi_var.get(),
            "enable_sound": self.enable_sound_var.get(),
            "enable_email": self.enable_email_var.get(),
            "auto_record": self.auto_record_var.get(),
        }
        messagebox.showinfo("保存成功", "场景配置已保存")
        print(f"场景配置: {config}")
        # TODO: 实现配置保存到文件

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
