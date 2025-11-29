"""
配置更新工具模块

功能：
- 监听场景选择变化
- 更新 config/detection/default.yaml 的 scenarios 配置
- 使用 Gemini API 生成规范的场景配置格式

主要类：
- ConfigUpdater: 配置更新器类
"""

import yaml
import json
import re
import os
import signal
from pathlib import Path
from typing import List, Dict, Any, Optional

# DeepSeek API 支持（可选依赖）
try:
    from openai import OpenAI

    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False
    print("⚠️  openai 未安装，AI 生成功能不可用")
    print("   安装命令: pip install openai")


class ConfigUpdater:
    """配置更新器 - 负责根据用户选择的场景更新配置文件"""

    # DeepSeek API 密钥
    DEEPSEEK_API_KEY = "your_key_here"

    # API 超时时间（秒）
    API_TIMEOUT = 30

    def __init__(self, config_path: str = "config/detection/default.yaml"):
        """
        初始化配置更新器

        Args:
            config_path: 配置文件路径（相对于项目根目录）
        """
        # 获取项目根目录
        self.project_root = Path(__file__).parent.parent.parent
        self.config_file = self.project_root / config_path

        # 确保配置文件存在
        if not self.config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_file}")

        # 初始化 DeepSeek 客户端
        self.ai_client = None
        if DEEPSEEK_AVAILABLE and self.DEEPSEEK_API_KEY:
            self._init_deepseek()

        print(f"✓ 配置更新器初始化: {self.config_file}")

    def _init_deepseek(self) -> None:
        """初始化 DeepSeek API 客户端"""
        try:
            self.ai_client = OpenAI(
                api_key=self.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com"
            )
            print("✓ DeepSeek API 初始化成功")
        except Exception as e:
            print(f"⚠️  DeepSeek API 初始化失败: {e}")
            print(f"   提示: 检查网络连接和 API 密钥是否正确")
            self.ai_client = None

    def _call_ai_with_timeout(self, prompt: str, timeout: int = None) -> Optional[str]:
        """
        带超时的 AI API 调用

        Args:
            prompt: 提示词
            timeout: 超时时间（秒），默认使用 API_TIMEOUT

        Returns:
            响应文本，超时或失败返回 None
        """
        if timeout is None:
            timeout = self.API_TIMEOUT

        # 使用线程池实现真正的超时控制
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
                    print(f"   ⏱️  API 调用超时 ({timeout}秒)")
                    print(
                        f"   💡 提示: 可能是网络问题或 API 服务响应慢，建议检查网络连接"
                    )
                    return None

        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg or "timed out" in error_msg:
                print(f"   ⏱️  API 调用超时 ({timeout}秒)")
            elif "429" in error_msg or "quota" in error_msg:
                print(f"   ⚠️  API 配额已用尽或请求频率过高")
            elif "403" in error_msg or "401" in error_msg:
                print(f"   ⚠️  API 密钥无效或权限不足")
            elif "network" in error_msg or "connection" in error_msg:
                print(f"   ⚠️  网络连接失败，请检查网络设置")
            else:
                print(f"   ❌ API 调用失败: {type(e).__name__}: {str(e)[:100]}")
            return None

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
        print(f"✓ 配置已保存到: {self.config_file}")

    def update_scenarios(
        self, all_scenes: List[str], selected_scenes: List[str]
    ) -> bool:
        """
        根据所有场景和用户选择的场景更新配置文件的 scenarios 字段

        Args:
            all_scenes: 所有可用的场景列表，如 ["摔倒", "起火", "正常", "闯入"]
            selected_scenes: 用户勾选（启用）的场景列表，如 ["摔倒", "起火"]

        Returns:
            更新是否成功

        工作流程：
        1. 加载当前配置
        2. 为所有场景生成配置
        3. 根据selected_scenes设置enabled字段
        4. 更新并保存配置文件
        """
        try:
            print(f"\n{'='*60}")
            print(f"🔄 开始更新场景配置...")
            print(f"{'='*60}")
            print(f"📌 所有场景: {', '.join(all_scenes)}")
            print(
                f"✅ 已启用场景: {', '.join(selected_scenes) if selected_scenes else '无'}"
            )
            disabled = set(all_scenes) - set(selected_scenes)
            print(f"❌ 已禁用场景: {', '.join(disabled) if disabled else '无'}")

            # 1. 加载当前配置
            config = self.load_current_config()

            # 2. 生成新的 scenarios 配置（包含所有场景）
            # TODO: 这里将来会调用 Gemini API 来生成规范的配置
            new_scenarios = self._generate_scenarios_config(all_scenes, selected_scenes)

            # 3. 更新配置
            config["scenarios"] = new_scenarios

            # 4. 保存配置
            self.save_config(config)

            print(f"✅ 场景配置更新成功！")
            print(f"{'='*60}\n")
            return True

        except Exception as e:
            print(f"❌ 更新场景配置失败: {e}")
            import traceback

            traceback.print_exc()
            return False

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
        # 预定义映射表
        key_map = {
            "摔倒": "fall",
            "起火": "fire",
            "正常": "normal",
            "闯入": "intrusion",
            "打架": "fight",
            "异常行为": "abnormal_behavior",
        }

        # 如果在映射表中，直接返回
        if scene_name in key_map:
            return key_map[scene_name]

        # 否则尝试使用 Gemini 翻译
        return self.generate_scene_key_with_gemini(scene_name)

    def add_deepseek_support(self, api_key: str) -> None:
        """
        添加 DeepSeek API 支持

        Args:
            api_key: DeepSeek API 密钥
        """
        if not DEEPSEEK_AVAILABLE:
            print("❌ openai 未安装，无法启用 AI 支持")
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
        重新计算所有场景的阈值

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
            print(f"\n📊 重新计算阈值 (总场景数: {total_scenarios})")

            for scene_key, scene_config in scenarios.items():
                if isinstance(scene_config, dict):
                    # 判断是否为"正常"场景
                    is_normal = scene_key == "normal" or scene_config.get(
                        "name", ""
                    ) in ["正常场景", "正常检测"]
                    new_threshold = self.calculate_dynamic_threshold(
                        total_scenarios, is_normal
                    )
                    old_threshold = scene_config.get("threshold", 0.5)
                    scene_config["threshold"] = new_threshold
                    print(f"   {scene_key}: {old_threshold} -> {new_threshold}")

            config["scenarios"] = scenarios
            self.save_config(config)
            print(f"✅ 阈值重新计算完成")
            return True

        except Exception as e:
            print(f"❌ 重新计算阈值失败: {e}")
            return False

    def generate_scene_with_ai(
        self, scene_name: str, total_scenarios: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        使用 DeepSeek API 为新场景生成配置

        Args:
            scene_name: 中文场景名称，如 "打架"、"闯入"
            total_scenarios: 当前总场景数（用于计算阈值）

        Returns:
            场景配置字典，失败返回 None
        """
        if not self.ai_client:
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

            print(
                f"   📡 正在调用 DeepSeek API 为 '{scene_name}' 生成配置（超时: {self.API_TIMEOUT}秒）..."
            )

            # 使用带超时的 AI API 调用
            response_text = self._call_ai_with_timeout(prompt)

            if response_text is None:
                print(f"   ⚠️  AI 响应超时或失败，将使用默认配置")
                return None

            # 解析 JSON（处理可能的 markdown 代码块）
            json_text = response_text
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()

            # 解析 JSON
            config = json.loads(json_text)

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

            print(f"   ✅ DeepSeek 成功生成配置:")
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
        if not self.ai_client:
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
        # 预定义映射表
        key_map = {
            "摔倒": "fall",
            "起火": "fire",
            "正常": "normal",
            "闯入": "intrusion",
            "打架": "fight",
            "异常行为": "abnormal_behavior",
            "跌倒": "fall",
            "火灾": "fire",
            "入侵": "intrusion",
            "斗殴": "fight",
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
            print(f"\n{'='*60}")
            print(f"➕ 添加新场景: {scene_key}")
            print(f"{'='*60}")

            # 1. 加载当前配置
            config = self.load_current_config()

            # 2. 确保 scenarios 存在
            if "scenarios" not in config:
                config["scenarios"] = {}

            # 3. 检查是否已存在
            if scene_key in config["scenarios"]:
                print(f"   ⚠️  场景 '{scene_key}' 已存在，将覆盖")

            # 4. 添加场景配置
            config["scenarios"][scene_key] = scene_config

            # 5. 保存配置
            self.save_config(config)

            # 6. 重新计算所有场景的阈值（因为场景数量变化了）
            self.recalculate_all_thresholds()

            print(f"✅ 新场景 '{scene_key}' 添加成功！")
            print(f"   - name: {scene_config.get('name', 'N/A')}")
            print(f"   - prompt: {scene_config.get('prompt', 'N/A')[:50]}...")
            print(f"   - enabled: {scene_config.get('enabled', True)}")
            print(f"{'='*60}\n")
            return True

        except Exception as e:
            print(f"❌ 添加场景失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    def delete_scenarios_by_names(self, scene_names: List[str]) -> bool:
        """
        根据中文名称删除场景

        Args:
            scene_names: 要删除的场景名称列表（中文，如 ["打架", "闯入"]）

        Returns:
            是否成功删除
        """
        try:
            print(f"\n{'='*60}")
            print(f"🗑️  删除场景: {', '.join(scene_names)}")
            print(f"{'='*60}")

            # 1. 加载当前配置
            config = self.load_current_config()
            scenarios = config.get("scenarios", {})

            if not scenarios:
                print("   ⚠️  配置文件中没有场景")
                return False

            # 2. 找到对应的场景键
            keys_to_delete = []
            for scene_name in scene_names:
                found = False
                for key, value in scenarios.items():
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
                    print(f"   ⚠️  未找到场景: {scene_name}")

            if not keys_to_delete:
                print(f"   ⚠️  未找到任何要删除的场景")
                return False

            # 3. 删除场景
            deleted_count = 0
            for key in keys_to_delete:
                if key in scenarios:
                    scene_name = scenarios[key].get("name", key)
                    del scenarios[key]
                    deleted_count += 1
                    print(f"   ✓ 已删除: {scene_name} (key: {key})")

            # 4. 保存配置
            config["scenarios"] = scenarios
            self.save_config(config)

            # 5. 重新计算所有场景的阈值（因为场景数量变化了）
            if deleted_count > 0:
                self.recalculate_all_thresholds()

            print(f"✅ 成功删除 {deleted_count} 个场景！")
            print(f"{'='*60}\n")
            return True

        except Exception as e:
            print(f"❌ 删除场景失败: {e}")
            import traceback

            traceback.print_exc()
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
