"""
配置更新工具模块

功能：
- 监听场景选择变化
- 更新 config/detection/default.yaml 的 scenarios 配置
- 使用多种 LLM API（优先 Gemini，备选 DeepSeek）生成规范的场景配置格式

主要类：
- ConfigUpdater: 配置更新器类

支持的 LLM API：
1. Google Gemini（优先）
2. DeepSeek
"""

import yaml
import json
import re
import os
import signal
from pathlib import Path
from typing import List, Dict, Any, Optional

# Gemini API 支持（可选依赖）
try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# DeepSeek API 支持（可选依赖）
try:
    from openai import OpenAI

    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False

# 提示用户安装情况
if not GEMINI_AVAILABLE and not DEEPSEEK_AVAILABLE:
    print("⚠️  未安装任何 LLM API 支持，AI 生成功能不可用")
    print("   推荐安装 Gemini: pip install google-generativeai")
    print("   或安装 DeepSeek: pip install openai")

# 内置场景保护列表（这些场景不能被删除）
PROTECTED_SCENE_KEYS = {"fall", "fire", "normal"}
PROTECTED_SCENE_NAMES = {
    "摔倒",
    "跌倒",
    "跌倒检测",  # fall 的别名
    "起火",
    "火灾",
    "火灾检测",  # fire 的别名
    "正常",
    "正常场景",  # normal 的别名
}


