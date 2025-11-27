"""
配置更新工具模块

功能：
- 监听场景选择变化
- 更新 config/detection/default.yaml 的 scenarios 配置
- 使用 Gemini API 生成规范的场景配置格式（预留接口）

主要类：
- ConfigUpdater: 配置更新器类
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any


class ConfigUpdater:
    """配置更新器 - 负责根据用户选择的场景更新配置文件"""

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

        print(f"✓ 配置更新器初始化: {self.config_file}")

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
        生成 scenarios 配置（占位符方法，未来将调用 Gemini API）

        Args:
            all_scenes: 所有可用的场景列表
            selected_scenes: 用户勾选（启用）的场景列表

        Returns:
            scenarios 配置字典

        说明：
        - 配置文件会包含所有场景
        - enabled字段根据用户是否勾选来设置（True/False）
        - 未来通过 Gemini API 生成规范的配置
        """
        print(f"\n🤖 正在生成场景配置...")
        print(f"   (未来将调用 Gemini API 进行智能适配)")

        scenarios = {}

        # 预定义场景模板（用于测试）
        scene_templates = {
            "摔倒": {
                "name": "跌倒检测",
                "prompt": "a person has fallen and is lying on the floor",
                "prompt_cn": "有人摔倒躺在地上",
                "threshold": 0.4,
                "cooldown": 30,
                "consecutive_frames": 2,
                "alert_level": "high",
            },
            "起火": {
                "name": "火灾检测",
                "prompt": "flames and fire burning with visible smoke",
                "prompt_cn": "发生火灾，有火焰和浓烟",
                "threshold": 0.4,
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

        # 为所有场景生成配置
        for scene_name in all_scenes:
            # 生成场景的英文键（小写+下划线）
            scene_key = self._generate_scene_key(scene_name)

            # 判断该场景是否被用户启用
            is_enabled = scene_name in selected_scenes

            # 如果有模板则使用模板，否则使用默认配置
            if scene_name in scene_templates:
                scenarios[scene_key] = scene_templates[scene_name].copy()
                scenarios[scene_key]["enabled"] = is_enabled
                status = "✅ 启用" if is_enabled else "❌ 禁用"
                print(f"   {status} {scene_name} -> 使用预定义模板")
            else:
                # 自定义场景：使用默认配置
                # TODO: 未来调用 Gemini API 生成更智能的配置
                scenarios[scene_key] = {
                    "enabled": is_enabled,
                    "name": f"{scene_name}检测",
                    "prompt": f"a scene of {scene_name}",  # 简单的英文prompt
                    "prompt_cn": f"{scene_name}场景",
                    "threshold": 0.5,
                    "cooldown": 30,
                    "consecutive_frames": 2,
                    "alert_level": "medium",
                }
                status = "✅ 启用" if is_enabled else "❌ 禁用"
                print(
                    f"   {status} {scene_name} -> 使用默认配置（建议后续通过 Gemini 优化）"
                )

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

        # 否则使用场景名作为键（未来可通过 Gemini 翻译）
        return scene_name.lower().replace(" ", "_")

    def add_gemini_support(self, api_key: str) -> None:
        """
        添加 Gemini API 支持（预留接口）

        Args:
            api_key: Gemini API 密钥

        未来实现：
        - 初始化 Gemini 客户端
        - 在 _generate_scenarios_config 中调用 Gemini
        - 生成更智能、更准确的场景配置
        """
        print(f"⚠️  Gemini API 支持功能待实现")
        print(f"   将支持以下功能：")
        print(f"   - 智能生成英文 prompt")
        print(f"   - 自动设置合理的阈值")
        print(f"   - 根据场景特征调整检测参数")
        # TODO: 实现 Gemini API 集成


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
