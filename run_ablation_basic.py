"""
运行前两个消融实验：Baseline 和 +势能奖励
"""
import subprocess
import sys
from pathlib import Path

# 前两个实验配置
EXPERIMENTS = [
    {
        "name": "baseline",
        "algo_config": "configs/algos/qmix_baseline.yaml",
        "description": "Baseline（无势能奖励、无动态恢复）"
    },
    {
        "name": "potential_only",
        "algo_config": "configs/algos/qmix_potential_only.yaml",
        "description": "+势能奖励（有势能奖励、无动态恢复）"
    }
]

ENV_CONFIG = "configs/envs/grid_ablation.yaml"
BASE_CONFIG = "configs/base.yaml"
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
    except KeyboardInterrupt:
        print(f"\n⚠ {config['description']} 实验被用户中断")
        return False

def main():
    """运行前两个消融实验"""
    print("="*60)
    print("开始运行消融实验（Baseline 和 +势能奖励）")
    print("="*60)
    print(f"环境配置: {ENV_CONFIG}")
    print(f"随机种子: {SEED}")
    print(f"实验配置数量: {len(EXPERIMENTS)}")
    print("="*60)
    print("\n注意：每个实验需要约 9.8 GPU·h（RTX 4060），请确保有足够的计算资源。")
    print("实验过程中可以随时按 Ctrl+C 中断。\n")
    
    results = []
    for i, config in enumerate(EXPERIMENTS, 1):
        success = run_experiment(config, i, len(EXPERIMENTS))
        results.append((config["name"], success))
        
        if not success:
            print(f"\n实验 {config['name']} 失败，是否继续运行下一个实验？")
            response = input("继续？(y/n): ").strip().lower()
            if response != 'y':
                break
    
    # 汇总结果
    print("\n" + "="*60)
    print("实验汇总")
    print("="*60)
    for name, success in results:
        status = "✓ 成功" if success else "✗ 失败"
        print(f"{name:20s}: {status}")
    
    success_count = sum(1 for _, s in results if s)
    print(f"\n完成: {success_count}/{len(results)}")
    
    if success_count == len(results):
        print("\n所有实验已完成！")
        print("请检查 experiments/logs/ 目录下的日志文件获取结果。")
        print("可以使用以下命令查看覆盖率等指标：")
        print("  grep 'coverage_mean' experiments/logs/*.log")
    else:
        print("\n部分实验失败，请检查错误信息。")

if __name__ == "__main__":
    main()

