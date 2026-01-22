"""
消融实验运行脚本
运行表5的4个配置：Baseline、+势能奖励、+动态恢复、完整模型
"""
import subprocess
import sys
from pathlib import Path

# 消融实验配置
ABLATION_CONFIGS = [
    {
        "name": "baseline",
        "algo_config": "configs/algos/qmix_baseline.yaml",
        "description": "Baseline（无势能奖励、无动态恢复）"
    },
    {
        "name": "potential_only",
        "algo_config": "configs/algos/qmix_potential_only.yaml",
        "description": "+势能奖励（有势能奖励、无动态恢复）"
    },
    {
        "name": "recovery_only",
        "algo_config": "configs/algos/qmix_recovery_only.yaml",
        "description": "+动态恢复（无势能奖励、有动态恢复）"
    },
    {
        "name": "full",
        "algo_config": "configs/algos/qmix_full.yaml",
        "description": "完整模型（有势能奖励、有动态恢复）"
    }
]

ENV_CONFIG = "configs/envs/grid_ablation.yaml"
BASE_CONFIG = "configs/base.yaml"  # 如果不存在，将使用默认值
SEED = 1234

def run_experiment(config: dict, exp_id: int, total: int):
    """运行单个消融实验配置"""
    print(f"\n{'='*60}")
    print(f"实验 {exp_id}/{total}: {config['description']}")
    print(f"配置文件: {config['algo_config']}")
    print(f"{'='*60}\n")
    
    cmd = [
        sys.executable,
        "src/algos/qmix/train_qmix.py",
        "--env-config", ENV_CONFIG,
        "--algo-config", config["algo_config"],
        "--seed", str(SEED),
        "--map-index", "0",
        "--uav-index", "0",
        "--obstacle-index", "0"
    ]
    
    if Path(BASE_CONFIG).exists():
        cmd.extend(["--base-config", BASE_CONFIG])
    
    try:
        result = subprocess.run(cmd, check=True, cwd=Path.cwd())
        print(f"\n✓ {config['description']} 实验完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {config['description']} 实验失败: {e}")
        return False

def main():
    """运行所有消融实验"""
    print("="*60)
    print("开始运行消融实验（表5）")
    print("="*60)
    print(f"环境配置: {ENV_CONFIG}")
    print(f"随机种子: {SEED}")
    print(f"实验配置数量: {len(ABLATION_CONFIGS)}")
    print("="*60)
    
    results = []
    for i, config in enumerate(ABLATION_CONFIGS, 1):
        success = run_experiment(config, i, len(ABLATION_CONFIGS))
        results.append((config["name"], success))
    
    # 汇总结果
    print("\n" + "="*60)
    print("消融实验汇总")
    print("="*60)
    for name, success in results:
        status = "✓ 成功" if success else "✗ 失败"
        print(f"{name:20s}: {status}")
    
    success_count = sum(1 for _, s in results if s)
    print(f"\n完成: {success_count}/{len(results)}")
    
    if success_count == len(results):
        print("\n所有消融实验已完成！")
        print("请检查 experiments/logs/ 目录下的日志文件获取结果。")
    else:
        print("\n部分实验失败，请检查错误信息。")

if __name__ == "__main__":
    main()

