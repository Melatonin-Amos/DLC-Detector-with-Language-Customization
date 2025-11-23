"""
配置验证脚本

用于检查Hydra配置是否正确加载
"""

import hydra
from omegaconf import DictConfig, OmegaConf


@hydra.main(version_base=None, config_path="config", config_name="config")
def validate_config(cfg: DictConfig):
    """验证配置"""
    print("=" * 60)
    print("配置验证")
    print("=" * 60)
    
    # 打印完整配置
    print("\n完整配置：")
    print(OmegaConf.to_yaml(cfg))
    
    # 检查必要的配置项
    print("\n配置项检查：")
    
    checks = [
        ("运行模式", cfg.get('mode')),
        ("摄像头索引", cfg.camera.get('index')),
        ("摄像头分辨率", f"{cfg.camera.width}x{cfg.camera.height}"),
        ("抽帧间隔", f"{cfg.camera.extract_interval}秒"),
        ("CLIP模型", cfg.model.name),
        ("设备", cfg.model.device),
        ("翻译功能", "启用" if cfg.translation.enabled else "禁用"),
    ]
    
    for name, value in checks:
        print(f"  ✓ {name}: {value}")
    
    # 检查场景配置
    print("\n场景配置：")
    scenarios = cfg.detection.scenarios
    for scenario_id, scenario in scenarios.items():
        status = "✓ 启用" if scenario.enabled else "✗ 禁用"
        print(f"  {status} {scenario.name} (阈值: {scenario.threshold})")
    
    print("\n" + "=" * 60)
    print("✅ 配置验证完成！")
    print("=" * 60)


if __name__ == "__main__":
    validate_config()