class ConfigUpdater:
    """配置更新器 - 负责根据用户选择的场景更新配置文件"""

    # API 密钥配置
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

    # API 超时时间（秒）
    API_TIMEOUT = 30

    # 当前使用的 API 类型
    current_api: str = None  # "gemini", "deepseek", or None

    def __init__(self, config_path: str = "config/detection/default.yaml"):
        """
        初始化配置更新器

        Args:
            config_path: 配置文件路径（相对于项目根目录）
        """
        # 获取项目根目录
        self.project_root = Path(__file__).parent.parent.parent
        self.config_file = self.project_root / config_path

        # 尝试加载 .env 文件
        self._load_env_file()

        # 确保配置文件存在
        if not self.config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_file}")

        # 初始化 LLM 客户端（优先 Gemini，备选 DeepSeek）
        self.ai_client = None
        self.gemini_model = None
        self._init_llm_client()

        print(f"✓ 配置更新器初始化: {self.config_file}")

    def _load_env_file(self) -> None:
        """手动加载 .env 文件（如果存在）"""
        env_path = self.project_root / ".env"
        if not env_path.exists():
            return

        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        # 去除引号
                        if (value.startswith('"') and value.endswith('"')) or (
                            value.startswith("'") and value.endswith("'")
                        ):
                            value = value[1:-1]

                        if key and value:
                            # 只有当环境变量不存在时才设置，避免覆盖系统环境变量
                            if key not in os.environ:
                                os.environ[key] = value

            # 更新 API 密钥
            self.GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
            self.DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

        except Exception as e:
            print(f"⚠️  加载 .env 文件失败: {e}")

    def _init_llm_client(self) -> None:
        """初始化 LLM 客户端（优先 Gemini，备选 DeepSeek）"""
        # 1. 优先尝试 Gemini
        if GEMINI_AVAILABLE and self.GEMINI_API_KEY:
            try:
                genai.configure(api_key=self.GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel("gemini-3-flash-preview")
                self.current_api = "gemini"
                print("✓ Gemini API 初始化成功（优先使用）")
                return
            except Exception as e:
                print(f"⚠️  Gemini API 初始化失败: {e}")

        # 2. 回退到 DeepSeek
        if DEEPSEEK_AVAILABLE and self.DEEPSEEK_API_KEY:
            try:
                self.ai_client = OpenAI(
                    api_key=self.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com"
                )
                self.current_api = "deepseek"
                print("✓ DeepSeek API 初始化成功（备选）")
                return
            except Exception as e:
                print(f"⚠️  DeepSeek API 初始化失败: {e}")

        # 3. 无可用 API
        print("ℹ️  无可用 LLM API，将使用预定义模板生成配置")
        self.current_api = None

    def _init_deepseek(self) -> None:
        """初始化 DeepSeek API 客户端（兼容旧代码）"""
        if DEEPSEEK_AVAILABLE and self.DEEPSEEK_API_KEY:
            try:
                self.ai_client = OpenAI(
                    api_key=self.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com"
                )
                self.current_api = "deepseek"
                print("✓ DeepSeek API 初始化成功")
            except Exception as e:
                print(f"⚠️  DeepSeek API 初始化失败: {e}")
                self.ai_client = None

    def _call_ai_with_timeout(self, prompt: str, timeout: int = None) -> Optional[str]:
        """
        带超时的 AI API 调用（自动选择可用的 API）

        Args:
            prompt: 提示词
            timeout: 超时时间（秒），默认使用 API_TIMEOUT

        Returns:
            响应文本，超时或失败返回 None
        """
        if timeout is None:
            timeout = self.API_TIMEOUT

        # 根据当前 API 类型选择调用方式
        if self.current_api == "gemini" and self.gemini_model:
            return self._call_gemini_with_timeout(prompt, timeout)
        elif self.current_api == "deepseek" and self.ai_client:
            return self._call_deepseek_with_timeout(prompt, timeout)
        else:
            return None

    def _call_gemini_with_timeout(self, prompt: str, timeout: int) -> Optional[str]:
        """
        带超时的 Gemini API 调用

        Args:
            prompt: 提示词
            timeout: 超时时间（秒）

        Returns:
            响应文本，超时或失败返回 None
        """
        from concurrent.futures import (
            ThreadPoolExecutor,
            TimeoutError as FutureTimeoutError,
        )

        def call_api():
            try:
                response = self.gemini_model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                raise e

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(call_api)
                try:
                    result = future.result(timeout=timeout)
                    return result
                except FutureTimeoutError:
                    print(f"   ⏱️  Gemini API 调用超时 ({timeout}秒)")
                    return None
        except Exception as e:
            self._handle_api_error(e, "Gemini")
            return None

    def _call_deepseek_with_timeout(self, prompt: str, timeout: int) -> Optional[str]:
        """
        带超时的 DeepSeek API 调用

        Args:
            prompt: 提示词
            timeout: 超时时间（秒）

        Returns:
            响应文本，超时或失败返回 None
        """
        from concurrent.futures import (
            ThreadPoolExecutor,
            TimeoutError as FutureTimeoutError,
        )

        def call_api():
            try:
                response = self.ai_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that generates scene detection configurations.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=500,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                raise e

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(call_api)
                try:
                    result = future.result(timeout=timeout)
                    return result
                except FutureTimeoutError:
                    print(f"   ⏱️  DeepSeek API 调用超时 ({timeout}秒)")
                    return None
        except Exception as e:
            self._handle_api_error(e, "DeepSeek")
            return None

    def _handle_api_error(self, e: Exception, api_name: str) -> None:
        """处理 API 错误信息"""
        error_msg = str(e).lower()
        if "timeout" in error_msg or "timed out" in error_msg:
            print(f"   ⏱️  {api_name} API 调用超时")
        elif "429" in error_msg or "quota" in error_msg:
            print(f"   ⚠️  {api_name} API 配额已用尽或请求频率过高")
        elif "403" in error_msg or "401" in error_msg:
            print(f"   ⚠️  {api_name} API 密钥无效或权限不足")
        elif "network" in error_msg or "connection" in error_msg:
            print(f"   ⚠️  网络连接失败，请检查网络设置")
        else:
            print(f"   ❌ {api_name} API 调用失败: {type(e).__name__}: {str(e)[:100]}")

    def is_ai_available(self) -> bool:
        """
        判断是否有可用的 AI API（Gemini 或 DeepSeek）

        Returns:
            True 如果有可用的 API
        """
        return self.gemini_model is not None or self.ai_client is not None

    def load_current_config(self) -> Dict[str, Any]:
        """
        加载当前配置文件

        Returns:
            配置字典
        """
        with open(self.config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config if config is not None else {}

    def save_config(self, config: Dict[str, Any]) -> None:
        """
        保存配置到文件

        Args:
            config: 配置字典
        """
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                config, f, allow_unicode=True, default_flow_style=False, sort_keys=False
            )

    def update_scenarios(
        self, all_scenes: List[str], selected_scenes: List[str]
    ) -> bool:
        """
        增量式更新场景配置（只修改 enabled 字段，保留其他配置）

        Args:
            all_scenes: 所有可用的场景列表（场景名称，如 ["跌倒检测", "火灾检测"]）
            selected_scenes: 用户勾选（启用）的场景列表

        Returns:
            更新是否成功
        """
        try:
            # 1. 加载当前配置
            config = self.load_current_config()
            scenarios = config.get("scenarios", {})

            # 2. 增量更新：只修改 enabled 字段
            updated_count = 0
            for scene_key, scene_config in scenarios.items():
                scene_name = scene_config.get("name", "")
                should_enable = scene_name in selected_scenes

                # normal 场景特殊保护：始终保持 alert_level: low
                if scene_key == "normal":
                    scene_config["alert_level"] = "low"

                if scene_config.get("enabled") != should_enable:
                    scene_config["enabled"] = should_enable
                    updated_count += 1

            # 3. 检查是否有新场景需要添加
            existing_names = {s.get("name") for s in scenarios.values()}
            for scene_name in all_scenes:
                if scene_name not in existing_names:
                    # 新场景：尝试生成配置
                    scene_key = self._generate_scene_key(scene_name)
                    new_config = self._get_or_generate_scene_config(
                        scene_name, scene_name in selected_scenes
                    )
                    scenarios[scene_key] = new_config
                    updated_count += 1
                    print(f"  ➕ 新增场景: {scene_name}")

            # 4. 保存配置
            config["scenarios"] = scenarios
            self.save_config(config)

            if updated_count > 0:
                enabled = [
                    s.get("name") for s in scenarios.values() if s.get("enabled")
                ]
                print(f"✅ 场景配置已更新，启用: {', '.join(enabled)}")

            return True

        except Exception as e:
            print(f"❌ 更新场景配置失败: {e}")
            return False

    def _get_or_generate_scene_config(
        self, scene_name: str, enabled: bool = True
    ) -> Dict[str, Any]:
        """
        获取或生成场景配置（优先使用模板，其次AI，最后默认）
        """
        # 预定义模板
        templates = {
            "跌倒检测": {
                "name": "跌倒检测",
                "prompt": "a person has fallen and is lying on the floor",
                "prompt_cn": "有人摔倒躺在地上",
                "threshold": 0.5,
                "cooldown": 30,
                "consecutive_frames": 2,
                "alert_level": "high",
            },
            "火灾检测": {
                "name": "火灾检测",
                "prompt": "flames and fire burning with visible smoke",
                "prompt_cn": "发生火灾，有火焰和浓烟",
                "threshold": 0.5,
                "cooldown": 60,
                "consecutive_frames": 3,
                "alert_level": "high",
            },
            "正常场景": {
                "name": "正常场景",
                "prompt": "an ordinary indoor room with no emergency",
                "prompt_cn": "普通室内环境，无异常",
                "threshold": 0.99,
                "cooldown": 10,
                "consecutive_frames": 1,
                "alert_level": "low",
            },
            "摔倒": {
                "name": "跌倒检测",
                "prompt": "a person has fallen and is lying on the floor",
                "prompt_cn": "有人摔倒躺在地上",
                "threshold": 0.5,
                "cooldown": 30,
                "consecutive_frames": 2,
                "alert_level": "high",
            },
            "起火": {
                "name": "火灾检测",
                "prompt": "flames and fire burning with visible smoke",
                "prompt_cn": "发生火灾，有火焰和浓烟",
                "threshold": 0.5,
                "cooldown": 60,
                "consecutive_frames": 3,
                "alert_level": "high",
            },
            "正常": {
                "name": "正常场景",
                "prompt": "an ordinary indoor room with no emergency",
                "prompt_cn": "普通室内环境，无异常",
                "threshold": 0.99,
                "cooldown": 10,
                "consecutive_frames": 1,
                "alert_level": "low",
            },
        }

        if scene_name in templates:
            config = templates[scene_name].copy()
            config["enabled"] = enabled
            return config

        # 尝试 AI 生成
        ai_config = self.generate_scene_with_ai(scene_name)
        if ai_config:
            ai_config["enabled"] = enabled
            return ai_config

        # 默认配置
        return {
            "enabled": enabled,
            "name": f"{scene_name}检测" if "检测" not in scene_name else scene_name,
            "prompt": f"a scene of {scene_name}",
            "prompt_cn": f"{scene_name}场景",
            "threshold": 0.5,
            "cooldown": 30,
            "consecutive_frames": 2,
            "alert_level": "medium",
        }

    def _generate_scenarios_config(
        self, all_scenes: List[str], selected_scenes: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        生成 scenarios 配置

        Args:
            all_scenes: 所有可用的场景列表
            selected_scenes: 用户勾选（启用）的场景列表

        Returns:
            scenarios 配置字典

        说明：
        - 配置文件会包含所有场景
        - enabled字段根据用户是否勾选来设置（True/False）
        - 优先使用 Gemini API 生成配置，如不可用则使用模板
        """
        print(f"\n🤖 正在生成场景配置...")

        scenarios = {}

        # 预定义场景模板（作为 Gemini 不可用时的备选）
        # 字段顺序: enabled -> name -> prompt -> prompt_cn -> threshold -> cooldown -> consecutive_frames -> alert_level
        scene_templates = {
            "摔倒": {
                "enabled": True,
                "name": "跌倒检测",
                "prompt": "a person has fallen and is lying on the floor",
                "prompt_cn": "有人摔倒躺在地上",
                "threshold": 0.4,
                "cooldown": 30,
                "consecutive_frames": 2,
                "alert_level": "high",
            },
            "跌倒检测": {
                "enabled": True,
                "name": "跌倒检测",
                "prompt": "a person has fallen and is lying on the floor",
                "prompt_cn": "有人摔倒躺在地上",
                "threshold": 0.4,
                "cooldown": 30,
                "consecutive_frames": 2,
                "alert_level": "high",
            },
            "起火": {
                "enabled": True,
                "name": "火灾检测",
                "prompt": "flames and fire burning with visible smoke",
                "prompt_cn": "发生火灾，有火焰和浓烟",
                "threshold": 0.4,
                "cooldown": 60,
                "consecutive_frames": 3,
                "alert_level": "high",
            },
            "火灾检测": {
                "enabled": True,
                "name": "火灾检测",
                "prompt": "flames and fire burning with visible smoke",
                "prompt_cn": "发生火灾，有火焰和浓烟",
                "threshold": 0.4,
                "cooldown": 60,
                "consecutive_frames": 3,
                "alert_level": "high",
            },
            "正常": {
                "enabled": False,
                "name": "正常场景",
                "prompt": "an ordinary indoor room with no emergency",
                "prompt_cn": "普通室内环境，无异常",
                "threshold": 0.99,
                "cooldown": 10,
                "consecutive_frames": 1,
                "alert_level": "low",
            },
            "正常场景": {
                "enabled": False,
                "name": "正常场景",
                "prompt": "an ordinary indoor room with no emergency",
                "prompt_cn": "普通室内环境，无异常",
                "threshold": 0.99,
                "cooldown": 10,
                "consecutive_frames": 1,
                "alert_level": "low",
            },
        }

        # 为所有场景生成配置
        for scene_name in all_scenes:
            # 生成场景的英文键（小写+下划线）
            scene_key = self._generate_scene_key(scene_name)

            # 判断该场景是否被用户启用
            is_enabled = scene_name in selected_scenes

            # 如果有模板则使用模板
            if scene_name in scene_templates:
                scenarios[scene_key] = scene_templates[scene_name].copy()
                scenarios[scene_key]["enabled"] = is_enabled
                status = "✅ 启用" if is_enabled else "❌ 禁用"
                print(f"   {status} {scene_name} -> 使用预定义模板")
            else:
                # 自定义场景：尝试使用 AI 生成配置
                ai_config = self.generate_scene_with_ai(scene_name)

                if ai_config:
                    scenarios[scene_key] = ai_config
                    scenarios[scene_key]["enabled"] = is_enabled
                    status = "✅ 启用" if is_enabled else "❌ 禁用"
                    print(f"   {status} {scene_name} -> 🤖 AI 智能生成")
                else:
                    # AI 失败，使用默认配置
                    scenarios[scene_key] = {
                        "enabled": is_enabled,
                        "name": f"{scene_name}检测",
                        "prompt": f"a scene of {scene_name}",
                        "prompt_cn": f"{scene_name}场景",
                        "threshold": 0.5,
                        "cooldown": 30,
                        "consecutive_frames": 2,
                        "alert_level": "medium",
                    }
                    status = "✅ 启用" if is_enabled else "❌ 禁用"
                    print(f"   {status} {scene_name} -> 使用默认配置")

        return scenarios

    def _generate_scene_key(self, scene_name: str) -> str:
        """
        根据场景名称生成英文键

        Args:
            scene_name: 中文场景名称，如 "摔倒"

        Returns:
            英文键，如 "fall"

        示例映射：
        - 摔倒 -> fall
        - 起火 -> fire
        - 正常 -> normal
        - 闯入 -> intrusion
        """
        # 预定义映射表（同时支持简写和完整名称）
        key_map = {
            "摔倒": "fall",
            "跌倒": "fall",
            "跌倒检测": "fall",
            "起火": "fire",
            "火灾": "fire",
            "火灾检测": "fire",
            "正常": "normal",
            "正常场景": "normal",
            "闯入": "intrusion",
            "入侵": "intrusion",
            "打架": "fight",
            "斗殴": "fight",
            "异常行为": "abnormal_behavior",
            "攀爬": "climbing",
            "奔跑": "running",
            "聚集": "gathering",
            "徘徊": "wandering",
            "遗留物": "abandoned_object",
            "烟雾": "smoke",
            "求救": "help_signal",
        }

        # 如果在映射表中，直接返回
        if scene_name in key_map:
            return key_map[scene_name]

        # 否则尝试使用 AI 翻译（支持多种 LLM API）
        return self.generate_scene_key_with_ai(scene_name)

    def add_gemini_support(self, api_key: str) -> None:
        """
        添加 Gemini API 支持（优先使用）

        Args:
            api_key: Gemini API 密钥
        """
        if not GEMINI_AVAILABLE:
            print("❌ google-generativeai 未安装，无法启用 Gemini 支持")
            print("   安装命令: pip install google-generativeai")
            return

        self.GEMINI_API_KEY = api_key
        try:
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel("gemini-3-flash-preview")
            self.current_api = "gemini"
            print("✓ Gemini API 初始化成功")
        except Exception as e:
            print(f"⚠️  Gemini API 初始化失败: {e}")

    def add_deepseek_support(self, api_key: str) -> None:
        """
        添加 DeepSeek API 支持

        Args:
            api_key: DeepSeek API 密钥
        """
        if not DEEPSEEK_AVAILABLE:
            print("❌ openai 未安装，无法启用 DeepSeek 支持")
            print("   安装命令: pip install openai")
            return

        self.DEEPSEEK_API_KEY = api_key
        self._init_deepseek()

    def calculate_dynamic_threshold(
        self, total_scenarios: int, is_normal: bool = False
    ) -> float:
        """
        根据场景总数计算动态阈值

        Args:
            total_scenarios: 总场景数
            is_normal: 是否为"正常"场景

        Returns:
            计算后的阈值

        计算公式：
        - 正常场景：固定为 0.99
        - 其他场景：1.5 * (1 / 总场景数)，范围限制在 0.3-0.6
        """
        if is_normal:
            return 0.99

        # 计算基础阈值：1.5 * (1 / 总场景数)
        if total_scenarios <= 0:
            total_scenarios = 1

        base_threshold = 1.5 * (1.0 / total_scenarios)

        # 限制在合理范围内 [0.3, 0.6]
        threshold = max(0.3, min(0.6, base_threshold))

        # 保留3位小数
        return round(threshold, 3)

    def recalculate_all_thresholds(self) -> bool:
        """
        重新计算所有场景的阈值（静默执行）

        当场景数量变化时调用此方法，根据新的总场景数重新计算每个场景的阈值

        Returns:
            是否成功更新
        """
        try:
            config = self.load_current_config()
            scenarios = config.get("scenarios", {})

            if not scenarios:
                return True

            total_scenarios = len(scenarios)

            for scene_key, scene_config in scenarios.items():
                if isinstance(scene_config, dict):
                    # 判断是否为"正常"场景
                    is_normal = scene_key == "normal" or scene_config.get(
                        "name", ""
                    ) in ["正常场景", "正常检测"]
                    new_threshold = self.calculate_dynamic_threshold(
                        total_scenarios, is_normal
                    )
                    scene_config["threshold"] = new_threshold

                    # 确保 normal 场景的 alert_level 始终为 low
                    if is_normal:
                        scene_config["alert_level"] = "low"

            config["scenarios"] = scenarios
            self.save_config(config)
            return True

        except Exception as e:
            print(f"❌ 重新计算阈值失败: {e}")
            return False

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取 JSON"""
        # 1. 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 2. 尝试提取 markdown 代码块
        if "```" in text:
            try:
                if "```json" in text:
                    json_text = text.split("```json")[1].split("```")[0].strip()
                else:
                    json_text = text.split("```")[1].split("```")[0].strip()
                return json.loads(json_text)
            except (IndexError, json.JSONDecodeError):
                pass

        # 3. 尝试使用正则提取最外层的 {}
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                json_text = text[start : end + 1]
                return json.loads(json_text)
        except json.JSONDecodeError:
            pass

        return None

    def generate_scene_with_ai(
        self, scene_name: str, total_scenarios: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        使用 AI API（优先 Gemini，备选 DeepSeek）为新场景生成配置

        Args:
            scene_name: 中文场景名称，如 "打架"、"闯入"
            total_scenarios: 当前总场景数（用于计算阈值）

        Returns:
            场景配置字典，失败返回 None
        """
        if not self.is_ai_available():
            print(f"   ⚠️  AI 不可用，无法为 '{scene_name}' 生成智能配置")
            return None

        # 预先计算阈值
        is_normal = scene_name in ["正常", "普通", "normal"]
        calculated_threshold = self.calculate_dynamic_threshold(
            total_scenarios + 1, is_normal
        )

        try:
            # 构建 prompt
            prompt = f"""你是一个视频监控场景检测配置专家。请为以下场景生成一个检测配置。

场景名称（中文）: {scene_name}

请严格按照以下 JSON 格式返回配置（不要添加任何其他文字）:
{{
    "name": "场景的中文名称（带'检测'后缀，如'跌倒检测'、'火灾检测'）",
    "prompt": "用于CLIP模型的英文描述，描述该场景的视觉特征，简洁准确，10-20个英文单词",
    "prompt_cn": "中文描述，与prompt对应，简洁准确",
    "cooldown": 冷却时间（秒，10-120之间的整数，紧急场景设短一些）,
    "consecutive_frames": 连续检测帧数（1-5之间的整数，越紧急越少）,
    "alert_level": "告警级别（high/medium/low，紧急危险场景用high）"
}}

参考示例：
- 跌倒检测: prompt="a person has fallen down and is lying on the ground or floor", alert_level="high"
- 火灾检测: prompt="flames and fire burning with visible smoke in the scene", alert_level="high"
- 打架检测: prompt="two or more people fighting, hitting or attacking each other violently", alert_level="high"
- 闯入检测: prompt="unauthorized person entering restricted area or climbing over fence", alert_level="high"

请确保：
1. prompt 必须是用于 CLIP 视觉模型的英文描述，应准确描述场景的视觉特征
2. prompt 要具体、准确，便于视觉模型识别
3. 根据场景的紧急程度合理设置 cooldown、consecutive_frames 和 alert_level
4. 只返回 JSON，不要有任何其他内容（包括注释）"""

            api_name = self.current_api.upper() if self.current_api else "AI"
            print(
                f"   📡 正在调用 {api_name} API 为 '{scene_name}' 生成配置（超时: {self.API_TIMEOUT}秒）..."
            )

            # 使用带超时的 AI API 调用
            response_text = self._call_ai_with_timeout(prompt)

            if response_text is None:
                print(f"   ⚠️  AI 响应超时或失败，将使用默认配置")
                return None

            # 解析 JSON
            config = self._extract_json(response_text)

            if config is None:
                print(f"   ⚠️  无法解析 AI 返回的 JSON 配置")
                return None

            # 验证必要字段（threshold 不再由 Gemini 生成）
            required_fields = [
                "name",
                "prompt",
                "prompt_cn",
                "cooldown",
                "consecutive_frames",
                "alert_level",
            ]
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"缺少必要字段: {field}")

            # 使用动态计算的阈值（不使用 Gemini 返回的阈值）
            config["threshold"] = calculated_threshold

            # 验证其他数值范围
            config["cooldown"] = max(10, min(120, int(config.get("cooldown", 30))))
            config["consecutive_frames"] = max(
                1, min(5, int(config.get("consecutive_frames", 2)))
            )

            if config.get("alert_level") not in ["high", "medium", "low"]:
                config["alert_level"] = "medium"

            # 按照标准顺序重新组织配置
            # 字段顺序: enabled -> name -> prompt -> prompt_cn -> threshold -> cooldown -> consecutive_frames -> alert_level
            ordered_config = {
                "enabled": True,  # 新创建的场景默认启用
                "name": config["name"],
                "prompt": config["prompt"],
                "prompt_cn": config["prompt_cn"],
                "threshold": config["threshold"],
                "cooldown": config["cooldown"],
                "consecutive_frames": config["consecutive_frames"],
                "alert_level": config["alert_level"],
            }

            api_name = self.current_api.upper() if self.current_api else "AI"
            print(f"   ✅ {api_name} 成功生成配置:")
            print(f"      - name: {ordered_config['name']}")
            print(f"      - prompt: {ordered_config['prompt'][:60]}...")
            print(f"      - threshold: {ordered_config['threshold']} (动态计算)")
            print(f"      - alert_level: {ordered_config['alert_level']}")

            return ordered_config

        except json.JSONDecodeError as e:
            print(f"   ❌ AI 返回的 JSON 解析失败: {e}")
            return None
        except Exception as e:
            print(f"   ❌ AI API 调用失败: {e}")
            return None

    def generate_scene_key_with_ai(self, scene_name: str) -> str:
        """
        使用 AI 将中文场景名翻译为英文键

        Args:
            scene_name: 中文场景名称

        Returns:
            英文键（小写+下划线）
        """
        if not self.is_ai_available():
            return self._generate_pinyin_key(scene_name)

        try:
            prompt = f"""将以下中文场景名称翻译为简短的英文键（用于配置文件的键名）。
要求：全小写，多个单词用下划线连接，简洁明了。

中文场景: {scene_name}

只返回英文键，不要其他内容。

示例:
- 摔倒 -> fall
- 起火 -> fire
- 闯入 -> intrusion
- 打架 -> fight"""

            # 使用带超时的调用，翻译任务用较短的超时时间
            response_text = self._call_ai_with_timeout(prompt, timeout=8)

            if response_text is None:
                return self._generate_pinyin_key(scene_name)

            key = response_text.lower().replace(" ", "_")
            # 移除非法字符
            key = re.sub(r"[^a-z0-9_]", "", key)
            return key if key else self._generate_pinyin_key(scene_name)

        except Exception:
            return self._generate_pinyin_key(scene_name)

    def _generate_pinyin_key(self, scene_name: str) -> str:
        """
        根据中文名称生成拼音风格的键名（作为备选）

        Args:
            scene_name: 中文场景名称

        Returns:
            转换后的键名（小写+下划线）
        """
        # 预定义映射表（同时支持简写和完整名称）
        key_map = {
            "摔倒": "fall",
            "跌倒": "fall",
            "跌倒检测": "fall",
            "起火": "fire",
            "火灾": "fire",
            "火灾检测": "fire",
            "正常": "normal",
            "正常场景": "normal",
            "闯入": "intrusion",
            "入侵": "intrusion",
            "打架": "fight",
            "斗殴": "fight",
            "异常行为": "abnormal_behavior",
            "攀爬": "climbing",
            "奔跑": "running",
            "聚集": "gathering",
            "徘徊": "wandering",
            "遗留物": "abandoned_object",
            "烟雾": "smoke",
            "求救": "help_signal",
        }

        if scene_name in key_map:
            return key_map[scene_name]

        # 对于未知场景，使用简单的转换
        # 移除空格和特殊字符，转为小写
        key = scene_name.lower().replace(" ", "_")
        key = re.sub(r"[^a-z0-9_\u4e00-\u9fff]", "", key)

        # 如果还是中文，添加scene_前缀和时间戳
        if re.search(r"[\u4e00-\u9fff]", key):
            import time

            key = f"scene_{int(time.time())}"

        return key

    def _generate_default_scene_config(
        self, scene_name: str, total_scenarios: int = 3
    ) -> Dict[str, Any]:
        """
        生成默认的场景配置（当Gemini不可用时使用）

        Args:
            scene_name: 中文场景名称
            total_scenarios: 当前总场景数（用于计算阈值）

        Returns:
            默认配置字典
        """
        is_normal = scene_name in ["正常", "普通", "normal"]
        threshold = self.calculate_dynamic_threshold(total_scenarios + 1, is_normal)

        # 字段顺序: enabled -> name -> prompt -> prompt_cn -> threshold -> cooldown -> consecutive_frames -> alert_level
        return {
            "enabled": True,
            "name": f"{scene_name}检测",
            "prompt": f"a scene showing {scene_name} situation or event",
            "prompt_cn": f"{scene_name}场景",
            "threshold": threshold,
            "cooldown": 30,
            "consecutive_frames": 2,
            "alert_level": "medium",
        }

    def add_new_scenario(self, scene_key: str, scene_config: Dict[str, Any]) -> bool:
        """
        添加单个新场景到配置文件

        Args:
            scene_key: 场景键名（英文，如 'fall', 'fire'）
            scene_config: 场景配置字典

        Returns:
            是否成功添加
        """
        try:
            # 1. 加载当前配置
            config = self.load_current_config()

            # 2. 确保 scenarios 存在
            if "scenarios" not in config:
                config["scenarios"] = {}

            # 3. 添加场景配置
            config["scenarios"][scene_key] = scene_config

            # 4. 保存配置
            self.save_config(config)

            # 5. 重新计算所有场景的阈值
            self.recalculate_all_thresholds()

            print(f"✅ 新增场景: {scene_config.get('name', scene_key)}")
            return True

        except Exception as e:
            print(f"❌ 添加场景失败: {e}")
            return False

    def delete_scenarios_by_names(self, scene_names: List[str]) -> bool:
        """
        根据中文名称删除场景（内置场景不可删除）

        Args:
            scene_names: 要删除的场景名称列表（中文，如 ["打架", "闯入"]）

        Returns:
            是否成功删除
        """
        # 过滤掉受保护的场景（使用模块级常量）
        deletable_scenes = [s for s in scene_names if s not in PROTECTED_SCENE_NAMES]
        if len(deletable_scenes) < len(scene_names):
            skipped = set(scene_names) - set(deletable_scenes)
            print(f"⚠️  跳过内置场景: {', '.join(skipped)}")

        if not deletable_scenes:
            print("⚠️  没有可删除的场景")
            return False

        try:
            # 1. 加载当前配置
            config = self.load_current_config()
            scenarios = config.get("scenarios", {})

            if not scenarios:
                print("⚠️  配置文件中没有场景")
                return False

            # 2. 找到对应的场景键（跳过受保护的键）
            keys_to_delete = []
            for scene_name in deletable_scenes:
                found = False
                for key, value in scenarios.items():
                    # 跳过受保护的键（使用模块级常量）
                    if key in PROTECTED_SCENE_KEYS:
                        continue

                    if isinstance(value, dict):
                        config_name = value.get("name", "")

                        # 直接完整匹配，或者去掉两边的"检测"后缀进行匹配
                        if config_name == scene_name:
                            keys_to_delete.append(key)
                            found = True
                            break

                        # 尝试去掉"检测"后缀匹配（兼容性）
                        config_name_stripped = (
                            config_name[:-2]
                            if config_name.endswith("检测")
                            else config_name
                        )
                        scene_name_stripped = (
                            scene_name[:-2]
                            if scene_name.endswith("检测")
                            else scene_name
                        )

                        if config_name_stripped == scene_name_stripped:
                            keys_to_delete.append(key)
                            found = True
                            break

                if not found:
                    print(f"⚠️  未找到场景: {scene_name}")

            if not keys_to_delete:
                print(f"⚠️  未找到任何要删除的场景")
                return False

            # 3. 删除场景
            deleted_names = []
            for key in keys_to_delete:
                if key in scenarios:
                    scene_name = scenarios[key].get("name", key)
                    del scenarios[key]
                    deleted_names.append(scene_name)

            # 4. 保存配置
            config["scenarios"] = scenarios
            self.save_config(config)

            # 5. 重新计算所有场景的阈值（因为场景数量变化了）
            if deleted_names:
                self.recalculate_all_thresholds()
                print(f"🗑️  已删除: {', '.join(deleted_names)}")

            return True

        except Exception as e:
            print(f"❌ 删除场景失败: {e}")
            return False

    def get_all_scene_names(self) -> List[str]:
        """
        从配置文件获取所有场景的中文名称

        Returns:
            场景名称列表
        """
        try:
            config = self.load_current_config()
            scenarios = config.get("scenarios", {})

            names = []
            for key, value in scenarios.items():
                if isinstance(value, dict) and "name" in value:
                    # 去掉"检测"后缀作为显示名称
                    name = value["name"]
                    if name.endswith("检测"):
                        name = name[:-2]
                    names.append(name)
                else:
                    names.append(key)

            return names
        except Exception as e:
            print(f"获取场景名称失败: {e}")
            return []

    def get_enabled_scene_names(self) -> List[str]:
        """
        获取所有启用的场景名称

        Returns:
            启用的场景名称列表
        """
        try:
            config = self.load_current_config()
            scenarios = config.get("scenarios", {})

            names = []
            for key, value in scenarios.items():
                if isinstance(value, dict) and value.get("enabled", True):
                    if "name" in value:
                        name = value["name"]
                        if name.endswith("检测"):
                            name = name[:-2]
                        names.append(name)
                    else:
                        names.append(key)

            return names
        except Exception as e:
            print(f"获取启用场景名称失败: {e}")
            return []


def test_config_updater():
    """测试配置更新器"""
    print("\n" + "=" * 60)
    print("测试配置更新器")
    print("=" * 60)

    try:
        # 创建更新器
        updater = ConfigUpdater()

        # 测试场景：所有场景和用户选择的场景
        all_scenes = ["摔倒", "起火", "正常"]
        selected_scenes = ["摔倒", "起火"]  # 只启用这两个

        # 更新配置
        success = updater.update_scenarios(all_scenes, selected_scenes)

        if success:
            print("\n✅ 测试通过！")
            print("\n📝 查看配置文件 config/detection/default.yaml")
            print("   应包含所有3个场景，其中：")
            print("   - 摔倒: enabled=true")
            print("   - 起火: enabled=true")
            print("   - 正常: enabled=false")
        else:
            print("\n❌ 测试失败！")

    except Exception as e:
        print(f"\n❌ 测试出错: {e}")


if __name__ == "__main__":
    test_config_updater()
